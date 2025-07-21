from __future__ import annotations

from typing import Any, Dict, List, Tuple
import pymysql.cursors
from api.db import getDb
from api.models.npcs import get_npc_spawnpoints

NUMERIC_ATTR_MAP: Dict[str, str] = {
  "str": "i.astr",
  "sta": "i.asta",
  "dex": "i.adex",
  "agi": "i.aagi",
  "int": "i.aint",
  "wis": "i.awis",
  "cha": "i.acha",
  "ac": "i.ac",
  "hp": "i.hp",
  "mana": "i.mana",
  "endur": "i.endur",
  "attack": "i.attack",
  "damage": "i.damage",
  "delay": "i.delay",
  "haste": "i.haste",
  "mr": "i.mr",
  "fr": "i.fr",
  "cr": "i.cr",
  "dr": "i.dr",
  "pr": "i.pr",
}

ITEM_SOURCE_OPTIONS: Dict[str, int] = {
  "drop": 1,
  "tradeskill": 2,
  "merchant": 3,
}

BOOL_FLAG_MAP: Dict[str, str] = {
  "artifact": "i.artifactflag",
  "aug": "i.augslot1type",
  "attuneable": "i.attuneable",
  "quest": "i.questitemflag",
  "tradeskill": "i.tradeskills",
  "heirloom": "i.heirloom",
  "lore": "i.loregroup",
  "noTrade": "i.nodrop",
}

SLOT_BITMASKS: Dict[int, Tuple[int, str]] = {
  7:  (1 << 2,  "Head"),
  8:  (1 << 17, "Chest"),
  9:  (1 << 7,  "Arms"),
  10: (1 << 9,  "Wrist"),
  11: (1 << 12, "Hands"),
  12: (1 << 18, "Legs"),
  13: (1 << 19, "Feet"),
  14: (1 << 8,  "Back"),
  30: (1 << 21, "Primary"),
  31: (1 << 22, "Secondary"),
  3:  (1 << 1,  "Ear"),
  4:  (1 << 15, "Finger"),
  5:  (1 << 5,  "Neck"),
  2:  (1 << 11, "Range"),
}

SLOT_OPTIONS = [(str(idx), name) for idx, (_, name) in SLOT_BITMASKS.items()]
SORTABLE_FIELDS = {"name": "i.Name", **NUMERIC_ATTR_MAP}
CMP_OPS = {">=", "<=", "="}

CLASS_BITMASK = {
  "Warrior":       1 << 0,
  "Cleric":        1 << 1,
  "Paladin":       1 << 2,
  "Ranger":        1 << 3,
  "Shadow Knight": 1 << 4,
  "Druid":         1 << 5,
  "Monk":          1 << 6,
  "Bard":          1 << 7,
  "Rogue":         1 << 8,
  "Shaman":        1 << 9,
  "Necromancer":   1 << 10,
  "Wizard":        1 << 11,
  "Magician":      1 << 12,
  "Enchanter":     1 << 13,
  "Beastlord":     1 << 14,
  "Berserker":     1 << 15
}

RACE_BITMASK = {
  "Human":     1 << 0,
  "Barbarian": 1 << 1,
  "Erudite":   1 << 2,
  "Wood Elf":  1 << 3,
  "High Elf":  1 << 4,
  "Dark Elf":  1 << 5,
  "Half Elf":  1 << 6,
  "Dwarf":     1 << 7,
  "Troll":     1 << 8,
  "Ogre":      1 << 9,
  "Halfling":  1 << 10,
  "Gnome":     1 << 11,
  "Iksar":     1 << 12,
  "Vah Shir":  1 << 13,
  "Froglok":   1 << 14
}

