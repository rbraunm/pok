from __future__ import annotations

from typing import Any, Dict, List, Tuple
import pymysql.cursors
from api.db import getDb
from api.models.npcs import get_npc_spawnpoints
from api.models.characters import CLASS_BITMASK, RACE_BITMASK

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
  0:  (1 << 0,  "Charm"),
  1:  (1 << 1,  "Ear"),
  2:  (1 << 2,  "Head"),
  3:  (1 << 3,  "Face"),
  # Ear 2
  5:  (1 << 5,  "Neck"),
  6:  (1 << 6, "Shoulders"),
  7:  (1 << 7,  "Arms"),
  8:  (1 << 8,  "Back"),
  9:  (1 << 9,  "Wrist"),
  # Wrist 2
  11:  (1 << 11, "Range"),
  12:  (1 << 12, "Hands"),
  13:  (1 << 13, "Primary"),
  14:  (1 << 14, "Secondary"),
  15:  (1 << 15, "Finger"),
  # Finger 2
  17:  (1 << 17, "Chest"),
  18:  (1 << 18, "Legs"),
  19:  (1 << 19, "Feet"),
  20:  (1 << 20, "Waist"),
  21:  (1 << 21, "PowerSource"),
  22:  (1 << 22, "Ammo"),
}

SLOT_OPTIONS = [(str(idx), name) for idx, (_, name) in SLOT_BITMASKS.items()]
SORTABLE_FIELDS = {"name": "i.Name", **NUMERIC_ATTR_MAP}
CMP_OPS = {">=", "<=", "="}

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

  aggregated = {}

  for npc in npcDrops:
    npcSpawnData = get_npc_spawnpoints(npc['npc_id'])
    if not npcSpawnData or not npcSpawnData.get('zones'):
      continue

    npcInfo = {k: v for k, v in npcSpawnData.items() if k != 'zones'}
    zones = npcSpawnData['zones']

    for zoneShort, zoneData in zones.items():
      key = (npcInfo['name'], npc['effective_chance'], zoneShort)

      if key not in aggregated:
        aggregated[key] = {
          'npc': {
            'name': npcInfo['name'],
            'lastname': npcInfo.get('lastname'),
            'race': npcInfo.get('race'),
            'class': npcInfo.get('class'),
            'bodytype': npcInfo.get('bodytype'),
            'runspeed': npcInfo.get('runspeed'),
            'level': npcInfo.get('level'),
            'maxlevel': npcInfo.get('level')  # Initial max same as current level
          },
          'effective_chance': npc['effective_chance'],
          'zones': {
            zoneShort: {
              'zone_longname': zoneData['zone_longname'],
              'spawnpoints': list(zoneData['spawnpoints'])
            }
          }
        }
      else:
        existing = aggregated[key]
        existing['npc']['level'] = min(existing['npc']['level'], npcInfo['level'])
        existing['npc']['maxlevel'] = max(existing['npc']['maxlevel'], npcInfo['level'])

        if zoneShort not in existing['zones']:
          existing['zones'][zoneShort] = {
            'zone_longname': zoneData['zone_longname'],
            'spawnpoints': list(zoneData['spawnpoints'])
          }
        else:
          existing['zones'][zoneShort]['spawnpoints'].extend(zoneData['spawnpoints'])

  return list(aggregated.values())

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
