NAME = "Gear Scout"

from pathlib import Path
import html
from flask import request, url_for
from web.utils import renderPage
from api.models.characters import CLASS_BITMASK, RACE_BITMASK
from applogging import get_logger

logger = get_logger(__name__)

from api.models.items import (
  search_items_filtered,
  NUMERIC_ATTR_MAP,
  BOOL_FLAG_MAP,
  SLOT_OPTIONS,
  SORTABLE_FIELDS,
  ITEM_SOURCE_OPTIONS,
  get_spell_options_for
)

URL_PREFIX = "/" + Path(__file__).stem
CMP_OPTIONS = ["=", ">=", "<="]

def _toI(val):
  return int(val) if val and val.isdigit() else None

def renderForm(nameRaw, slots, minLevel, maxLevel, minRecLevel, maxRecLevel, attrFilters,
               sort, sortOrder, limit, selectedClasses, selectedRaces, augmentOption, selectedSources,
               equippableOnly, boolFilters,
               focusOptions, clickOptions, procOptions,
               selectedFocusIds, selectedClickIds, selectedProcIds, bardOptions, selectedBardIds):
  esc = lambda x: html.escape(str(x) if x is not None else "")

  def select(name, label, options, selectedIds, size=5):
    selectedSet = {str(v) for v in (selectedIds or [])}
    html_opts = []
    for opt in options:
      sel = " selected" if str(opt["id"]) in selectedSet else ""
      html_opts.append(f"<option value='{opt['id']}'{sel}>{html.escape(opt['name'])}</option>")
    return (
      f"<div class='gs-selectblock'>"
      f"  <label class='gs-label'>{label}</label>"
      f"  <select name='{name}' multiple size='{size}' class='gs-multi'>"
      + "".join(html_opts) +
      "  </select>"
      "</div>"
    )

  def select_from_pairs(name, label, pairs, selectedVals, size=5):
    selectedSet = {str(v) for v in (selectedVals or [])}
    opts = []
    for val, lab in pairs:
      val_str = html.escape(str(val))
      lab_str = html.escape(str(lab))
      sel = " selected" if val_str in selectedSet else ""
      opts.append(f"<option value='{val_str}'{sel}>{lab_str}</option>")
    return (
      f"<div class='gs-selectblock'>"
      f"  <label class='gs-label'>{label}</label>"
      f"  <select name='{name}' multiple size='{size}' class='gs-multi'>"
      + "".join(opts) +
      "  </select>"
      "</div>"
    )

  # map for fast lookup of current numeric attr filters
  attrCmp = {a: c for a, c, _ in attrFilters}
  attrVal = {a: v for a, _, v in attrFilters}

  # item source (still checkboxes)
  srcHtml = []
  for src in ITEM_SOURCE_OPTIONS:
    checked = "checked" if src in selectedSources else ""
    srcHtml.append(f"<label class='gs-check gs-chip'><input type='checkbox' name='itemSource' value='{src}' {checked}><span>{src.title()}</span></label>")

  # flags (still checkboxes)
  flagHtml = []
  for flag in BOOL_FLAG_MAP:
    checked = "checked" if boolFilters.get(flag) == 'true' else ""
    flagHtml.append(f"<label class='gs-check gs-chip'><input type='checkbox' name='bool_{flag}' {checked}><span>{flag.title()}</span></label>")

  # numeric attr controls
  attrRows = []
  for attr in sorted(NUMERIC_ATTR_MAP.keys()):
    cmpVal = attrCmp.get(attr, "")
    numVal = esc(attrVal.get(attr, ""))
    cmpOptions = "".join(
      f"<option value='{c}' {'selected' if c == cmpVal else ''}>{c}</option>"
      for c in ["=", ">=", "<="]
    )
    attrRows.append(
      f"<div class='gs-attr'>"
      f"  <label class='gs-attr-label' for='attr_{attr}'>{attr}</label>"
      f"  <select name='cmp_{attr}' class='gs-cmp' aria-label='{attr} comparator'>{cmpOptions}</select>"
      f"  <input id='attr_{attr}' type='number' name='{attr}' value='{numVal}' class='gs-num" + (" gs-dec" if attr == 'ratio' else "") + f"'" + (" step='any'" if attr == 'ratio' else "") + ">"
      f"</div>"
    )

  # Spell selects (shorter)
  focusSelect = select("focusId", "Focus", focusOptions, selectedFocusIds, size=5)
  clickSelect = select("clickId", "Click", clickOptions, selectedClickIds, size=5)
  procSelect  = select("procId",  "Proc",  procOptions,  selectedProcIds,  size=5)
  bardSelect  = select("bardId",  "Bard",  bardOptions,  selectedBardIds, size=5)

  # Slots / Class / Race (shorter)
  slotsSelectHtml = select_from_pairs("slots", "Slot(s)", SLOT_OPTIONS, slots, size=5)
  classPairs = [(c, c) for c in sorted(CLASS_BITMASK.keys())]
  racesPairs = [(r, r) for r in sorted(RACE_BITMASK.keys())]
  classSelectHtml = select_from_pairs("class", "Class", classPairs, selectedClasses, size=5)
  raceSelectHtml  = select_from_pairs("race",  "Race",  racesPairs,  selectedRaces,  size=5)

  return """
  <form method='get' action='#gearscout-results' class='gs-form'>
    <div class='gs-row gs-topbar'>
      <div class='gs-col name'>
        <label class='gs-label'>Name</label>
        <input type='text' name='name' value='""" + esc(nameRaw) + """' placeholder='Item name…'>
      </div>

      <div class='gs-col sources'>
        <label class='gs-label'>Item Source</label>
        <div class='gs-checkgrid gs-chips'>""" + "".join(srcHtml) + """</div>
      </div>

      <div class='gs-col aug'>
        <label class='gs-label'>Augmentations</label>
        <select name='augmentOption'>
          <option value='both' """ + ("selected" if augmentOption == "both" else "") + """>Both</option>
          <option value='only' """ + ("selected" if augmentOption == "only" else "") + """>Only Augmentations</option>
          <option value='exclude' """ + ("selected" if augmentOption == "exclude" else "") + """>Only Non-Augmentations</option>
        </select>
        <label class='gs-inline'><input type='checkbox' name='equippableOnly' """ + ("checked" if equippableOnly else "") + """> Equippable Only</label>
      </div>

      <div class='gs-col sort'>
        <label class='gs-label'>Sort</label>
        <div class='gs-inline-row'>
          <select name='sort'>""" + "".join(
            f"<option value='{key}' {'selected' if key == sort else ''}>{key}</option>" for key in SORTABLE_FIELDS
          ) + """</select>
          <select name='sortOrder'>
            <option value='asc' """ + ("selected" if sortOrder == "asc" else "") + """>Asc</option>
            <option value='desc' """ + ("selected" if sortOrder == "desc" else "") + """>Desc</option>
          </select>
          <label class='gs-inline'>Limit <input type='number' name='limit' value='""" + esc(limit) + """' class='gs-limit'></label>
          <button type='submit'>Search</button>
        </div>
      </div>
    </div>

    <fieldset class='gs-fieldset'>
      <legend>Spell Filters</legend>
      <div class='gs-selectgrid'>
        """ + focusSelect + clickSelect + procSelect + bardSelect + """
      </div>
    </fieldset>

    <fieldset class='gs-fieldset'>
      <legend>Slot / Class / Race</legend>
      <div class='gs-selectgrid'>
        """ + slotsSelectHtml + classSelectHtml + raceSelectHtml + """
      </div>
    </fieldset>

    <div class='gs-row'>
      <div class='gs-col half'>
        <fieldset class='gs-fieldset'>
          <legend>Required Level</legend>
          <div class='gs-range'>
            <label>Min <input type='number' name='minLevel' value='""" + esc(minLevel) + """'></label>
            <span class='dash'>–</span>
            <label>Max <input type='number' name='maxLevel' value='""" + esc(maxLevel) + """'></label>
          </div>
        </fieldset>
      </div>
      <div class='gs-col half'>
        <fieldset class='gs-fieldset'>
          <legend>Recommended Level</legend>
          <div class='gs-range'>
            <label>Min <input type='number' name='minRecLevel' value='""" + esc(minRecLevel) + """'></label>
            <span class='dash'>–</span>
            <label>Max <input type='number' name='maxRecLevel' value='""" + esc(maxRecLevel) + """'></label>
          </div>
        </fieldset>
      </div>
    </div>

    <fieldset class='gs-fieldset'>
      <legend>Attributes</legend>
      <div class='gs-attrs-grid'>
        """ + "".join(attrRows) + """
      </div>
    </fieldset>

    <fieldset class='gs-fieldset'>
      <legend>Flags</legend>
      <div class='gs-checkgrid gs-chips'>""" + "".join(flagHtml) + """</div>
    </fieldset>
  </form>
  """

