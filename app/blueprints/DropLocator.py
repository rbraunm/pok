NAME = "Drop Locator"

from pathlib import Path
URL_PREFIX = "/" + Path(__file__).stem

from flask import request, jsonify
from collections import defaultdict
from app import renderPage
import re
import html

from api.models.items import get_item, search_items, ItemNotFoundError
from api.models.loot import get_drop_locations

def register(app):
  @app.route(URL_PREFIX, methods=["GET"])
  def droplocator():
    raw = request.args.get("item_id", "").strip()
    itemId = int(re.search(r"\((\d+)\)$", raw).group(1)) if re.search(r"\((\d+)\)$", raw) else (int(raw) if raw.isdigit() else None)
    itemName = None
    grouped = defaultdict(list)

    if itemId:
      try:
        item = get_item(itemId)
        itemName = item["Name"]
        for r in get_drop_locations(itemId):
          zoneName = r["zone_longname"] or f"(Zone: {r['zone_shortname']})"
          mobName = r["npc_lastname"] or r["npc_name"]
          lvl = r.get("level") or 0
          maxLvl = r.get("maxlevel") or 0
          levelStr = str(lvl) if not maxLvl or maxLvl == lvl else f"{lvl}-{maxLvl}"
          grouped[zoneName].append({
            "base": float(r["base_chance"]),
            "mult": int(r["multiplier"]),
            "eff":  float(r["effective_chance"]),
            "mob":  mobName,
            "lvl":  levelStr,
            "pts":  r["spawn_points"] or ""
          })
      except ItemNotFoundError:
        print(f"Item with ID {itemId} not found in database.")
        itemName = None

    escapedVal = html.escape(f"{itemName} ({itemId})") if itemId and itemName else html.escape(str(itemId or ""))
    header = f"""
<div class="headerRow">
  <h1>{NAME}</h1>
</div>

<form action="{URL_PREFIX}" method="get" autocomplete="off">
  <input type="text" id="itemInput" name="item_id"
         placeholder="Enter item ID or name"
         value="{escapedVal}">
  <button type="submit">Search</button>
  <div id="autocomplete" class="autocomplete-suggestions" style="display:none;"></div>
</form>
<script>
const input = document.getElementById('itemInput');
const box   = document.getElementById('autocomplete');

input.addEventListener('input', () => {{
  const q = input.value.trim();
  if (q.length < 2) return box.style.display = 'none';
  fetch('{URL_PREFIX}/search?q=' + encodeURIComponent(q))
    .then(r => r.json())
    .then(data => {{
      if (!data.results.length) return box.style.display = 'none';
      box.innerHTML = data.results.map(r =>
        `<div data-id="${{r.id}}" data-name="${{r.name}}">${{r.name}} (${{r.id}})</div>`
      ).join('');
      box.style.display = 'block';
    }});
}});

box.addEventListener('click', e => {{
  e.preventDefault();
  e.stopPropagation();

  const d = e.target.closest('div');
  if (!d) return;
  input.value = d.dataset.id;
  input.form.submit();
}});

input.addEventListener('focus', () => {{
  input.value = '';
  box.style.display = 'none';
}});

document.addEventListener('click', e => {{
  if (!box.contains(e.target) && e.target !== input) box.style.display = 'none';
}});
</script>
"""

    if itemId and itemName and grouped:
      body = f"<h2>{html.escape(itemName)} ({itemId})</h2>" + "".join(
        f"<div class='zone'><h3>{html.escape(zn)}</h3><table><thead><tr><th>Mob</th><th>Base%</th>"
        f"<th>×</th><th>Effective%</th><th>Spawn Points</th></tr></thead><tbody>"
        + "".join(
          f"<tr><td>{html.escape(e['mob'])} (Lv {e['lvl']})</td><td>{e['base']:.2f}%</td>"
          f"<td>{e['mult']}</td><td>{e['eff']:.2f}%</td><td>{e['pts']}</td></tr>"
          for e in entries
        )
        + "</tbody></table></div>"
        for zn, entries in grouped.items()
      )
    elif itemId and itemName and not grouped:
      body = "<p class='no-results'>No drop locations found for this item.</p>"
    elif itemId and not itemName:
      body = f"<p class='no-results'>Item with ID {itemId} not found.</p>"
    else:
      body = ""

    return renderPage(header=header, body=body)

  @app.route(f"{URL_PREFIX}/search")
  def droplocator_search():
    q = request.args.get("q", "").strip()
    return jsonify(results=search_items(q)) if q else jsonify(results=[])
