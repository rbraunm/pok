NAME = "Gear Scout"

from pathlib import Path
import html
from typing import List
from flask import request, jsonify, json as flask_json
from app import renderPage
from api.models.items import (
  search_items_filtered,
  NUMERIC_ATTR_MAP,
  SLOT_OPTIONS,
  SORTABLE_FIELDS
)

URL_PREFIX = "/" + Path(__file__).stem
CMP_OPTIONS = ["=", ">=", "<="]
POK_DEBUG = False

def _toi(v: str | None):
  return int(v) if v and v.isdigit() else None

def _tof(v: str | None):
  try:
    return float(v) if v else None
  except ValueError:
    return None

def _form(name_raw, slots, minl, maxl, mind, maxd, minr, maxr,
          equip, attr_filters, sort, page, limit) -> str:
  esc = lambda x: html.escape(str(x) if x is not None else "")
  checked = lambda s: "checked" if s in slots else ""

  parts: List[str] = ["<form method='get'>"]
  parts.append(f"<label>Name: <input type='text' name='name' value='{esc(name_raw)}'></label>")
  parts.append("<fieldset><legend>Slot(s)</legend>")
  for val, label in SLOT_OPTIONS:
    parts.append(
      f"<label><input type='checkbox' name='slots' value='{val}' {checked(val)}> {label}</label>"
    )
  parts.append("</fieldset>")

  parts.append("<fieldset><legend>Attributes</legend>")
  for attr in sorted(NUMERIC_ATTR_MAP.keys()):
    cmp_val = next((c for a, c, _ in attr_filters if a == attr), "")
    num_val = next((v for a, _, v in attr_filters if a == attr), "")
    opts = "".join(
      f"<option value='{c}' {'selected' if c == cmp_val else ''}>{c}</option>"
      for c in CMP_OPTIONS
    )
    parts.append(
      f"<label>{attr}: <select name='cmp_{attr}'>{opts}</select> "
      f"<input type='number' name='{attr}' value='{esc(num_val)}' size='4'></label><br>"
    )
  parts.append("</fieldset>")

  parts.append("<fieldset><legend>Sort</legend>")
  parts.append("<label>Sort by: <select name='sort'>")
  for key in SORTABLE_FIELDS:
    sel = "selected" if key == sort else ""
    parts.append(f"<option value='{key}' {sel}>{key.title()}</option>")
  parts.append("</select></label></fieldset>")

  parts.append("<button type='submit'>Search</button>")
  parts.append("</form>")
  return "\n".join(parts)

def _pagination_controls(page: int, total_items: int, limit: int, base_query: str) -> str:
  if total_items == 0:
    return ""

  total_pages = (total_items + limit - 1) // limit
  parts = [f"<div class='pagination'>"]

  def page_link(p):
    return f"<strong>{p}</strong> " if p == page else f"<a href='{base_query}&page={p}'>{p}</a> "

  if total_pages <= 10:
    parts.extend(page_link(p) for p in range(1, total_pages + 1))
  else:
    parts.append(page_link(1))
    if page > 4:
      parts.append("... ")

    for p in range(max(2, page - 2), min(total_pages, page + 3)):
      parts.append(page_link(p))

    if page < total_pages - 3:
      parts.append("... ")

    parts.append(page_link(total_pages))

  parts.append(
    f"""<form method='get' style='display:inline'>
         <input type='hidden' name='limit' value='{limit}'>"""
  )
  for k, v in (kv.split('=') for kv in base_query.split('?')[1].split('&') if kv and not kv.startswith('page=')):
    parts.append(f"<input type='hidden' name='{html.escape(k)}' value='{html.escape(v)}'>")
  parts.append(
    f"""Go to page: <input type='number' name='page' value='{page}' min='1' max='{total_pages}' size='3'>
         <button type='submit'>Go</button>
       </form>"""
  )

  parts.append("</div>")
  return "".join(parts)

def register(app):
  global POK_DEBUG
  POK_DEBUG = app.debug or app.config.get("POK_DEBUG", False)

  @app.route(URL_PREFIX, methods=["GET"])
  def scout():
    name_raw = request.args.get("name", "")
    slots = request.args.getlist("slots")
    minl, maxl = _toi(request.args.get("minLevel")), _toi(request.args.get("maxLevel"))
    mind, maxd = _toi(request.args.get("minDelay")), _toi(request.args.get("maxDelay"))
    minr, maxr = _tof(request.args.get("minRatio")), _tof(request.args.get("maxRatio"))
    equip = request.args.get("equippable") == "1"
    sort = request.args.get("sort", "name")
    page = _toi(request.args.get("page")) or 1
    limit = _toi(request.args.get("limit")) or 50
    offset = (page - 1) * limit

    attr_filters = []
    for attr in NUMERIC_ATTR_MAP:
      cmp = request.args.get(f"cmp_{attr}")
      val = _toi(request.args.get(attr))
      if cmp and val is not None:
        attr_filters.append((attr, cmp, val))

    result = search_items_filtered(
      nameQuery=name_raw,
      slots=slots,
      minLevel=minl,
      maxLevel=maxl,
      minDelay=mind,
      maxDelay=maxd,
      minRatio=minr,
      maxRatio=maxr,
      attrFilters=attr_filters,
      equippableOnly=equip,
      limit=limit,
      offset=offset,
      sortField=SORTABLE_FIELDS.get(sort, "i.Name"),
      sortOrder="asc"
    )

    if "api" in request.args:
      return jsonify(result["items"])

    body = _form(
      name_raw, slots, minl, maxl, mind, maxd, minr, maxr,
      equip, attr_filters, sort, page, limit
    )

    body += "<h2>Results</h2>"
    if result["items"]:
      body += "<ul>"
      for item in result["items"]:
        body += f"<li>{html.escape(item['Name'])} ({item['id']})</li>"
      body += "</ul>"
    else:
      body += "<p>No items found.</p>"

    base_query = request.full_path.split("&page=")[0].split("?")[0] + "?" + "&".join(
      f"{k}={v}" for k, v in request.args.items() if k != "page"
    )
    pagination_html = _pagination_controls(page, total_items=result["total"], limit=limit, base_query=base_query)
    body += pagination_html

    if POK_DEBUG:
      debug_json = html.escape(flask_json.dumps(result, indent=2))
      body += (
        "<hr><details><summary>Debug Output (JSON)</summary>"
        f"<pre>{debug_json}</pre></details>"
      )

    return renderPage(NAME, body)
