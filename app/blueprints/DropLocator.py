NAME = "Drop Locator"

from pathlib import Path
URL_PREFIX = "/" + Path(__file__).stem.lower()

from flask import request, jsonify
from collections import defaultdict
from app import renderPage
import re

from api.models.items import get_item
from api.models.loot import get_drop_locations
from api.models.items import search_items  # for autocomplete

def register(app):
  @app.route(URL_PREFIX, methods=["GET"])
  def droplocator():
    raw = request.args.get("item_id", "").strip()
    itemId = int(re.search(r"\((\d+)\)$", raw).group(1)) if re.search(r"\((\d+)\)$", raw) else (int(raw) if raw.isdigit() else None)
    itemName = None
    grouped = defaultdict(list)

    if itemId:
      item = get_item(itemId)
      if item:
        itemName = item["name"]
      for r in get_drop_locations(itemId):
        zoneName = r["zone_longname"] or f"(Zone: {r['zone_shortname']})"
        mobName = r["npc_lastname"] or r["npc_name"]
        lvl = r["level"]
        maxLvl = r["maxlevel"]
        levelStr = str(lvl) if not maxLvl or maxLvl == lvl else f"{lvl}-{maxLvl}"
        grouped[zoneName].append({
          "base": float(r["base_chance"]),
          "mult": int(r["multiplier"]),
          "eff":  float(r["effective_chance"]),
          "mob":  mobName,
          "lvl":  levelStr,
          "pts":  r["spawn_points"] or ""
        })

    header = f"""
<div class="headerRow">
  <h1>{NAME}</h1>
</div>

<form action="{URL_PREFIX}" method="get" autocomplete="off">
  <input type="text" id="itemInput" name="item_id"
         placeholder="Enter item ID or name"
         value="{itemName + f' ({itemId})' if itemId and itemName else (itemId or '')}">
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
  const d = e.target.closest('div');
  if (!d) return;
  input.value = `${{d.dataset.name}} (${{d.dataset.id}})`;
  const h = document.createElement('input');
  h.type = 'hidden'; h.name = 'item_id'; h.value = d.dataset.id;
  input.form.appendChild(h);
  input.form.submit();
}});

document.addEventListener('click', e => {{
  if (!box.contains(e.target) && e.target !== input) box.style.display = 'none';
}});
</script>
"""

    if itemId and not grouped:
      body = "<p class='no-results'>No drop locations found for this item.</p>"
    else:
      body = f"<h2>{itemName} ({itemId})</h2>".join(
        f"<div class='zone'><h3>{zn}</h3><table><thead><tr><th>Mob</th><th>Base%</th>"
        f"<th>×</th><th>Effective%</th><th>Spawn Pts</th></tr></thead><tbody>"
        + "".join(
          f"<tr><td>{e['mob']} (Lv {e['lvl']})</td><td>{e['base']:.2f}%</td>"
          f"<td>{e['mult']}</td><td>{e['eff']:.2f}%</td><td>{e['pts']}</td></tr>"
          for e in entries
        )
        + "</tbody></table></div>"
        for zn, entries in grouped.items()
      )

    return renderPage(header, body)

  # autocomplete endpoint
  @app.route(f"{URL_PREFIX}/search")
  def droplocator_search():
    q = request.args.get("q", "").strip()
    return jsonify(results=search_items(q)) if q else jsonify(results=[])