def register(app):
  @app.route(URL_PREFIX, methods=["GET"])
  def scout():
    args = request.args
    nameRaw = args.get("name", "")
    slots = args.getlist("slots")               # works for multiselect
    minLevel = _toI(args.get("minLevel"))
    maxLevel = _toI(args.get("maxLevel"))
    minRecLevel = _toI(args.get("minRecLevel"))
    maxRecLevel = _toI(args.get("maxRecLevel"))

    def _ids(key):
      vals = args.getlist(key)
      out = []
      for v in vals:
        try:
          out.append(int(v))
        except (TypeError, ValueError):
          logger.exception("Exception in blueprints/GearScout.py")
          pass
      return out

    selectedFocusIds = _ids("focusId")
    selectedClickIds = _ids("clickId")
    selectedProcIds  = _ids("procId")
    selectedBardIds = _ids("bardId")

    attrFilters = []
    for attr in NUMERIC_ATTR_MAP:
      cmpOp = args.get(f"cmp_{attr}")
      try:
        val = (float(args.get(attr)) if attr == 'ratio' else int(args.get(attr))) if args.get(attr) not in (None, "") else None
      except ValueError:
        logger.exception("Exception in blueprints/GearScout.py")
        val = None
      if cmpOp and val is not None:
        attrFilters.append((attr, cmpOp, val))

    selectedClasses = args.getlist("class")     # works for multiselect
    selectedRaces   = args.getlist("race")      # works for multiselect
    selectedSources = args.getlist("itemSource") or list(ITEM_SOURCE_OPTIONS.keys())

    augmentOption   = args.get("augmentOption", "both")
    equippableOnly  = args.get("equippableOnly") == "on"

    boolFilters = {}
    for flag in BOOL_FLAG_MAP:
      if args.get(f"bool_{flag}") == 'on':
        boolFilters[flag] = 'true'

    sort = args.get("sort", "name")
    sortOrder = args.get("sortOrder", "asc")
    try:
      limit = int(args.get("limit")) if args.get("limit") else 25
    except ValueError:
      logger.exception("Exception in blueprints/GearScout.py")
      limit = 25
    try:
      currentPage = int(args.get("page")) if args.get("page") else 1
    except ValueError:
      logger.exception("Exception in blueprints/GearScout.py")
      currentPage = 1
    offset = (currentPage - 1) * limit

    classMask = sum(CLASS_BITMASK.get(c, 0) for c in selectedClasses) if selectedClasses else None
    raceMask  = sum(RACE_BITMASK.get(r, 0) for r in selectedRaces)   if selectedRaces   else None

    focusOptions = get_spell_options_for("focus")
    clickOptions = get_spell_options_for("click")
    procOptions  = get_spell_options_for("proc")
    bardOptions  = get_spell_options_for("bard")

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
      focusIds=selectedFocusIds, clickIds=selectedClickIds, procIds=selectedProcIds, bardIds=selectedBardIds,
      limit=limit, offset=offset,
      sortField=SORTABLE_FIELDS.get(sort, "i.Name"),
      sortOrder=sortOrder
    )

    # light, useful log
    logger.info(f"GearScout query name='{nameRaw}' results={result['total']} page={currentPage} limit={limit}")

    htmlContent = renderForm(
      nameRaw, slots, minLevel, maxLevel, minRecLevel, maxRecLevel,
      attrFilters, sort, sortOrder, limit,
      selectedClasses, selectedRaces, augmentOption, selectedSources,
      equippableOnly, boolFilters,
      focusOptions, clickOptions, procOptions,
      selectedFocusIds, selectedClickIds, selectedProcIds, bardOptions, selectedBardIds
    )

    htmlContent += f"<h2>Results ({result['total']})</h2><ul id='gearscout-results'>"
    for item in result["items"]:
      icons = []
      if item.get('lootdropEntries'):
        icons.append('<span data-source="drops" role="button" tabindex="0" title="Drops">🗡️</span>')
      if item.get('merchantListEntries'):
        icons.append('<span data-source="merchants" role="button" tabindex="0" title="Merchants">🛒</span>')
      if item.get('tradeskillRecipeEntries'):
        icons.append('<span data-source="recipes" role="button" tabindex="0" title="Recipes">⚒️</span>')
      if item.get('questEntries'):
        icons.append('<span title="Quest">📜</span>')
      if item.get('unobtainable'):
        icons.append('<span title="Unobtainable">❌</span>') # If everything works, this should never appear
      iconDisplay = " ".join(icons)

      spellBits = []
      if item.get('focusname'):
        spellBits.append(f"Focus: {html.escape(item['focusname'])}")
      if item.get('procname'):
        spellBits.append(f"Proc: {html.escape(item['procname'])}")
      if item.get('clickname'):
        spellBits.append(f"Click: {html.escape(item['clickname'])}")
      if item.get('bardspellname'):
        spellBits.append(f"Bard: {html.escape(item['bardspellname'])}")

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

      if spellBits:
        statSummary = (statSummary or "") + f" <small>[{' | '.join(spellBits)}]</small>"

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

    # ES module (deferred by default)
    script_src = url_for('static', filename='js/gearscout.js')
    htmlContent += f"<script type='module' src='{script_src}'></script>"

    totalResults = result['total']
    totalPages = (totalResults + limit - 1) // limit
    if totalPages > 1:
      from web.utils import renderPagination
      queryParams = request.args.to_dict(flat=False)
      paginationHtml = renderPagination(currentPage, totalPages, URL_PREFIX, queryParams)
      htmlContent += paginationHtml

    return renderPage(htmlContent)
