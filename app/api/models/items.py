from __future__ import annotations

from typing import Any, Dict, List, Tuple
import pymysql.cursors
from db import getDb
from applogging import get_logger
logger = get_logger(__name__)

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
  "ratio": "(i.damage / NULLIF(i.delay, 0))"
}

# ToDo: add new item sources:
# 1) Purchased from standard merchants (coin)
#    Where: merchantlist.item (per-merchant, per-slot). Join items.id = merchantlist.item.
# 2) Ground spawns
#    Where: ground_spawns.item (per zone/coords). Simple lookup by item.
# 3) Foraged
#    Where: forage.Itemid (per zone). Join items.id = forage.Itemid.
# 4) Fished
#    Where: fishing.Itemid (per zone). Join items.id = fishing.Itemid.
# 5) Starting items (character creation)
#    Where: starting_items.itemid (keyed by race/class/deity/start zone).
# 6) Crafted via tradeskill combines
#    Where: tradeskill_recipe + tradeskill_recipe_entries.
#           Produced items appear in tradeskill_recipe_entries.item_id with successcount > 0.
# 7) Looted from NPCs (standard loot tables)
#    Where: npc_types.loottable_id → loottable_entries → lootdrop_entries.item_id.
# 8) Global loot (server/zone-wide rules)
#    Where: global_loot attaches extra loot; ultimately resolves to lootdrop_entries.item_id.
# 9) Chest / object-container loot (world/event chests)
#    Where: object_contents.itemid (contents) associated with object rows spawned in a zone/instance.
# 10) Purchased from alternate-currency merchants
#     Where: merchantlist.alt_currency_cost > 0; merchant’s currency via
#            npc_types.alt_currency_id ↔ alternate_currency.id.
# 11) Task / Mission rewards
#     Where: tasks.rewardid (single item) and/or tasks.rewardmethod pointing to reward lists.
# 12) Summoned by spells
#     Where: spells_new effect slots using SE_SummonItem / SE_SummonItemIntoBag; item IDs in effect base values.
# 13) Granted directly by quests/scripts (Perl/Lua)
#     Where: quest API (e.g., quest::summonitem / e.other:SummonItem()) — not a static DB table.
# 14) Script-created ground objects (quest-placed pickups)
#     Where: quest::creategroundobject(...); appears at runtime as object/object_contents entries.
# 15) Instance/expedition chest rewards
#     Where: same object/object_contents mechanics, spawned in instance contexts
#            (tie back via instance_list / zone version).
# 16) Pick Pocket
#     Where: runtime skill logic; no dedicated “pickpocket source” table (shows as inventory changes).
# 17) Begging
#     Where: runtime skill logic; no dedicated DB source (occasional coin/items).
# 18) Account claims / veteran rewards
#     Where: veteran_reward_templates.item_id and account_rewards; surfaced via /claim.

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

SIZES = ('Tiny', 'Small', 'Medium', 'Large', 'Giant', 'Massive', 'Colossal')

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
      i.wornname,
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
      ROUND(i.damage / NULLIF(i.delay, 0), 4) AS ratio,
      i.epicitem"""

class ItemNotFoundError(Exception):
  pass

def decodeBitmask(value, mapping):
  return [name for name, mask in mapping.items() if value & mask] if value else []

def get_spell_options_for(kind: str) -> List[Dict[str, Any]]:
  col_map = {"focus": "focuseffect", "click": "clickeffect", "proc": "proceffect", "bard": "bardeffect"}
  col = col_map.get(kind)
  if not col:
    return []

  sql = f"""
    SELECT DISTINCT i.{col} AS id, s.name
    FROM items i
    JOIN pok_item_sources pis ON pis.item_id = i.id
    JOIN spells_new s ON s.id = i.{col}
    WHERE i.{col} IS NOT NULL
      AND i.{col} > 0
      AND (pis.lootdropEntries IS NOT NULL
          OR pis.merchantListEntries IS NOT NULL
          OR pis.tradeskillRecipeEntries IS NOT NULL
          OR pis.questEntries IS NOT NULL)
    ORDER BY s.name ASC
  """
  db = getDb()
  with db.cursor(pymysql.cursors.DictCursor) as cur:
    cur.execute(sql)
    return cur.fetchall()

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
  attrFilters: List[Tuple[str, str, float]] | None = None,
  boolFilters: Dict[str, str] | None = None,
  augmentOption: str = "both",
  equippableOnly: bool = False,
  itemSourceFilters: List[str] | None = None,
  bardIds: List[int] | None = None,
  focusIds: List[int] | None = None,
  clickIds: List[int] | None = None,
  procIds:  List[int] | None = None,
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

  def add_in_list(col: str, values: List[int] | None):
    if values:
      placeholders = ",".join(["%s"] * len(values))
      where.append(f"i.{col} IN ({placeholders})")
      params.extend(values)

  add_in_list("focuseffect", focusIds)
  add_in_list("clickeffect", clickIds)
  add_in_list("proceffect",  procIds)
  add_in_list("bardeffect",  bardIds)

  whereClause = " AND ".join(where) if where else "1=1"

  dataSql = f"""
    SELECT 
      {ITEM_TABLE_SELECT_FIELDS},
      fs.name AS focusname,
      cs.name AS clickname,
      ps.name AS procname,
      bs.name AS bardspellname,
      pis.*,
      CASE
        WHEN pis.item_id IS NULL
          OR (pis.lootdropEntries IS NULL AND pis.merchantListEntries IS NULL
            AND pis.tradeskillRecipeEntries IS NULL AND pis.questEntries IS NULL)
        THEN 1 ELSE 0
      END AS unobtainable
    FROM items i
    LEFT JOIN pok_item_sources pis ON i.id = pis.item_id
    LEFT JOIN spells_new fs ON i.focuseffect = fs.id
    LEFT JOIN spells_new cs ON i.clickeffect = cs.id
    LEFT JOIN spells_new ps ON i.proceffect  = ps.id
    LEFT JOIN spells_new bs ON i.bardeffect  = bs.id
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
    cur.execute(dataSql, params + [limit, offset])
    items = cur.fetchall()
    cur.execute(countSql, params)
    total = cur.fetchone()["COUNT(*)"]

  return {"items": items, "total": total}

def get_item(itemId: int) -> Dict[str, Any]:
  db = getDb()
  with db.cursor(pymysql.cursors.DictCursor) as cur:
    cur.execute(f"""
      SELECT 
        {ITEM_TABLE_SELECT_FIELDS},
        fs.name as focusname,
        cs.name as clickname,
        ps.name as procname,
      bs.name as bardspellname,
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
      LEFT JOIN spells_new fs ON i.focuseffect = fs.id
      LEFT JOIN spells_new cs ON i.clickeffect = cs.id
      LEFT JOIN spells_new ps ON i.proceffect = ps.id
      LEFT JOIN spells_new bs ON i.bardeffect = bs.id
      WHERE i.id = %s
    """, (itemId,))
    item = cur.fetchone()
    if not item:
      raise ItemNotFoundError(f"Item with ID {itemId} not found.")
  return item
