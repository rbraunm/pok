"""
api/models/items.py

Item search utilities used by Gear Scout and Drop Locator.
Fully self-contained: import only `getDb` from api.__init__.
"""

from __future__ import annotations

from typing import Any, Dict, List, Tuple
import os
import pymysql.cursors
from api import getDb

POK_DEBUG = os.getenv("POK_DEBUG", "false").lower() == "true"

# --------------------------------------------------------------------------- #
# Column maps & constants
# --------------------------------------------------------------------------- #

NUMERIC_ATTR_MAP: Dict[str, str] = {
  # —— primary stats / combat ——
  "ac":        "i.ac",
  "hp":        "i.hp",
  "mana":      "i.mana",
  "endurance": "i.endur",
  "attack":    "i.attack",
  "damage":    "i.damage",
  "delay":     "i.delay",
  "haste":     "i.haste",
  # —— character attributes ——
  "str":  "i.astr",
  "sta":  "i.asta",
  "dex":  "i.adex",
  "agi":  "i.aagi",
  "int":  "i.aint",
  "wis":  "i.awis",
  "cha":  "i.acha",
  # —— resists ——
  "mr":  "i.mr",
  "fr":  "i.fr",
  "cr":  "i.cr",
  "dr":  "i.dr",
  "pr":  "i.pr",
}

BOOL_FLAG_MAP: Dict[str, str] = {
  "artifact":   "i.artifactflag",
  "aug":        "i.augslot1type",
  "attuneable": "i.attuneable",
  "quest":      "i.questitemflag",
  "tradeskill": "i.tradeskills",
  "heirloom":   "i.heirloom",
  "lore":       "i.loregroup",
  "noTrade":    "i.nodrop",
}

# EQEmu slot-index → (bitmask, label)
SLOT_BITMASKS: Dict[int, Tuple[int, str]] = {
   7: (1 << 2,  "Head"),
   8: (1 << 17, "Chest"),
   9: (1 << 7,  "Arms"),
  10: (1 << 9,  "Wrist"),
  11: (1 << 12, "Hands"),
  12: (1 << 18, "Legs"),
  13: (1 << 19, "Feet"),
  14: (1 << 8,  "Back"),
  30: (1 << 21, "Primary"),
  31: (1 << 22, "Secondary"),
   3: (1 << 1,  "Ear"),
   4: (1 << 15, "Finger"),
   5: (1 << 5,  "Neck"),
   2: (1 << 11, "Range"),
}

SLOT_OPTIONS: List[Tuple[str, str]] = [
  (str(idx), name) for idx, (_, name) in SLOT_BITMASKS.items()
]

# All sortable fields Gear Scout exposes → actual SQL column
SORTABLE_FIELDS: Dict[str, str] = {
  "name":   "i.Name",
  **NUMERIC_ATTR_MAP,         # ac, hp, mana, …
}

CMP_OPS = {">=", "<=", "="}

# --------------------------------------------------------------------------- #
# Exceptions
# --------------------------------------------------------------------------- #

class ItemNotFoundError(Exception):
  """Raised when an item ID does not exist."""


# --------------------------------------------------------------------------- #
# Public helpers
# --------------------------------------------------------------------------- #

def get_item(itemId: int) -> Dict[str, Any]:
  if not isinstance(itemId, int) or itemId <= 0:
    raise ValueError(f"Invalid item ID: {itemId}")

  db = getDb()
  with db.cursor(pymysql.cursors.DictCursor) as cur:
    cur.execute("SELECT * FROM items WHERE id = %s", (itemId,))
    row = cur.fetchone()

  if not row:
    raise ItemNotFoundError(f"Item not found: {itemId}")

  return row