ITEM_TABLE_SELECT_FIELDS = """
      i.id,
      i.Name,
      i.astr as str,
      i.asta as sta,
      i.adex as dex,
      i.aagi as agi,
      i.aint as `int`,
      i.awis as wis,
      i.acha as cha,
      i.ac,
      i.hp,
      i.mana,
      i.endur,
      i.attack,
      i.damage,
      i.delay,
      i.haste,
      i.mr,
      i.fr,
      i.cr,
      i.dr,
      i.pr,
      i.accuracy,
      i.avoidance,
      i.bagsize,
      i.bagslots,
      i.bagtype,
      i.bagwr,
      i.classes,
      i.combateffects,
      i.extradmgskill,
      i.extradmgamt,
      i.price,
      i.damageshield,
      i.deity,
      i.augdistiller,
      i.dotshielding,
      i.clicktype,
      i.clicklevel2,
      i.elemdmgtype,
      i.elemdmgamt,
      i.focuseffect,
      i.clicklevel,
      i.regen,
      i.icon,
      i.idfile,
      i.itemclass,
      i.itemtype,
      i.ldonprice,
      i.ldontheme,
      i.ldonsold,
      i.light,
      i.loregroup,
      i.magic,
      i.manaregen,
      i.enduranceregen,
      i.material,
      i.maxcharges,
      i.nodrop,
      i.norent,
      i.pendingloreflag,
      i.procrate,
      i.races,
      i.range,
      i.reclevel,
      i.recskill,
      i.reqlevel,
      i.sellrate,
      i.shielding,
      i.size,
      i.skillmodtype,
      i.skillmodvalue,
      i.slots,
      i.clickeffect,
      i.spellshield,
      i.strikethrough,
      i.stunresist,
      i.summonedflag,
      i.tradeskills,
      i.favor,
      i.weight,
      i.benefitflag,
      i.booktype,
      i.recastdelay,
      i.recasttype,
      i.guildfavor,
      i.attuneable,
      i.nopet,
      i.comment,
      i.pointtype,
      i.potionbelt,
      i.potionbeltslots,
      i.stacksize,
      i.notransfer,
      i.stackable,
      i.proceffect,
      i.proctype,
      i.proclevel2,
      i.proclevel,
      i.worneffect,
      i.worntype,
      i.wornlevel2,
      i.wornlevel,
      i.focustype,
      i.focuslevel2,
      i.focuslevel,
      i.scrolleffect,
      i.scrolltype,
      i.scrolllevel2,
      i.scrolllevel,
      i.serialized,
      i.serialization,
      i.lorefile,
      i.skillmodmax,
      i.clickname,
      i.procname,
      i.wornname,
      i.focusname,
      i.scrollname,
      i.healamt,
      i.spelldmg,
      i.clairvoyance,
      i.backstabdmg,
      i.elitematerial,
      i.ldonsellbackrate,
      i.scriptfileid,
      i.expendablearrow,
      i.powersourcecapacity,
      i.bardeffect,
      i.bardeffecttype,
      i.bardlevel2,
      i.bardlevel,
      i.bardname,
      i.subtype,
      i.heirloom,
      i.placeable,
      i.epicitem"""

class ItemNotFoundError(Exception):
  pass

def decodeBitmask(value, mapping):
  return [name for name, mask in mapping.items() if value & mask] if value else []

def search_items_filtered(
  *,
  nameQuery: str = "",
  slots: List[str] | None = None,
  classMask: int | None = None,
  raceMask: int | None = None,
  minLevel: int | None = None,
  maxLevel: int | None = None,
  minRecLevel: int | None = None,
  maxRecLevel: int | None = None,
  attrFilters: List[Tuple[str, str, int]] | None = None,
  boolFilters: Dict[str, str] | None = None,
  augmentOption: str = "both",
  equippableOnly: bool = False,
  itemSourceFilters: List[str] | None = None,
  limit: int = 25,
  offset: int = 0,
  sortField: str = "i.Name",
  sortOrder: str = "asc"
) -> Dict[str, Any]:
  where, params = [], []

  if nameQuery:
    where.append("i.Name LIKE %s")
    params.append(f"%{nameQuery}%")

  if slots:
    mask = sum(SLOT_BITMASKS[int(s)][0] for s in slots if s.isdigit() and int(s) in SLOT_BITMASKS)
    where.append("(i.slots & %s) <> 0")
    params.append(mask)

  if classMask is not None:
    where.append("(i.classes & %s) <> 0")
    params.append(classMask)

  if raceMask is not None:
    where.append("(i.races & %s) <> 0")
    params.append(raceMask)

  if minLevel is not None:
    where.append("i.reqlevel >= %s")
    params.append(minLevel)

  if maxLevel is not None:
    where.append("i.reqlevel <= %s")
    params.append(maxLevel)

  if minRecLevel is not None:
    where.append("i.reclevel >= %s")
    params.append(minRecLevel)

  if maxRecLevel is not None:
    where.append("i.reclevel <= %s")
    params.append(maxRecLevel)

  for attr, cmp_op, val in (attrFilters or []):
    col = NUMERIC_ATTR_MAP.get(attr)
    if col and cmp_op in CMP_OPS:
      where.append(f"{col} {cmp_op} %s")
      params.append(val)

  if boolFilters:
    for key, val in boolFilters.items():
      col = BOOL_FLAG_MAP.get(key)
      if col:
        clause = f"{col} {'!=' if val == 'true' else '='} 0"
        where.append(clause)

  if augmentOption == "only":
    where.append("i.itemtype = 54")
  elif augmentOption == "exclude":
    where.append("i.itemtype <> 54")

  if equippableOnly:
    where.append("i.slots > 0")

  if itemSourceFilters:
    sourceConditions = []
    if "drop" in itemSourceFilters:
      sourceConditions.append("pis.lootdropEntries IS NOT NULL")
    if "merchant" in itemSourceFilters:
      sourceConditions.append("pis.merchantListEntries IS NOT NULL")
    if "tradeskill" in itemSourceFilters:
      sourceConditions.append("pis.tradeskillRecipeEntries IS NOT NULL")
    if sourceConditions:
      where.append("(" + " OR ".join(sourceConditions) + ")")

  whereClause = " AND ".join(where) if where else "1=1"

  dataSql = f"""
    SELECT {ITEM_TABLE_SELECT_FIELDS},
      pis.*,
      CASE
        WHEN pis.item_id IS NULL
          OR (pis.lootdropEntries IS NULL AND pis.merchantListEntries IS NULL
            AND pis.tradeskillRecipeEntries IS NULL AND pis.questEntries IS NULL)
        THEN 1 ELSE 0
      END AS unobtainable
    FROM items i
    LEFT JOIN pok_item_sources pis ON i.id = pis.item_id
    WHERE {whereClause}
    ORDER BY {sortField} {sortOrder}
    LIMIT %s OFFSET %s
  """

  countSql = f"""
    SELECT COUNT(*)
    FROM items i
    LEFT JOIN pok_item_sources pis ON i.id = pis.item_id
    WHERE {whereClause}
  """

  db = getDb()
  with db.cursor(pymysql.cursors.DictCursor) as cur:
    # Run data query
    dataParams = params + [limit, offset]
    cur.execute(dataSql, dataParams)
    items = cur.fetchall()

    # Run count query
    cur.execute(countSql, params)
    total = cur.fetchone()["COUNT(*)"]

  return {"items": items, "total": total}

