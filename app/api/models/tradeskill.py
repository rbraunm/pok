from typing import Dict, List
from db import getDb, DB_PREFIX
from api.models.eqemu import get_current_expansion
from applogging import get_logger
logger = get_logger(__name__)

TRADESKILL = {
  55: "Fishing",
  56: "Make Poison",
  57: "Tinkering",
  58: "Research",
  59: "Alchemy",
  60: "Baking",
  61: "Tailoring",
  63: "Blacksmithing",
  64: "Fletching",
  65: "Brewing",
  68: "Jewelry Making",
  69: "Pottery"
}

RECIPE_TABLE_SELECT_FIELDS = """
  tr.id,
  tr.name,
  tr.tradeskill,
  tr.skillneeded,
  tr.trivial,
  tr.enabled,
  tr.min_expansion,
  tr.max_expansion
  """

TRADESKILL_OBJECT_TABLE = """
  WITH container_map AS (
    SELECT 10 AS object_type_id, 'Tool Box' AS object_type_name
    UNION ALL SELECT 11, 'Research'
    UNION ALL SELECT 12, 'Mortar'
    UNION ALL SELECT 13, 'Self Dusting'
    UNION ALL SELECT 14, 'Oven'
    UNION ALL SELECT 15, 'Oven'
    UNION ALL SELECT 16, 'Loom'
    UNION ALL SELECT 17, 'Forge'
    UNION ALL SELECT 18, 'Fletching'
    UNION ALL SELECT 19, 'Brew Barrel'
    UNION ALL SELECT 20, 'Jewelcraft'
    UNION ALL SELECT 21, 'Pottery Wheel'
    UNION ALL SELECT 22, 'Pottery Kiln'
    UNION ALL SELECT 24, 'Wiz only combine container'
    UNION ALL SELECT 25, 'Mage only'
    UNION ALL SELECT 26, 'Necro only'
    UNION ALL SELECT 27, 'Ench Only'
    UNION ALL SELECT 28, 'Invalid or Class/Race limited'
    UNION ALL SELECT 29, 'Invalid or Class/Race limited'
    UNION ALL SELECT 30, 'Always Works'
    UNION ALL SELECT 31, 'High Elves Forge'
    UNION ALL SELECT 32, 'Dark Elves Forge'
    UNION ALL SELECT 33, 'Ogre Forge'
    UNION ALL SELECT 34, 'Dwarve Forge'
    UNION ALL SELECT 35, 'Gnome Forge'
    UNION ALL SELECT 36, 'Barbarian Forge'
    UNION ALL SELECT 38, 'Iksar Forge'
    UNION ALL SELECT 39, 'Freeport Forge'
    UNION ALL SELECT 40, 'Qeynos Forge'
    UNION ALL SELECT 41, 'Halfling Tailoring kit'
    UNION ALL SELECT 42, 'Erudite Tailor'
    UNION ALL SELECT 43, 'Wood Elf Tailor'
    UNION ALL SELECT 44, 'Wood Elf Fletching kit'
    UNION ALL SELECT 45, 'Iksar Pottery Wheel'
    UNION ALL SELECT 47, 'Troll Forge'
    UNION ALL SELECT 48, 'Wood Elf Forge'
    UNION ALL SELECT 49, 'Halfling Forge'
    UNION ALL SELECT 50, 'Erudite Forge'
    UNION ALL SELECT 53, 'Augment')"""

def get_skills_by_character(characterID: int) -> dict:
  with getDb().cursor() as cur:
    # Step 1: Get character's class and race
    cur.execute("SELECT class, race FROM character_data WHERE id = %s AND deleted_at IS NULL", (characterID,))
    row = cur.fetchone()
    if not row:
      return {}

    characterClass = row["class"]
    characterRace = row["race"]

    # Step 2: Filter TRADESKILL based on class/race restrictions
    eligibleSkills = {
      skillId: name for skillId, name in TRADESKILL.items()
      if not (
        (skillId == 56 and characterClass != 8) or
        (skillId == 59 and characterClass != 9) or
        (skillId == 57 and characterRace != 11)
      )
    }

    if not eligibleSkills:
      return {}

    # Step 3: Build and execute pivot query
    skill_fields = [
      f"MAX(CASE WHEN skill_id = {skillId} THEN value END) AS `{skillId}`"
      for skillId in eligibleSkills
    ]
    sql = f"""
      SELECT {", ".join(skill_fields)}
      FROM character_skills
      WHERE id = %s
    """
    cur.execute(sql, (characterID,))
    return {int(k): v for k, v in (cur.fetchone() or {}).items() if v is not None}