def search_items_filtered(
  *,
  nameQuery: str = "",
  slots: List[str] | None = None,
  itemType: str = "",
  classMask: int | None = None,
  raceMask: int | None = None,
  minLevel: int | None = None,
  maxLevel: int | None = None,
  attrFilters: List[Tuple[str, str, int]] | None = None,
  boolFilters: Dict[str, str] | None = None,
  minDelay: int | None = None,
  maxDelay: int | None = None,
  minRatio: float | None = None,
  maxRatio: float | None = None,
  equippableOnly: bool = False,
  limit: int = 50,
  offset: int = 0,
  sortField: str = "i.Name",
  sortOrder: str = "asc"
) -> Dict[str, Any]:
  """
  Search items with rich filters **and** pagination.

  Returns
  -------
  {"items": [row, …], "total": int}
  """
  where: List[str] = []
  params: List[Any] = []

  # ---------------------------------------------------- text search / slots
  if nameQuery:
    where.append("i.Name LIKE %s")
    params.append(f"%{nameQuery}%")

  if slots:
    mask = 0
    for s in slots:
      if not s.isdigit():
        raise ValueError(f"Invalid slot index: {s}")
      idx = int(s)
      if idx not in SLOT_BITMASKS:
        raise ValueError(f"Unknown slot index for bitmask: {idx}")
      bitmask, _ = SLOT_BITMASKS[idx]
      mask |= bitmask
    where.append("(i.slots & %s) <> 0")
    params.append(mask)

  # ---------------------------------------------------- numeric attributes
  for attr, cmp_op, val in (attrFilters or []):
    if cmp_op not in CMP_OPS:
      raise ValueError(f"Invalid comparator: {cmp_op}")
    col = NUMERIC_ATTR_MAP.get(attr)
    if not col:
      raise ValueError(f"Unknown attribute: {attr}")
    where.append(f"{col} {cmp_op} %s")
    params.append(val)

  # ---------------------------------------------------- delay / ratio
  if minDelay is not None:
    where.append("i.delay >= %s"); params.append(minDelay)
  if maxDelay is not None:
    where.append("i.delay <= %s"); params.append(maxDelay)
  if minRatio is not None:
    where.append("(i.damage / NULLIF(i.delay,0)) >= %s"); params.append(minRatio)
  if maxRatio is not None:
    where.append("(i.damage / NULLIF(i.delay,0)) <= %s"); params.append(maxRatio)

  # ---------------------------------------------------- level / class / race
  if minLevel is not None:
    where.append("i.reqlevel >= %s"); params.append(minLevel)
  if maxLevel is not None:
    where.append("i.reqlevel <= %s"); params.append(maxLevel)
  if classMask is not None:
    where.append("(i.classes & %s) <> 0"); params.append(classMask)
  if raceMask is not None:
    where.append("(i.races & %s) <> 0"); params.append(raceMask)

  # ---------------------------------------------------- boolean flags
  for flag, value in (boolFilters or {}).items():
    col = BOOL_FLAG_MAP.get(flag)
    if not col:
      raise ValueError(f"Unknown boolean flag: {flag}")
    val = 1 if value else 0
    where.append(f"{col} = %s")
    params.append(val)

  if equippableOnly:
    where.append("i.slots <> 0")

  # ---------------------------------------------------- build & run query
  where_clause = " AND ".join(where) if where else "1=1"
  sort_col = SORTABLE_FIELDS.get(sortField.lower().lstrip("i."), "i.Name")
  sort_dir = "desc" if sortOrder.lower() == "desc" else "asc"

  sql = f"""
    SELECT SQL_CALC_FOUND_ROWS i.*
    FROM items i
    WHERE {where_clause}
    ORDER BY {sort_col} {sort_dir}
    LIMIT %s OFFSET %s
  """
  params.extend([limit, offset])

  if POK_DEBUG:
    print("ITEM SEARCH:", sql, params, flush=True)

  db = getDb()
  with db.cursor(pymysql.cursors.DictCursor) as cur:
    cur.execute(sql, params)
    items = cur.fetchall()
    cur.execute("SELECT FOUND_ROWS() AS total")
    total = cur.fetchone()["total"]

  return {"items": items, "total": total}


# --------------------------------------------------------------------------- #
# Legacy alias (back-compat)
# --------------------------------------------------------------------------- #

def search_items(*args, **kwargs):
  return search_items_filtered(*args, **kwargs)


__all__ = [
  "get_item",
  "search_items_filtered",
  "search_items",
  "NUMERIC_ATTR_MAP",
  "BOOL_FLAG_MAP",
  "SLOT_OPTIONS",
  "SLOT_BITMASKS",
  "SORTABLE_FIELDS",
  "ItemNotFoundError",
]
