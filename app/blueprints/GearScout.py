NAME = "Gear Scout"

from pathlib import Path
import html
from flask import request
from web.utils import renderPage
from api.models.characters import CLASS_BITMASK, RACE_BITMASK
from api.models.items import (
  search_items_filtered,
  NUMERIC_ATTR_MAP,
  BOOL_FLAG_MAP,
  SLOT_OPTIONS,
  SORTABLE_FIELDS,
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

        function formatPrice(cp) {
          const pp = Math.floor(cp / 1000);
          cp %= 1000;
          const gp = Math.floor(cp / 100);
          cp %= 100;
          const sp = Math.floor(cp / 10);
          const cpLeft = cp % 10;

          const parts = [];
          if (pp) parts.push(`${pp}p`);
          if (gp) parts.push(`${gp}g`);
          if (sp) parts.push(`${sp}s`);
          if (cpLeft || parts.length === 0) parts.push(`${cpLeft}c`);

          return parts.join(' ');
        }

        function renderDrops(drops) {
          if (!drops.length) return '';

          const zonesGrouped = {};

          for (const drop of drops) {
            const npc = drop.npc || {};
            const zones = drop.zones || {};

            for (const [zoneShort, zoneData] of Object.entries(zones)) {
              const zoneKey = `${zoneData.zone_longname} (${zoneShort})`;
              if (!zonesGrouped[zoneKey]) zonesGrouped[zoneKey] = [];

              zonesGrouped[zoneKey].push({
                name: npc.name || 'Unknown',
                lastname: npc.lastname || '',
                level: npc.maxlevel && npc.maxlevel !== npc.level
                  ? `${npc.level} - ${npc.maxlevel}`
                  : `${npc.level ?? '??'}`,
                chance: drop.effective_chance ?? '?',
                spawnpoints: zoneData.spawnpoints || []
              });
            }
          }

          return Object.entries(zonesGrouped).map(([zone, npcList]) => {
            return `
              <div class="drop-zone-block">
                <strong>${zone}</strong>
                <ul class="drop-npc-list">
                  ${npcList.map(npc => `
                    <li>
                      <b>${npc.name} ${npc.lastname}</b> (Lvl ${npc.level}, ${npc.chance}%)
                      <ul class="spawnpoint-list">
                        ${npc.spawnpoints.map(sp => {
                          const tooltip = sp.placeholders?.length
                            ? ` title="Placeholders: ${sp.placeholders.replace(/"/g, '&quot;')}"`
                            : '';
                          const chance = sp.chance != null ? ` (${sp.chance}%)` : '';
                          return `<li${tooltip}>(${sp.y}, ${sp.x}, ${sp.z}) – ${formatRespawnTime(sp.respawntime)}${chance}</li>`;
                        }).join('')}
                      </ul>
                    </li>
                  `).join('')}
                </ul>
              </div>
            `;
          }).join('');
        }

        function renderMerchants(merchants) {
          if (!merchants.length) return '';

          const byZone = {};

          for (const m of merchants) {
            const zone = m.zone_longname || m.zone_shortname || 'Unknown Zone';
            if (!byZone[zone]) byZone[zone] = [];
            byZone[zone].push(m);
          }

          return Object.entries(byZone).map(([zone, list]) => {
            return `
              <div class="merchant-zone-block">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                  <strong>${zone}</strong>
                </div>
                <ul class="merchant-list">
                  ${list.map(m => {
                    const coords = (m.x != null && m.y != null)
                      ? ` (${m.y}, ${m.x}${m.z != null ? `, ${m.z}` : ''})`
                      : '';
                    const chance = (m.chance != null && m.chance < 100) ? ` (${m.chance}% chance)` : '';
                    return `<li><b>${m.Name || 'Unknown Merchant'}</b>${coords}${chance}</li>`;
                  }).join('')}
                </ul>
              </div>
            `;
          }).join('');
        }

        function renderRecipes(recipes) {
          if (!recipes.length) return '';

          // Group recipes by name
          const grouped = {};
          for (const recipe of recipes) {
            if (!grouped[recipe.name]) {
              grouped[recipe.name] = [];
            }
            grouped[recipe.name].push(recipe);
          }

          return Object.entries(grouped).map(([name, variants]) => {
            return `
              <div class="recipe-block">
                <h4 class="recipe-title">${name}</h4>
                <div class="recipe-section">
                  ${variants.map(variant => {
                    const list = (label, items, countField = 'componentCount') => {
                      if (!items?.length) return '';
                      return `
                        <div class="recipe-subsection">
                          <b>${label}:</b>
                          <ul class="recipe-list">
                            ${items.map(i => `
                              <li>${i[countField]} x 
                                <span class="eqtooltip" data-type="item" data-id="${i.id}">${i.name}</span>
                              </li>`).join('')}
                          </ul>
                        </div>`;
                    };

                    const failItems = variant.ingredients?.filter(i => i.failCount > 0);
                    const successReturn = variant.ingredients?.filter(i => i.successCount > 0 && i.componentCount > 0);
                    const outputs = variant.outputs?.filter(i => i.successCount > 0 && i.componentCount === 0);

                    return `
                      <div class="recipe-variant">
                        <div class="recipe-variant-meta">
                          <span class="tradeskill-name">${variant.tradeskill_name}</span>
                          <span class="skill-needed">Min: ${variant.skillNeeded}</span>
                          <span class="trivial">Trivial: ${variant.trivial}</span>
                        </div>
                        <div class="recipe-columns">
                          <div class="recipe-left-column">
                            ${list("Ingredients", variant.ingredients)}
                            ${list("Makes", outputs, "successCount")}
                          </div>
                          <div class="recipe-right-column">
                            ${list("Returned on Failure", failItems, "failCount")}
                            ${list("Returned on Success", successReturn, "successCount")}
                          </div>
                        </div>
                      </div>`;
                  }).join('')}
                </div>
              </div>`;
          }).join('');
        }

        function bindResultItemClicks() {
          document.querySelectorAll('.result-item').forEach(itemElement => {
            itemElement.addEventListener('click', async () => {
              const detailsBox = itemElement.querySelector('.result-details');
              if (!detailsBox.style.display || detailsBox.style.display === 'none') {
                const itemId = itemElement.getAttribute('data-itemid');
                const [dropsRes, merchantsRes, recipesRes] = await Promise.all([
                  fetch(`/api/item/${itemId}/drops`),
                  fetch(`/api/item/${itemId}/merchants`),
                  fetch(`/api/item/${itemId}/recipes`)
                ]);

                const drops = await dropsRes.json();
                const merchants = await merchantsRes.json();
                const recipes = await recipesRes.json();

                const parts = [];

                if (drops.length) {
                  parts.push(`<div class="source-header"><h3>Drops</h3></div>`);
                  parts.push(renderDrops(drops));
                }

                if (merchants.length) {
                  const merchantPrice = merchants?.[0]?.price != null ? formatPrice(merchants[0].price) : null;
                  parts.push(`
                    <div class="source-header">
                      <h3>Merchants</h3>
                      ${merchantPrice ? `<span class="merchant-price">${merchantPrice}</span>` : ''}
                    </div>
                  `);
                  parts.push(renderMerchants(merchants, true));
                }

                if (recipes.length) {
                  parts.push(`<div class="source-header"><h3>Tradeskill Recipes</h3></div>`);
                  parts.push(renderRecipes(recipes));
                }

                detailsBox.innerHTML = parts.join('');
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