def process_recipe_results(rows):
  recipes, excluded = {}, set()

  for row in rows:
    rid = row["id"]
    if rid in excluded:
      continue

    if rid not in recipes:
      recipes[rid] = {
        "id":               rid,
        "name":             row["name"],
        "tradeskill_id":    row["tradeskill"],
        "tradeskill_name":  TRADESKILL.get(row["tradeskill"], "Unknown"),
        "skillNeeded":      row["skillneeded"],
        "trivial":          row["trivial"],
        "outputs":          [],
        "containers":       [],
        "ingredients":      [],
        "returnedAlways":   [],
        "returnedOnFailure":[],
        "returnedOnSuccess":[]
      }

    item_sources = {
      "lootdrop":   row["lootdropEntries"],
      "merchant":   row["merchantListEntries"],
      "tradeskill": row["tradeskillRecipeEntries"],
      "quest":      row["questEntries"],
    }

    base_item = {
      "id":          row["item_id"],
      "name":        row["item_name"],
      "quantity":    0,                      # will be set per bucket
      "sources":     item_sources,
      "unobtainable": not any(item_sources.values()),
    }

    comp_cnt = row["componentcount"] or 0
    fail_cnt = row["failcount"]      or 0
    succ_cnt = row["successcount"]   or 0
    is_cont  = bool(row["iscontainer"])

    if is_cont:
      # containers never show a quantity
      recipes[rid]["containers"].append(base_item)
      continue

    if succ_cnt > 0 and comp_cnt == 0:
      # finished product
      out_item = dict(base_item)
      out_item["quantity"] = succ_cnt
      recipes[rid]["outputs"].append(out_item)
      continue

    if comp_cnt > 0:
      ing_item = dict(base_item)
      ing_item["quantity"] = comp_cnt
      recipes[rid]["ingredients"].append(ing_item)

      if fail_cnt and succ_cnt:               # always returned
        ret_item = dict(base_item)
        ret_item["quantity"] = succ_cnt
        recipes[rid]["returnedAlways"].append(ret_item)

      elif fail_cnt:                          # returned on failure
        ret_item = dict(base_item)
        ret_item["quantity"] = fail_cnt
        recipes[rid]["returnedOnFailure"].append(ret_item)

      elif succ_cnt:                          # returned on success
        ret_item = dict(base_item)
        ret_item["quantity"] = succ_cnt
        recipes[rid]["returnedOnSuccess"].append(ret_item)

      # drop whole recipe only if the ingredient is *consumed* AND unobtainable
      if not (fail_cnt or succ_cnt) and ing_item["unobtainable"]:
        excluded.add(rid)
        recipes.pop(rid, None)

  return list(recipes.values())

def get_skill_up_recipes(skillId, skillLevel):
  with getDb().cursor() as cur:
    expansionRule = get_current_expansion()

    cur.execute(f"""
      {TRADESKILL_OBJECT_TABLE}

      SELECT
        {RECIPE_TABLE_SELECT_FIELDS},
        tre.item_id,
        COALESCE(i.name, cm.object_type_name) AS item_name,
        tre.componentcount,
        tre.failcount,
        tre.iscontainer,
        tre.successcount,
        pis.lootdropEntries,
        pis.merchantListEntries,
        pis.tradeskillRecipeEntries,
        pis.questEntries
      FROM tradeskill_recipe tr
      LEFT JOIN tradeskill_recipe_entries tre ON tr.id = tre.recipe_id
      LEFT JOIN items i ON tre.item_id = i.id
      LEFT JOIN container_map cm ON tre.item_id = cm.object_type_id
      LEFT JOIN {DB_PREFIX}_item_sources pis ON i.id = pis.item_id
      WHERE tr.tradeskill = %s
        AND tr.skillneeded <= %s
        AND tr.trivial > %s
        AND tr.trivial < %s + 101
        AND tr.enabled = 1
        AND (tr.min_expansion <= %s)
        AND (tr.max_expansion = -1 OR tr.max_expansion >= %s)
        AND tr.id NOT IN (
          SELECT tre_bad.recipe_id
          FROM tradeskill_recipe_entries tre_bad
          LEFT JOIN items i2 ON tre_bad.item_id = i2.id
          WHERE tre_bad.item_id IS NOT NULL
            AND i2.id IS NULL
            AND (tre_bad.iscontainer IS NULL OR tre_bad.iscontainer = 0)
        )
      ORDER BY tr.trivial, tr.skillneeded ASC, tr.name
    """, (skillId, skillLevel, skillLevel, skillLevel, expansionRule, expansionRule))
    rows = cur.fetchall()
  return process_recipe_results(rows)

def get_item_recipes(itemId: int) -> List[Dict]:
  db = getDb()
  expansionRule = get_current_expansion()

  with db.cursor() as cur:
    cur.execute(f"""
      {TRADESKILL_OBJECT_TABLE}

      SELECT
        {RECIPE_TABLE_SELECT_FIELDS},
        tre.item_id,
        COALESCE(i.name, cm.object_type_name) AS item_name,
        tre.componentcount,
        tre.failcount,
        tre.iscontainer,
        tre.successcount,
        pis.lootdropEntries,
        pis.merchantListEntries,
        pis.tradeskillRecipeEntries,
        pis.questEntries
      FROM tradeskill_recipe tr
      JOIN tradeskill_recipe_entries tre ON tr.id = tre.recipe_id
      LEFT JOIN items i ON tre.item_id = i.id
      LEFT JOIN container_map cm ON tre.item_id = cm.object_type_id
      LEFT JOIN {DB_PREFIX}_item_sources pis ON i.id = pis.item_id
      WHERE tr.enabled = 1
        AND (tr.min_expansion <= %s)
        AND (tr.max_expansion = -1 OR tr.max_expansion >= %s)
        AND tr.id NOT IN (
          SELECT tre_bad.recipe_id
          FROM tradeskill_recipe_entries tre_bad
          LEFT JOIN items i2 ON tre_bad.item_id = i2.id
          WHERE tre_bad.item_id IS NOT NULL
            AND i2.id IS NULL
            AND (tre_bad.iscontainer IS NULL OR tre_bad.iscontainer = 0)
        )
        AND tr.id IN (
          SELECT recipe_id
          FROM tradeskill_recipe_entries
          WHERE item_id = %s
            AND successcount > 0
            AND componentcount = 0
        )
      ORDER BY tr.trivial, tr.skillneeded ASC, tr.name
    """, (expansionRule, expansionRule, itemId))
    rows = cur.fetchall()
  return process_recipe_results(rows)
