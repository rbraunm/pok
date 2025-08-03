from typing import Dict, List
from api.db import getDb
from api.models.eqemu import get_current_expansion

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
  recipes = {}
  excluded = set()

  for row in rows:
    recipeId = row["id"]

    # Skip processing if already excluded
    if recipeId in excluded:
      continue

    # Initialize the recipe block
    if recipeId not in recipes:
      recipes[recipeId] = {
        "id": recipeId,
        "name": row["name"],
        "tradeskill_id": row["tradeskill"],
        "tradeskill_name": TRADESKILL.get(row["tradeskill"], "Unknown"),
        "skillNeeded": row["skillneeded"],
        "trivial": row["trivial"],
        "outputs": [],
        "containers": [],
        "ingredients": []
      }

    item = {
      "id": row["item_id"],
      "name": row["item_name"],
      "componentCount": row["componentcount"],
      "failCount": row["failcount"],
      "successCount": row["successcount"],
      "isContainer": bool(row["iscontainer"]),
      "sources": {
        "lootdrop": row["lootdropEntries"],
        "merchant": row["merchantListEntries"],
        "tradeskill": row["tradeskillRecipeEntries"],
        "quest": row["questEntries"]
      }
    }

    # Classify the item
    if item["successCount"] > 0 and item["componentCount"] == 0:
      recipes[recipeId]["outputs"].append(item)
    elif item["isContainer"]:
      recipes[recipeId]["containers"].append(item)
    elif item["componentCount"] and item["componentCount"] > 0:
      # Check if ingredient is obtainable
      if all(item["sources"][key] is None for key in item["sources"]):
        excluded.add(recipeId)
        del recipes[recipeId]  # discard the whole recipe
        continue
      recipes[recipeId]["ingredients"].append(item)

  return list(recipes.values())

def get_skill_up_recipes(skillId, skillLevel):
  with getDb().cursor() as cur:
    expansionRule = get_current_expansion()

    cur.execute(f"""
      SELECT
        {RECIPE_TABLE_SELECT_FIELDS},
        tre.item_id,
        i.name as item_name,
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
      LEFT JOIN pok_item_sources pis ON i.id = pis.item_id
      WHERE tr.tradeskill = %s
        AND tr.skillneeded <= %s
        AND tr.trivial > %s
        AND tr.trivial < %s + 101
        AND tr.enabled = 1
        AND (tr.min_expansion <= %s)
        AND (tr.max_expansion = -1 OR tr.max_expansion >= %s)
      ORDER BY tr.trivial, tr.skillneeded ASC, tr.name
    """, (skillId, skillLevel, skillLevel, skillLevel, expansionRule, expansionRule))
    rows = cur.fetchall()
  return process_recipe_results(rows)


def get_item_recipes(itemId: int) -> List[Dict]:
  db = getDb()
  expansionRule = get_current_expansion()

  with db.cursor() as cur:
    cur.execute(f"""
      SELECT
        {RECIPE_TABLE_SELECT_FIELDS},
        tre.item_id,
        i.name AS item_name,
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
      LEFT JOIN pok_item_sources pis ON i.id = pis.item_id
      WHERE tr.enabled = 1
        AND (tr.min_expansion <= %s)
        AND (tr.max_expansion = -1 OR tr.max_expansion >= %s)
        AND EXISTS (
          SELECT 1
          FROM tradeskill_recipe_entries tre_out
          WHERE tre_out.recipe_id = tr.id
            AND tre_out.item_id = %s
            AND tre_out.successcount > 0
            AND tre_out.componentcount = 0
        )
      ORDER BY tr.trivial, tr.skillneeded ASC, tr.name
    """, (expansionRule, expansionRule, itemId))
    rows = cur.fetchall()
  return process_recipe_results(rows)
