NAME = "Drop Locator"
URL_PREFIX = "/droplocator"

from flask import request, render_template_string, jsonify
from db import getDb
from collections import defaultdict

TEMPLATE = """
<!doctype html>
<html>
  <head>
    <meta charset="utf-8">
    <title>Drop Locator</title>
    <style>
      body { font-family: monospace; background: #2c3e50; color: #ecf0f1; margin: 2rem; }
      h1 { margin-bottom: 1rem; }
      form { margin-bottom: 2rem; }
      input[type="text"] {
        font-size: 1rem; padding: 0.5rem; width: 300px;
        border-radius: 0.25rem; border: 1px solid #ccc;
      }
      button {
        font-size: 1rem; padding: 0.5rem 1rem;
        background: #1abc9c; color: white; border: none; border-radius: 0.25rem;
      }
      .autocomplete-suggestions {
        background: white; color: black;
        border: 1px solid #ccc;
        max-height: 200px; overflow-y: auto;
        position: absolute; z-index: 10;
        width: 300px;
      }
      .autocomplete-suggestions div {
        padding: 0.25rem 0.5rem;
        cursor: pointer;
      }
      .autocomplete-suggestions div:hover {
        background: #eee;
      }
      .zone { margin-bottom: 2rem; }
      .zone h2 { background: #34495e; padding: 0.5rem; border-radius: 0.25rem; }
      table { width: 100%; border-collapse: collapse; margin-top: 0.5rem; }
      th, td { border: 1px solid #7f8c8d; padding: 0.5rem; text-align: left; vertical-align: top; }
      th { background: #1abc9c; color: white; }
      tbody tr:nth-child(odd) { background: #34495e; }
      tbody tr:nth-child(even) { background: #2c3e50; }
      td.spawn-cell { white-space: pre-line; }
      .no-results { color: #e74c3c; }
    </style>
  </head>
  <body>
    <h1>Drop Locator</h1>
    <form action="{{ url_for('droplocator') }}" method="get" autocomplete="off">
      <input type="text" id="itemInput" name="item_id" placeholder="Enter item ID or name" value="{{ itemId or '' }}">
      <button type="submit">Search</button>
      <div id="autocomplete" class="autocomplete-suggestions" style="display:none;"></div>
    </form>

    {% if itemId and not grouped %}
      <p class="no-results">No drop locations found for this item.</p>
    {% elif grouped %}
      <h2>Drop Locations for Item {{ itemName }} ({{ itemId }})</h2>
      {% for zoneName, entries in grouped.items() %}
        <div class="zone">
          <h3>{{ zoneName }}</h3>
          <table>
            <thead>
              <tr>
                <th>Table ID</th>
                <th>Drops From</th>
                <th>Base Chance</th>
                <th>Multiplier</th>
                <th>Effective Chance</th>
                <th>Spawn Location(s)</th>
              </tr>
            </thead>
            <tbody>
              {% for e in entries %}
                <tr>
                  <td>{{ e.loottableId }}</td>
                  <td>{{ e.mobName }} (Level {{ e.mobLevel }})</td>
                  <td>{{ "%.2f"|format(e.baseChance) }}%</td>
                  <td>{{ e.multiplier }}×</td>
                  <td>{{ "%.2f"|format(e.effectiveChance) }}%</td>
                  <td class="spawn-cell">{{ e.spawnPoints }}</td>
                </tr>
              {% endfor %}
            </tbody>
          </table>
        </div>
      {% endfor %}
    {% endif %}

    <script>
      const input = document.getElementById('itemInput');
      const box = document.getElementById('autocomplete');

      input.addEventListener('input', () => {
        const q = input.value;
        if (q.length < 2) return box.style.display = 'none';

        fetch('{{ url_for("droplocator_search") }}?q=' + encodeURIComponent(q))
          .then(res => res.json())
          .then(data => {
            if (!data.results.length) return box.style.display = 'none';
            box.innerHTML = data.results.map(r =>
              `<div data-id="${r.id}" data-name="${r.name}">${r.id} - ${r.name}</div>`
            ).join('');
            box.style.display = 'block';
          });
      });

      box.addEventListener('click', (e) => {
        const div = e.target.closest('div');
        if (!div) return;
        input.value = div.dataset.id;
        box.style.display = 'none';
      });

      document.addEventListener('click', e => {
        if (!box.contains(e.target) && e.target !== input) {
          box.style.display = 'none';
        }
      });
    </script>
  </body>
</html>
"""

