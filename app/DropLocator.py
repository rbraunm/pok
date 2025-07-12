NAME = "Drop Locator"
URL_PREFIX = "/droplocator"

from flask import request, jsonify
from db import getDb
from collections import defaultdict
from app import renderPage
import re

def register(app):
  @app.route(URL_PREFIX, methods=["GET"])
  def droplocator():
    itemIdRaw = request.args.get("item_id", "").strip()
    itemId = None
    itemName = None

    match = re.search(r"\((\d+)\)$", itemIdRaw)
    if match:
      itemId = int(match.group(1))
    elif itemIdRaw.isdigit():
      itemId = int(itemIdRaw)

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
              ROUND(s2.y, 1), ', ',
              ROUND(s2.x, 1), ', ',
              ROUND(s2.z, 1)
            ) SEPARATOR '<br>'
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

    header = f"""
<h1>Drop Locations for {'(ID ' + str(itemId) + ')' if itemId and not itemName else (itemName + ' (' + str(itemId) + ')') if itemName else ''}</h1>
<form action="{URL_PREFIX}" method="get" autocomplete="off">
  <input type="text" id="itemInput" name="item_id" placeholder="Enter item ID or name" value="{itemName + f' ({itemId})' if itemId and itemName else itemId or ''}">
  <button type="submit">Search</button>
  <div id="autocomplete" class="autocomplete-suggestions" style="display:none;"></div>
</form>
<script>
const input = document.getElementById('itemInput');
const box = document.getElementById('autocomplete');

input.addEventListener('focus', () => {{
  input.value = "";
  box.style.display = "none";
}});

input.addEventListener('input', () => {{
  const q = input.value;
  if (q.length < 2) return box.style.display = 'none';

  fetch('{URL_PREFIX}/search?q=' + encodeURIComponent(q))
    .then(res => res.json())
    .then(data => {{
      if (!data.results.length) return box.style.display = 'none';
      box.innerHTML = data.results.map(r =>
        `<div data-id="${{r.id}}" data-name="${{r.name}}">${{r.name}} (${{r.id}})</div>`
      ).join('');
      box.style.display = 'block';
    }});
}});

box.addEventListener('click', (e) => {{
  const div = e.target.closest('div');
  if (!div) return;
  const displayValue = `${{div.dataset.name}} (${{div.dataset.id}})`;
  input.value = displayValue;

  const form = input.closest("form");
  const hiddenInput = document.createElement("input");
  hiddenInput.type = "hidden";
  hiddenInput.name = "item_id";
  hiddenInput.value = div.dataset.id;
  form.appendChild(hiddenInput);
  form.submit();
}});

document.addEventListener('click', e => {{
  if (!box.contains(e.target) && e.target !== input) {{
    box.style.display = 'none';
  }}
}});
</script>
"""

    if itemId and not grouped:
      body = "<p class='no-results'>No drop locations found for this item.</p>"
    else:
      body = ""
      for zoneName, entries in grouped.items():
        body += f"<div class='zone'><h2>{zoneName}</h2><table><thead><tr><th>Drops From</th><th>Base Chance</th><th>Multiplier</th><th>Effective Chance</th><th>Spawn Location(s)</th></tr></thead><tbody>"
        for e in entries:
          body += f"<tr><td>{e['mobName']} (Level {e['mobLevel']})</td><td>{e['baseChance']:.2f}%</td><td>{e['multiplier']}×</td><td>{e['effectiveChance']:.2f}%</td><td class='spawn-cell'>{e['spawnPoints']}</td></tr>"
        body += "</tbody></table></div>"

    return renderPage(header, body)

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
