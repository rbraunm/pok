from __future__ import annotations

import html
from typing import Any, Dict, Optional
from applogging import get_logger

logger = get_logger(__name__)

def _esc(v: Any) -> str:
  return html.escape("" if v is None else str(v))

def _pill(s: Optional[str]) -> str:
  return f"<span class='pill'>{_esc(s)}</span>" if s else ""

def render_item_header(item: Dict[str, Any]) -> str:
  """Compact item header (name + a few pills). Purely presentational."""
  if not item:
    return "<div class='item-detail'><p>Item not found.</p></div>"

  item_id = item.get("id")
  name = item.get("Name") or item.get("name") or f"Item #{item_id}"
  req = item.get("requiredlevel") or item.get("required_level") or item.get("req_level")
  rec = item.get("recommendedlevel") or item.get("recommended_level")

  pills = []
  if req is not None: pills.append(f"Req {int(req)}")
  if rec is not None: pills.append(f"Rec {int(rec)}")

  # Spell bits if present
  sbits = []
  if item.get("focusname"): sbits.append(f"Focus: {_esc(item['focusname'])}")
  if item.get("procname"):  sbits.append(f"Proc: {_esc(item['procname'])}")
  if item.get("clickname"): sbits.append(f"Click: {_esc(item['clickname'])}")

  return (
    "<div class='item-detail'>"
    f"  <div class='id-header'>"
    f"    <span class='name eqtooltip' data-type='item' data-id='{_esc(item_id)}'>{_esc(name)}</span>"
    f"    <span class='pills'>{' '.join(_pill(p) for p in pills)}</span>"
    f"  </div>"
    f"  {('<div class=\"subline\">' + ' | '.join(sbits) + '</div>') if sbits else ''}"
    "</div>"
  )