def register(app):
  @app.route(URL_PREFIX, methods=["GET"])
  def droplocator():
    itemId = request.args.get("item_id")
    itemName = None
    if itemId and itemId.isdigit():
      itemId = int(itemId)
    else:
      itemId = None

    grouped = defaultdict(list)
    if itemId is not None:
      db = getDb()
      with db.cursor() as cur:
        cur.execute("SELECT name FROM items WHERE id = %s", (itemId,))
        row = cur.fetchone()
        if row:
          itemName = row["name"]

      zoneMap = {}
      with db.cursor() as cur:
        cur.execute("SELECT short_name, long_name FROM zone")
        for z in cur.fetchall():
          zoneMap[z["short_name"]] = z["long_name"]

      query = """
        SELECT
          lt.id                        AS loottable_id,
          lde.chance                   AS base_chance,
          le.multiplier                AS multiplier,
          (lde.chance * le.multiplier) AS effective_chance,
          z.short_name                 AS zone_shortname,
          z.long_name                  AS zone_longname,
          nt.name                      AS npc_name,
          nt.lastname                  AS npc_lastname,
          nt.level,
          nt.maxlevel,
          GROUP_CONCAT(
            CONCAT(
              ROUND(s2.x, 1), ', ',
              ROUND(s2.y, 1), ', ',
              ROUND(s2.z, 1)
            ) SEPARATOR '\\n'
          ) AS spawn_points
        FROM lootdrop_entries     AS lde
        JOIN loottable_entries    AS le  ON lde.lootdrop_id = le.lootdrop_id
        JOIN loottable            AS lt  ON le.loottable_id = lt.id
        JOIN npc_types            AS nt  ON lt.id = nt.loottable_id
        JOIN spawnentry           AS se  ON nt.id = se.npcID
        JOIN spawn2               AS s2  ON se.spawngroupID = s2.spawngroupID
        JOIN zone                 AS z   ON s2.zone = z.short_name
        WHERE lde.item_id = %s
          AND z.peqzone = 1
        GROUP BY lt.id, nt.id, s2.zone
        ORDER BY z.long_name, effective_chance DESC
      """
      with db.cursor() as cur:
        cur.execute(query, (itemId,))
        rows = cur.fetchall()

      for r in rows:
        zoneShort = r.get("zone_shortname") or "unknown"
        zoneName = zoneMap.get(zoneShort, f"(Zone: {zoneShort})")
        mobName = r["npc_lastname"] or r["npc_name"]
        level = r["level"]
        maxLevel = r["maxlevel"]
        levelStr = str(level) if not maxLevel or maxLevel == level else f"{level}-{maxLevel}"
        grouped[zoneName].append({
          "loottableId":     r["loottable_id"],
          "baseChance":      float(r["base_chance"]),
          "multiplier":      int(r["multiplier"]),
          "effectiveChance": float(r["effective_chance"]),
          "mobName":         mobName,
          "mobLevel":        levelStr,
          "spawnPoints":     r["spawn_points"] or ""
        })

    return render_template_string(TEMPLATE, itemId=itemId, itemName=itemName, grouped=grouped)

  @app.route(f"{URL_PREFIX}/search")
  def droplocator_search():
    q = request.args.get("q", "").strip()
    if not q:
      return jsonify(results=[])

    db = getDb()
    query = """
      SELECT id, name
      FROM items
      WHERE CAST(id AS CHAR) LIKE %(like)s OR name LIKE %(like)s
      ORDER BY
        CASE
          WHEN name LIKE %(prefix)s THEN 0
          WHEN CAST(id AS CHAR) LIKE %(prefix)s THEN 1
          ELSE 2
        END,
        name
      LIMIT 15
    """
    like = f"%{q}%"
    prefix = f"{q}%"

    with db.cursor() as cur:
      cur.execute(query, {"like": like, "prefix": prefix})
      results = [{"id": r["id"], "name": r["name"]} for r in cur.fetchall()]

    return jsonify(results=results)
