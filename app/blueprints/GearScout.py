NAME = "Gear Scout"

from pathlib import Path
import html
from flask import request
from web.utils import renderPage
from api.models.items import (
  search_items_filtered,
  NUMERIC_ATTR_MAP,
  BOOL_FLAG_MAP,
  SLOT_OPTIONS,
  SORTABLE_FIELDS,
  CLASS_BITMASK,
  RACE_BITMASK,
  ITEM_SOURCE_OPTIONS
)

URL_PREFIX = "/" + Path(__file__).stem
CMP_OPTIONS = ["=", ">=", "<="]

def _toI(val):
  return int(val) if val and val.isdigit() else None

def renderForm(nameRaw, slots, minLevel, maxLevel, minRecLevel, maxRecLevel, attrFilters,
               sort, sortOrder, limit, selectedClasses, selectedRaces, augmentOption, selectedSources,
               equippableOnly, boolFilters):
  esc = lambda x: html.escape(str(x) if x is not None else "")
  parts = ["<form method='get' action='#results'>"]

  parts.append(f"<label>Name: <input type='text' name='name' value='{esc(nameRaw)}'></label><br>")

  parts.append("<fieldset><legend>Slot(s)</legend>")
  for val, label in SLOT_OPTIONS:
    checked = "checked" if val in slots else ""
    parts.append(f"<label><input type='checkbox' name='slots' value='{val}' {checked}> {label}</label>")
  parts.append("</fieldset>")

  for attr in sorted(NUMERIC_ATTR_MAP.keys()):
    cmpVal = next((c for a, c, _ in attrFilters if a == attr), "")
    numVal = next((v for a, _, v in attrFilters if a == attr), "")
    cmpOptions = "".join(f"<option value='{c}' {'selected' if c == cmpVal else ''}>{c}</option>" for c in CMP_OPTIONS)
    parts.append(f"<label>{attr}: <select name='cmp_{attr}'>{cmpOptions}</select> "
                 f"<input type='number' name='{attr}' value='{esc(numVal)}'></label><br>")

  parts.append(f"<label>Required Level Min: <input type='number' name='minLevel' value='{esc(minLevel)}'></label> ")
  parts.append(f"<label>Max: <input type='number' name='maxLevel' value='{esc(maxLevel)}'></label><br>")

  parts.append(f"<label>Recommended Level Min: <input type='number' name='minRecLevel' value='{esc(minRecLevel)}'></label> ")
  parts.append(f"<label>Max: <input type='number' name='maxRecLevel' value='{esc(maxRecLevel)}'></label><br>")

  parts.append("<fieldset><legend>Class</legend>")
  for cls in sorted(CLASS_BITMASK):
    checked = "checked" if cls in selectedClasses else ""
    parts.append(f"<label><input type='checkbox' name='class' value='{cls}' {checked}> {cls}</label>")
  parts.append("</fieldset>")

  parts.append("<fieldset><legend>Race</legend>")
  for race in sorted(RACE_BITMASK):
    checked = "checked" if race in selectedRaces else ""
    parts.append(f"<label><input type='checkbox' name='race' value='{race}' {checked}> {race}</label>")
  parts.append("</fieldset>")

  parts.append("<fieldset><legend>Item Source</legend>")
  for src in ITEM_SOURCE_OPTIONS:
    checked = "checked" if src in selectedSources else ""
    parts.append(f"<label><input type='checkbox' name='itemSource' value='{src}' {checked}> {src.title()}</label>")
  parts.append("</fieldset>")

  parts.append(
    "<label>Augmentations: <select name='augmentOption'>"
    f"<option value='both' {'selected' if augmentOption == 'both' else ''}>Both</option>"
    f"<option value='only' {'selected' if augmentOption == 'only' else ''}>Only Augmentations</option>"
    f"<option value='exclude' {'selected' if augmentOption == 'exclude' else ''}>Only Non-Augmentations</option>"
    "</select></label><br>"
  )

  parts.append(f"<label>Equippable Only: <input type='checkbox' name='equippableOnly' {'checked' if equippableOnly else ''}></label><br>")

  parts.append("<fieldset><legend>Flags</legend>")
  for flag in BOOL_FLAG_MAP:
    checked = "checked" if boolFilters.get(flag) == 'true' else ""
    parts.append(f"<label><input type='checkbox' name='bool_{flag}' {checked}> {flag.title()}</label>")
  parts.append("</fieldset>")

  parts.append("<label>Sort by: <select name='sort'>")
  for key in SORTABLE_FIELDS:
    selected = "selected" if key == sort else ""
    parts.append(f"<option value='{key}' {selected}>{key}</option>")
  parts.append("</select></label> ")

  parts.append("<label>Order: <select name='sortOrder'>")
  for order in ["asc", "desc"]:
    selected = "selected" if order == sortOrder else ""
    parts.append(f"<option value='{order}' {selected}>{order.title()}</option>")
  parts.append("</select></label><br>")

  parts.append(f"<label>Limit: <input type='number' name='limit' value='{esc(limit)}'></label><br>")
  parts.append("<button type='submit'>Search</button></form>")

  return "\n".join(parts)

