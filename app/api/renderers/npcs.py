from __future__ import annotations

import html
from typing import List, Dict, Any, Optional
from applogging import get_logger

logger = get_logger(__name__)

# ---------- helpers ----------
def esc(s: Any) -> str:
  return html.escape("" if s is None else str(s))

def _to_num(v) -> Optional[float]:
  try:
    if v is None or v == "" or (isinstance(v, float) and (v != v)):  # NaN
      return None
    return float(v)
  except Exception:
    return None

def _fmt01(n) -> str:
  n = _to_num(n)
  return "" if n is None else f"{n:.1f}"

def format_respawn_time(seconds_maybe) -> str:
  s = int(_to_num(seconds_maybe) or 0)
  m, sec = divmod(s, 60)
  return f"{m}m {sec}s"

def format_price(copper) -> str:
  c = int(_to_num(copper) or 0)
  pp, rem = divmod(c, 1000)
  gp, rem = divmod(rem, 100)
  sp, cp = divmod(rem, 10)
  parts = []
  if pp: parts.append(f"{pp}pp")
  if gp: parts.append(f"{gp}gp")
  if sp: parts.append(f"{sp}sp")
  if cp or not parts: parts.append(f"{cp}cp")
  return " ".join(parts)

def format_chance(row: Dict[str, Any]) -> str:
  mult = int(_to_num(row.get("drop_multiplier")) or 1)
  ch = float(_to_num(row.get("drop_chance")) or 0.0)
  return f"{mult} × {ch:.2f}%"

# ---------- renderers ----------
def render_item_drops(drops: List[Dict[str, Any]]) -> str:
  """Server-side HTML renderer for item *drops* (by NPC & spawnpoint).
  Accepts the structure returned by api.models.npcs.get_item_drops().
  """
  if not drops:
    return "<div class='empty'>No drop data.</div>"

  # Group by zone header to match client-side layout
  zones: dict[str, list[tuple[Dict[str, Any], str]]] = {}
  for row in drops:
    zones_obj = (row.get("zones") or {})
    for zone_short, zdata in zones_obj.items():
      header = f"{zdata.get('zone_longname') or zone_short} ({zone_short})"
      zones.setdefault(header, []).append((row, zone_short))

  parts: list[str] = []
  for zone_header, entries in zones.items():
    parts.append(f"<div class='zone-block'><div class='zone-title'>{esc(zone_header)}</div><ul class='drop-list'>")
    for row, zone_short in entries:
      npc = row.get("npc") or {}
      lvl_lo = _to_num(npc.get("level"))
      lvl_hi = _to_num(npc.get("maxlevel"))
      if lvl_lo is not None and lvl_hi is not None and int(lvl_lo) != int(lvl_hi):
        lvl_text = f"Lvl {int(lvl_lo)} – {int(lvl_hi)}"
      else:
        lvl_text = f"Lvl {int(lvl_lo or lvl_hi or 0)}"

      zone = (row.get("zones") or {}).get(zone_short) or {"spawnpoints": []}
      label = format_chance(row)

      npc_id = _to_num(npc.get("id"))
      name_inner = esc(npc.get("name") or "Unknown")
      if npc_id is not None:
        npc_html = f"<span class='npc-name eqtooltip' data-type='npc' data-id='{int(npc_id)}'>{name_inner}</span>"
      else:
        npc_html = f"<span class='npc-name'>{name_inner}</span>"

      parts.append(f"<li class='drop-npc'>")
      parts.append(f"  <div class='drop-npc-head'>{npc_html} <span class='npc-level'>({esc(lvl_text)})</span> <span class='npc-drop'>{esc(label)}</span></div>")
      parts.append("  <ul class='spawn-list'>")

      for sp in (zone.get("spawnpoints") or []):
        cy = _to_num(sp.get("y") if sp.get("y") is not None else sp.get("loc_y"))
        cx = _to_num(sp.get("x") if sp.get("x") is not None else sp.get("loc_x"))
        cz = _to_num(sp.get("z") if sp.get("z") is not None else sp.get("loc_z"))
        coords = f"({_fmt01(cy)}, {_fmt01(cx)}{(', ' + _fmt01(cz)) if cz is not None else ''})"

        respawn_secs = int(_to_num(sp.get("respawntime")) or 0)
        point_ch = sp.get("chance")
        point_ch_text = f"{float(point_ch):.0f}%" if point_ch is not None else ""

        ph_title = ""
        ph_list = sp.get("ph") or []
        if isinstance(ph_list, list) and ph_list:
          bits = []
          for p in ph_list:
            try:
              n = p.get("name")
            except Exception:
              n = None
            ch = p.get("chance")
            if n:
              bits.append(f"{n} ({float(ch or 0):.0f}%)")
          if bits:
            ph_title = f" title=\"PH: {esc(', '.join(bits))}\""
        elif sp.get("placeholders"):
          ph_title = f" title=\"PH: {esc(str(sp.get('placeholders')))}\""

        parts.append(
          "  <li class='spawn' data-loc-y='{y}' data-loc-x='{x}' data-loc-z='{z}'>"
          f"<span class='coords'>{esc(coords)}</span>"
          " <span class='sep'> — </span>"
          f"<span class='respawn'>{esc(format_respawn_time(respawn_secs))}</span>"
          f"{(' <span class=\'point-chance\'' + ph_title + f'>({esc(point_ch_text)})</span>') if point_ch_text else ''}"
          "</li>"
          .format(y=esc(cy if cy is not None else ''), x=esc(cx if cx is not None else ''), z=esc(cz if cz is not None else ''))
        )
      parts.append("  </ul>")
      parts.append("</li>")
    parts.append("</ul></div>")
  return "".join(parts)

def render_item_merchants(rows: List[Dict[str, Any]]) -> str:
  """Server-side HTML renderer for item *merchants* where it's sold."""
  if not rows:
    return "<div class='empty'>Not sold by merchants.</div>"

  out: list[str] = ["<ul class='merchant-list'>"]
  for r in rows:
    z_long = r.get('zone_longname') or r.get('zone')
    cy = _to_num(r.get('y') if r.get('y') is not None else r.get('loc_y'))
    cx = _to_num(r.get('x') if r.get('x') is not None else r.get('loc_x'))
    cz = _to_num(r.get('z') if r.get('z') is not None else r.get('loc_z'))
    coords = f" ({_fmt01(cy)}, {_fmt01(cx)}{(', ' + _fmt01(cz)) if cz is not None else ''})" if (cy is not None or cx is not None or cz is not None) else ""

    merch_id = _to_num(r.get('npcId') or r.get('npc_id') or r.get('id'))
    merch_name_inner = esc(r.get('Name') or r.get('npc_name') or 'Merchant')
    if merch_id is not None:
      merch_html = f"<span class='merchant-name eqtooltip' data-type='npc' data-id='{int(merch_id)}'>{merch_name_inner}</span>"
    else:
      merch_html = f"<span class='merchant-name'>{merch_name_inner}</span>"

    chance = f" — {float(r.get('chance') or 0):.0f}%" if r.get('chance') is not None else ""
    respawn = f" — {format_respawn_time(r.get('respawntime'))}" if r.get('respawntime') is not None else ""
    price = f" @ {esc(format_price(r.get('price')))}" if r.get('price') is not None else ""

    out.append(
      f"<li class='merchant-row'>{merch_html}{(' — ' + esc(z_long)) if z_long else ''}{coords}{chance}{respawn}{price}</li>"
    )
  out.append("</ul>")
  return "".join(out)
