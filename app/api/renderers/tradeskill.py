from __future__ import annotations

import html
from typing import List, Dict, Any, Optional
from applogging import get_logger

logger = get_logger(__name__)

def _get_trivial_color_class(skill: int, trivial: int) -> str:
  if skill is None:
    return ""
  try:
    skill = int(skill)
    trivial = int(trivial)
  except Exception:
    return ""
  if trivial <= int(skill * 0.95):
    return "eq-color-grey"
  elif trivial <= skill:
    return "eq-color-green"
  elif trivial <= skill + 15:
    return "eq-color-lightblue"
  elif trivial <= skill + 35:
    return "eq-color-blue"
  elif trivial <= skill + 50:
    return "eq-color-yellow"
  else:
    return "eq-color-red"

def _get_source_icons(item: Dict[str, Any]) -> str:
  sources = item.get("sources", {}) or {}
  icons: list[str] = []
  if sources.get("lootdrop"):
    icons.append('<span title="Drop">🗡️</span>')
  if sources.get("merchant"):
    icons.append('<span title="Merchant">🛒</span>')
  if sources.get("tradeskill"):
    icons.append('<span title="Tradeskill">⚒️</span>')
  if sources.get("quest"):
    icons.append('<span title="Quest">📜</span>')
  if item.get("unobtainable"):
    icons.append('<span title="Unobtainable">❌</span>')
  return f"<span class='result-icons'> {''.join(icons)}</span>" if icons else ""

def _render_item_list(title: str,
                      items: List[Dict[str, Any]] | None,
                      showSources: bool = False) -> str:
  if not items:
    return ""
  # Sort alphabetically by item name for readability
  sortedItems = sorted(
    (i for i in items if i.get("name")),
    key=lambda i: i["name"].lower()
  )
  rows: list[str] = []
  for itm in sortedItems:
    # Skip tooltip tradeskill container objects
    if itm.get("id") is not None and itm["id"] < 54:
      itemName = html.escape(itm["name"])
    else:
      itemName = (
        f"<span class='eqtooltip' data-type='item' data-id='{itm.get('id')}'>"
        f"{html.escape(itm['name'])}</span>"
      )
    qty = itm.get("quantity", 0) or 0
    qtyPrefix = f"{qty} × " if qty else ""
    icons = _get_source_icons(itm) if showSources else ""
    rows.append(f"<li>{qtyPrefix}{itemName}{icons}</li>")
  return (
    f"<div class='recipe-subsection'>"
    f"<b>{html.escape(title)}:</b>"
    "<ul class='recipe-list'>" + "".join(rows) + "</ul></div>"
  )

def render_recipe_list(recipes: List[Dict[str, Any]],
                       characterSkill: Optional[int] = None) -> str:
  """Render the tradeskill *recipe block* as HTML.

  This matches the two-column layout (Ingredients/Makes on the left,
  Combine/Returns on the right) with support for multiple variants of the
  same recipe name grouped together.
  """
  if not recipes:
    return ""

  # Group by recipe name
  grouped: dict[str, list[Dict[str, Any]]] = {}
  for recipe in recipes:
    grouped.setdefault(recipe.get("name", "Unnamed Recipe"), []).append(recipe)

  html_parts: list[str] = []

  for recipeName, variants in grouped.items():
    html_parts.append(
      f"<div class='recipe-block'><h4 class='recipe-title'>{html.escape(recipeName)}</h4><div class='recipe-section'>"
    )

    for variant in variants:
      variantColor = _get_trivial_color_class(characterSkill, variant.get("trivial", 0))

      html_parts.append("<div class='recipe-variant'>")
      html_parts.append(
        f"<div class='trivial {variantColor}'>Trivial: {variant.get('trivial', '')}</div>"
      )
      html_parts.append("<div class='recipe-columns'>")

      # Left column
      html_parts.append("<div class='recipe-left-column'>")
      html_parts.append(_render_item_list('Ingredients', variant.get("ingredients", []), showSources=True))
      html_parts.append(_render_item_list('Makes', variant.get("outputs", [])))
      html_parts.append("</div>")

      # Right column
      html_parts.append("<div class='recipe-right-column'>")
      html_parts.append(_render_item_list('Combine In',          variant.get("containers", [])))
      html_parts.append(_render_item_list('Always Returned',     variant.get("returnedAlways", [])))
      html_parts.append(_render_item_list('Returned on Failure', variant.get("returnedOnFailure", [])))
      html_parts.append(_render_item_list('Returned on Success', variant.get("returnedOnSuccess", [])))
      html_parts.append("</div>")  # /.recipe-right-column

      html_parts.append("</div>")  # /.recipe-columns
      html_parts.append("</div>")  # /.recipe-variant

    html_parts.append("</div></div>")  # /.recipe-section + /.recipe-block

  out = "\n".join(html_parts)
  logger.debug("Rendered %d recipe group(s)", len(grouped))
  return out