def register(app):
  @app.route(URL_PREFIX, methods=["GET"])
  def scout():
    args = request.args
    nameRaw = args.get("name", "")
    slots = args.getlist("slots")

    minLevel = _toI(args.get("minLevel"))
    maxLevel = _toI(args.get("maxLevel"))
    minRecLevel = _toI(args.get("minRecLevel"))
    maxRecLevel = _toI(args.get("maxRecLevel"))

    attrFilters = []
    for attr in NUMERIC_ATTR_MAP:
      cmpOp = args.get(f"cmp_{attr}")
      val = _toI(args.get(attr))
      if cmpOp and val is not None:
        attrFilters.append((attr, cmpOp, val))

    selectedClasses = args.getlist("class")
    selectedRaces = args.getlist("race")
    selectedSources = args.getlist("itemSource") or list(ITEM_SOURCE_OPTIONS.keys())

    augmentOption = args.get("augmentOption", "both")
    equippableOnly = args.get("equippableOnly") == "on"

    boolFilters = {}
    for flag in BOOL_FLAG_MAP:
      if args.get(f"bool_{flag}") == 'on':
        boolFilters[flag] = 'true'

    sort = args.get("sort", "name")
    sortOrder = args.get("sortOrder", "asc")
    limit = _toI(args.get("limit")) or 25
    currentPage = _toI(args.get("page")) or 1
    offset = (currentPage - 1) * limit

    classMask = sum(CLASS_BITMASK.get(c, 0) for c in selectedClasses) if selectedClasses else None
    raceMask = sum(RACE_BITMASK.get(r, 0) for r in selectedRaces) if selectedRaces else None

    result = search_items_filtered(
      nameQuery=nameRaw, slots=slots,
      minLevel=minLevel, maxLevel=maxLevel,
      minRecLevel=minRecLevel, maxRecLevel=maxRecLevel,
      attrFilters=attrFilters,
      boolFilters=boolFilters,
      classMask=classMask, raceMask=raceMask,
      augmentOption=augmentOption,
      equippableOnly=equippableOnly,
      itemSourceFilters=selectedSources,
      limit=limit, offset=offset,
      sortField=SORTABLE_FIELDS.get(sort, "i.Name"),
      sortOrder=sortOrder
    )

    htmlContent = renderForm(
      nameRaw, slots, minLevel, maxLevel, minRecLevel, maxRecLevel,
      attrFilters, sort, sortOrder, limit,
      selectedClasses, selectedRaces, augmentOption, selectedSources,
      equippableOnly, boolFilters
    )

    htmlContent += f"<h2>Results ({result['total']})</h2><ul id='results'>"
    for item in result["items"]:
      icons = []
      if item.get('lootdropEntries'):
        icons.append('<span title="Drop">🗡️</span>')
      if item.get('merchantListEntries'):
        icons.append('<span title="Merchant">🛒</span>')
      if item.get('tradeskillRecipeEntries'):
        icons.append('<span title="Tradeskill">⚒️</span>')
      if item.get('questEntries'):
        icons.append('<span title="Quest">📜</span>')
      if item.get('unobtainable'):
        icons.append('<span title="Unobtainable">❌</span>')

      iconDisplay = " ".join(icons)

      statSummary = ""
      if attrFilters:
        filteredStats = []
        for attr, _, _ in attrFilters:
          val = item.get(attr)
          if val is not None:
            sign = "+" if val > 0 else ""
            filteredStats.append(f"{attr}: {sign}{val}")
        if filteredStats:
          statSummary = f" <small>({' ,'.join(filteredStats)})</small>"

      htmlContent += (
        f"<li class='result-item' data-itemid='{item['id']}'>"
          "<div class='result-header'>"
            f"<span class='item-name eqtooltip' data-type='item' data-id='{item['id']}'>"
              f"{html.escape(item['Name'])}"
            "</span> "
            f"<span class='item-stats'>{statSummary.strip()}</span>"
            f"<span class='result-icons'>{iconDisplay}</span>"
          "</div>"
          "<div class='result-details'></div>"
        "</li>"
      )
    htmlContent += "</ul>"
    htmlContent += r"""
    <script>
      function formatRespawnTime(seconds) {
        const days = Math.floor(seconds / 86400);
        seconds %= 86400;
        const hours = Math.floor(seconds / 3600);
        seconds %= 3600;
        const minutes = Math.floor(seconds / 60);
        seconds = seconds % 60;

        const parts = [];
        if (days > 0) parts.push(`${days}d`);
        if (hours > 0) parts.push(`${hours}h`);
        if (minutes > 0) parts.push(`${minutes}m`);
        if (seconds > 0) parts.push(`${seconds}s`);

        return parts.join(' ') || '0s';
      }

      function bindResultItemClicks() {
        document.querySelectorAll('.result-item').forEach(itemElement => {
          itemElement.addEventListener('click', async () => {
            const detailsBox = itemElement.querySelector('.result-details');
            if (!detailsBox.style.display || detailsBox.style.display === 'none') {
              const itemId = itemElement.getAttribute('data-itemid');
              const res = await fetch(`/api/item/${itemId}/drops`);
              const drops = await res.json();

              if (!drops.length) {
                detailsBox.innerHTML = '<em>No drop sources available.</em>';
              } else {
                detailsBox.innerHTML = drops.map(drop => {
                  const npc = drop.npc || {};
                  const zones = drop.zones || {};
                  let zoneDetails = '';

                  for (const [zoneShort, zoneData] of Object.entries(zones)) {
                    const spawnPoints = zoneData.spawnpoints || [];
                    const spawnPointsText = spawnPoints.length
                      ? spawnPoints.map(sp => 
                          `(${sp.x}, ${sp.y}, ${sp.z}) ${formatRespawnTime(sp.respawntime)}`
                        ).join('<br>')
                      : '<em>No spawn points recorded</em>';

                    zoneDetails += `
                      <div class="zone-section">
                        <strong>${zoneData.zone_longname} (${zoneShort})</strong><br>
                        Spawn Points:<br>
                        ${spawnPointsText}
                      </div><br>`;
                  }

                  const levelRange = npc.level
                    ? (npc.maxlevel && npc.maxlevel !== npc.level
                        ? `${npc.level} - ${npc.maxlevel}`
                        : `${npc.level}`)
                    : '??';

                  return `
                    <div class="drop-source">
                      <strong>NPC:</strong> ${npc.name || 'Unknown'} ${npc.lastname || ''}<br>
                      Level: ${levelRange}<br>
                      Effective Chance: ${drop.effective_chance}%<br>
                      ${zoneDetails}
                    </div>`;
                }).join('<hr>');

                detailsBox.innerHTML += `
                  <hr>
                  <details>
                    <summary>Raw JSON Data</summary>
                    <pre>${JSON.stringify(drops, null, 2)}</pre>
                  </details>
                `;
              }
              detailsBox.style.display = 'block';
            } else {
              detailsBox.style.display = 'none';
            }
          });
        });
      }

      document.addEventListener('DOMContentLoaded', () => {
        bindResultItemClicks();
      });
    </script>
    """

    totalResults = result['total']
    totalPages = (totalResults + limit - 1) // limit

    if totalPages > 1:
      from web.utils import renderPagination
      queryParams = request.args.to_dict(flat=False)
      paginationHtml = renderPagination(currentPage, totalPages, URL_PREFIX, queryParams)
      htmlContent += paginationHtml

    return renderPage(htmlContent)