def get_item(itemId: int) -> Dict[str, Any]:
  db = getDb()
  with db.cursor(pymysql.cursors.DictCursor) as cur:
    cur.execute(f"""
      SELECT {ITEM_TABLE_SELECT_FIELDS},
        pis.*,
        CASE
          WHEN pis.lootdropEntries IS NULL AND 
               pis.merchantListEntries IS NULL AND
               pis.tradeskillRecipeEntries IS NULL AND
               pis.questEntries IS NULL
          THEN 1 ELSE 0
        END AS unobtainable
      FROM items i
      LEFT JOIN pok_item_sources pis ON i.id = pis.item_id
      WHERE i.id = %s
    """, (itemId,))
    item = cur.fetchone()
    if not item:
      raise ItemNotFoundError(f"Item with ID {itemId} not found.")
  return item

def get_item_drops(itemId: int) -> List[Dict[str, Any]]:
  sql = """
    SELECT
      nt.id AS npc_id,
      lde.item_id,
      lde.chance AS base_chance,
      ROUND(le.multiplier, 2) AS multiplier,
      ROUND(lde.chance * le.multiplier, 2) AS effective_chance
    FROM lootdrop_entries lde
    JOIN loottable_entries le ON lde.lootdrop_id = le.lootdrop_id
    JOIN loottable lt ON le.loottable_id = lt.id
    JOIN npc_types nt ON lt.id = nt.loottable_id
    WHERE lde.item_id = %s
    GROUP BY nt.id
    ORDER BY effective_chance DESC
  """

  db = getDb()
  with db.cursor(pymysql.cursors.DictCursor) as cur:
    cur.execute(sql, (itemId,))
    npcDrops = cur.fetchall()

  validNpcDrops = []

  for npc in npcDrops:
    npcSpawnData = get_npc_spawnpoints(npc['npc_id'])
    if not npcSpawnData or not npcSpawnData.get('zones'):
      continue

    npc['npc'] = {k: v for k, v in npcSpawnData.items() if k != 'zones'}
    npc['zones'] = npcSpawnData['zones']
    validNpcDrops.append(npc)

  return validNpcDrops

def get_item_merchants(itemId: int) -> List[int]:
  db = getDb()
  with db.cursor() as cur:
    cur.execute("""
      SELECT merchantListEntries
      FROM pok_item_sources
      WHERE item_id = %s
    """, (itemId,))
    row = cur.fetchone()

  if not row or not row[0]:
    return []

  return [int(mid) for mid in row[0].split(',')]

def get_item_recipes(itemId: int) -> List[int]:
  db = getDb()
  with db.cursor() as cur:
    cur.execute("""
      SELECT tradeskillRecipeEntries
      FROM pok_item_sources
      WHERE item_id = %s
    """, (itemId,))
    row = cur.fetchone()

  if not row or not row[0]:
    return []

  return [int(rid) for rid in row[0].split(',')]

__all__ = [
  "get_item",
  "search_items_filtered",
  "get_item_drops",
  "get_item_merchants",
  "get_item_recipes",
  "decodeBitmask",
  "NUMERIC_ATTR_MAP",
  "BOOL_FLAG_MAP",
  "SLOT_OPTIONS",
  "SLOT_BITMASKS",
  "SORTABLE_FIELDS",
  "CLASS_BITMASK",
  "RACE_BITMASK",
  "ITEM_SOURCE_OPTIONS"
]
