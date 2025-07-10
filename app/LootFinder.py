NAME = "Loot Finder"
URL_PREFIX = "/lootfinder"

from flask import request, render_template_string, url_for
from db import getDb
from collections import defaultdict

FORM_HTML = """
<!doctype html>
<html>
  <head><title>Loot Finder</title></head>
  <body>
    <h1>Find Loot Tables for Item</h1>
    <form action="" method="get">
      <label for="item_id">Item ID:</label>
      <input type="number" id="item_id" name="item_id" required>
      <button type="submit">Search</button>
    </form>
  </body>
</html>
"""

TEMPLATE = """
<!doctype html>
<html>
  <head>
    <meta charset="utf-8">
    <title>Loot Finder</title>
    <style>
      body { font-family: sans-serif; margin: 2rem; background: #2c3e50; color: #ecf0f1; }
      h1 { margin-bottom: 1rem; }
      .zone { margin-bottom: 2rem; }
      .zone h2 { background: #34495e; padding: 0.5rem; border-radius: 0.25rem; }
      table { width: 100%; border-collapse: collapse; margin-top: 0.5rem; }
      th, td { border: 1px solid #7f8c8d; padding: 0.5rem; text-align: left; }
      th { background: #1abc9c; color: white; }
      tbody tr:nth-child(odd) { background: #34495e; }
      tbody tr:nth-child(even) { background: #2c3e50; }
      .no-results { color: #e74c3c; }
      a { display: inline-block; margin-top: 1rem; color: #1abc9c; }
      a:hover { text-decoration: underline; }
    </style>
  </head>
  <body>
    <h1>Loot Tables for Item {{ itemId }}</h1>
    {% if not grouped %}
      <p class="no-results">No loot tables found for this item.</p>
    {% else %}
      {% for zoneName, entries in grouped.items() %}
        <div class="zone">
          <h2>{{ zoneName }}</h2>
          <table>
            <thead>
              <tr>
                <th>Table ID</th>
                <th>Table Name</th>
                <th>Base Chance</th>
                <th>Multiplier</th>
                <th>Effective Chance</th>
              </tr>
            </thead>
            <tbody>
              {% for e in entries %}
                <tr>
                  <td>{{ e.loottableId }}</td>
                  <td>{{ e.loottableName }}</td>
                  <td>{{ "%.2f"|format(e.baseChance) }}%</td>
                  <td>{{ e.multiplier }}×</td>
                  <td>{{ "%.2f"|format(e.effectiveChance) }}%</td>
                </tr>
              {% endfor %}
            </tbody>
          </table>
        </div>
      {% endfor %}
    {% endif %}
    <a href="{{ url_for('lootfinder') }}">Search another item</a>
  </body>
</html>
"""

def register(app):
  @app.route(URL_PREFIX, methods=["GET"])
  def lootfinder():
    itemId = request.args.get("item_id", type=int)
    if itemId is None:
      return render_template_string(FORM_HTML)

    db = getDb()

    # load zone id→long_name map
    zoneMap = {}
    with db.cursor() as cur:
      cur.execute("SELECT id, long_name FROM zone")
      for row in cur.fetchall():
        zoneMap[row["id"]] = row["long_name"]

    # fetch loot entries + raw zone field
    query = """
      SELECT
        lt.id                        AS loottable_id,
        lt.name                      AS loottable_name,
        lde.chance                   AS base_chance,
        le.multiplier                AS multiplier,
        (lde.chance * le.multiplier) AS effective_chance,
        gl.zone                      AS raw_zones
      FROM lootdrop_entries AS lde
      JOIN loottable_entries    AS le ON lde.lootdrop_id = le.lootdrop_id
      JOIN loottable            AS lt ON le.loottable_id = lt.id
      LEFT JOIN global_loot     AS gl ON lt.id = gl.loottable_id AND gl.enabled = 1
      WHERE lde.item_id = %s
      ORDER BY effective_chance DESC
    """
    with db.cursor() as cur:
      cur.execute(query, (itemId,))
      rows = cur.fetchall()

    # group by zone.long_name
    grouped = defaultdict(list)
    for r in rows:
      raw = r.get("raw_zones") or ""
      parts = [p for p in raw.split("|") if p.isdigit()]
      if not parts:
        keys = ["Unassigned"]
      else:
        keys = [zoneMap.get(int(p), "Unassigned") for p in parts]

      for zoneName in keys:
        grouped[zoneName].append({
          "loottableId":     r["loottable_id"],
          "loottableName":   r["loottable_name"],
          "baseChance":      float(r["base_chance"]),
          "multiplier":      int(r["multiplier"]),
          "effectiveChance": float(r["effective_chance"])
        })

    return render_template_string(TEMPLATE, itemId=itemId, grouped=grouped)
