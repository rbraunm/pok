from typing import List, Dict, Any
import pymysql.cursors
from db import getDb, DB_PREFIX
from api.models.npcs import get_npc_spawnpoints
from api.models.characters import get_character
from applogging import get_logger
logger = get_logger(__name__)

RESIST_TYPES = {
  0: "Unresistable",
  1: "Magic",
  2: "Fire",
  3: "Cold",
  4: "Poison",
  5: "Disease",
  6: "Chromatic",
  7: "Prismatic",
  8: "Physical",
  9: "Corruption"
}

SPELL_CATEGORIES = {
  -99: "NPC",
  -1: "AA Procs",
  1: "Direct Damage [Magic]",
  2: "Direct Damage [Undead]",
  3: "Direct Damage [Summoned]",
  4: "Direct Damage [Life Taps]",
  5: "Direct Damage [Plant]",
  6: "Direct Damage [Velious Races]",
  7: "Damage over Time [Magic]",
  8: "Damage over Time [Undead]",
  9: "Damage over Time [Life Taps]",
  10: "Targeted Area of Effect Damage",
  11: "Point Blank Area of Effect Damage",
  12: "Area of Effect Rain",
  13: "Direct Damage [Bolt]",
  14: "Stun [Targeted Area of Effect]",
  15: "Stun [Targeted]",
  16: "Stun [Point Blank Area of Effect]",
  17: "Drains [Health/Mana]",
  18: "Drains [Stats]",
  19: "Contact Innates",
  20: "Heal [Instant]",
  21: "Heal [Duration]",
  22: "Group Heal [Instant]",
  23: "Group Heal [Duration]",
  24: "Regeneration [Single]",
  25: "Regeneration [Group]",
  26: "Heal [Own Pet]",
  27: "Resurrect",
  28: "Necromancer Life Transfer",
  29: "Cure [Poison]",
  30: "Health Buffs [Single]",
  32: "AC Buff [Single]",
  34: "Hate Mod Buffs",
  35: "Haste [Single]",
  36: "Haste [Pet]",
  37: "Haste [Group]",
  38: "Slow [Single]",
  39: "Slow [Targeted Area]",
  40: "Cannabalize",
  41: "Move Speed [Single]",
  42: "Move Speed [Group]",
  43: "Wolf Form",
  44: "Move Speed [Pet]",
  45: "Illusion [Self]",
  46: "Lich",
  47: "Bear Form",
  48: "Tree Form",
  49: "Dead Man Floating",
  50: "Root",
  51: "Summon Pet",
  52: "Summon Corpse",
  53: "Sense Undead",
  54: "Invulnerability",
  55: "Gate [Combat Portal]",
  56: "Gate [Self Gates]",
  58: "Translocate",
  59: "Shadow Step",
  60: "Enchant Item",
  61: "Summon [Misc Item]",
  62: "Fear",
  63: "Fear [Animal]",
  64: "Fear [Undead]",
  65: "Damage Shield [Single]",
  66: "Damage Shield [Group]",
  67: "Mark Of Karn",
  68: "Damage Shield [Self]",
  69: "Resist Debuffs",
  70: "Resist Buffs",
  71: "BST Pet Buffs",
  72: "Summon Familiar",
  73: "STR Buff",
  74: "DEX Buff",
  75: "AGI Buff",
  76: "STA Buff",
  77: "INT Buff",
  78: "CHA Buff",
  79: "Stat Debuffs",
  80: "Invisible Undead",
  81: "Invisible Animals",
  82: "Invisibility",
  83: "Absorb Damage",
  84: "Casting Level Buffs",
  85: "Clarity Line",
  86: "Max Mana Buffs",
  87: "Drain Mana",
  88: "Mana Transfer",
  89: "Instant Gain Mana",
  90: "Lower Hate [Jolt]",
  91: "Increase Archery",
  92: "Attack Buff",
  93: "Vision",
  94: "Water Breathing",
  95: "Improve Faction",
  96: "Charm",
  97: "Dispell",
  98: "Lull",
  99: "Mesmerise",
  100: "Spell Focus Items",
  101: "Snare [single]",
  102: "Snare [Area of Effect]",
  105: "Feign Death",
  106: "Identify",
  107: "Reclaim Energy",
  108: "Find Corpse",
  109: "Summon Player",
  110: "Spell Shield",
  112: "Blindness",
  113: "Levitation",
  114: "Extinguish Fatigue",
  115: "Death Pact",
  116: "Memory Blur",
  118: "Height",
  119: "Add Hate",
  120: "Iron Maiden",
  121: "Focus Spells",
  122: "Melee Guard",
  125: "Direct Damage [Fire]",
  126: "Direct Damage [Ice]",
  127: "Direct Damage [Poison]",
  128: "Direct Damage [Disease]",
  129: "Damage over Time [Fire]",
  130: "Damage over Time [Ice]",
  131: "Damage over Time [Poison]",
  132: "Damage over Time [Disease]",
  133: "INT Caster Chest Opening",
  134: "INT Caster Chest Trap Appraisal",
  135: "INT Caster Chest Trap Disarm",
  136: "WIS Caster Chest Trap Disarm",
  137: "WIS Caster Chest Trap Appraisal",
  138: "WIS Caster Chest Opening",
  140: "Destroy [Undead]",
  141: "Destroy [Summoned]",
  142: "Targeted Area of Effect [Fire]",
  143: "Targeted Area of Effect [Ice]",
  146: "Point Blank Area of Effect [Fire]",
  147: "Point Blank Area of Effect [Ice]",
  150: "Rain [Fire]",
  151: "Rain [Ice]",
  152: "Rain [Poison]",
  154: "Fear Song",
  155: "Fast Heals",
  156: "Mana to Health",
  157: "Pet Siphons",
  159: "Cure [Disease]",
  160: "Cure [Curse]",
  161: "Cure [Multiple]",
  162: "Cure [Blind]",
  163: "Group Cure [Multiple]",
  164: "Misc Effects",
  165: "Shielding",
  166: "PAL/RNG/BST Health Buffs",
  167: "Symbols",
  168: "Aegolism Line",
  169: "Paladin AC Buffs",
  170: "Spell Damage Mitigate",
  171: "Spell/Melee Block",
  172: "Spell Reflect",
  173: "Hybrid AC Buffs",
  174: "Health/Mana Regeneration",
  175: "Aggro Decreasers",
  200: "Misc Spells",
  201: "Disciplines",
  202: "Melee Haste",
  203: "Area of Effect Slow",
  204: "Summon Air Pet",
  205: "Summon Water Pet",
  206: "Summon Fire Pet",
  207: "Summon Earth Pet",
  208: "Summon Monster Pet",
  209: "Transport [Antonica]",
  210: "Transport [Odus]",
  211: "Transport [Faydwer]",
  212: "Transport [Kunark]",
  213: "Transport [Velious]",
  214: "Transport [Luclin]",
  215: "Transport [Planes]",
  216: "Transport [Gates/Omens]",
  217: "Summon [Weapon]",
  218: "Summon [Focus]",
  219: "Summon [Food/Drink]",
  220: "Summon [Armor]",
  999: "AA / Abilities"
}

def generate_spell_category_case(field_name="spell_category", alias="spell_category"):
  lines = [f"CASE {field_name}"]
  for key, label in sorted(SPELL_CATEGORIES.items()):
    escaped_label = label.replace("'", "''")  # escape single quotes
    lines.append(f"  WHEN {key} THEN '{escaped_label}'")
  lines.append(f"  ELSE 'Unknown'")
  lines.append(f"END AS {alias}")

  return "\n".join(lines)

SPELL_TABLE_SELECT_FIELDS = """
  s.id,
  s.`name`,
  s.icon as old_icon,
  s.memicon as gem_icon,
  s.new_icon + 1 as icon,
  s.player_1,
  s.teleport_zone,
  s.you_cast,
  s.other_casts,
  s.cast_on_you,
  s.cast_on_other,
  s.spell_fades,
  s.`range`,
  s.aoerange,
  s.pushback,
  s.pushup,
  s.cast_time,
  s.recovery_time,
  s.recast_time,
  s.buffdurationformula,
  s.buffduration,
  s.AEDuration,
  s.mana,
  s.effect_base_value1,
  s.effect_base_value2,
  s.effect_base_value3,
  s.effect_base_value4,
  s.effect_base_value5,
  s.effect_base_value6,
  s.effect_base_value7,
  s.effect_base_value8,
  s.effect_base_value9,
  s.effect_base_value10,
  s.effect_base_value11,
  s.effect_base_value12,
  s.effect_limit_value1,
  s.effect_limit_value2,
  s.effect_limit_value3,
  s.effect_limit_value4,
  s.effect_limit_value5,
  s.effect_limit_value6,
  s.effect_limit_value7,
  s.effect_limit_value8,
  s.effect_limit_value9,
  s.effect_limit_value10,
  s.effect_limit_value11,
  s.effect_limit_value12,
  s.max1,
  s.max2,
  s.max3,
  s.max4,
  s.max5,
  s.max6,
  s.max7,
  s.max8,
  s.max9,
  s.max10,
  s.max11,
  s.max12,
  s.components1,
  s.components2,
  s.components3,
  s.components4,
  s.component_counts1,
  s.component_counts2,
  s.component_counts3,
  s.component_counts4,
  s.NoexpendReagent1,
  s.NoexpendReagent2,
  s.NoexpendReagent3,
  s.NoexpendReagent4,
  s.formula1,
  s.formula2,
  s.formula3,
  s.formula4,
  s.formula5,
  s.formula6,
  s.formula7,
  s.formula8,
  s.formula9,
  s.formula10,
  s.formula11,
  s.formula12,
  s.LightType,
  s.goodEffect,
  s.Activated,
  s.resisttype,
  s.effectid1,
  s.effectid2,
  s.effectid3,
  s.effectid4,
  s.effectid5,
  s.effectid6,
  s.effectid7,
  s.effectid8,
  s.effectid9,
  s.effectid10,
  s.effectid11,
  s.effectid12,
  s.targettype,
  s.basediff,
  s.skill,
  s.zonetype,
  s.EnvironmentType,
  s.TimeOfDay,
  CASE WHEN s.classes1  <= 70 THEN s.classes1  ELSE NULL END AS classes1,
  CASE WHEN s.classes2  <= 70 THEN s.classes2  ELSE NULL END AS classes2,
  CASE WHEN s.classes3  <= 70 THEN s.classes3  ELSE NULL END AS classes3,
  CASE WHEN s.classes4  <= 70 THEN s.classes4  ELSE NULL END AS classes4,
  CASE WHEN s.classes5  <= 70 THEN s.classes5  ELSE NULL END AS classes5,
  CASE WHEN s.classes6  <= 70 THEN s.classes6  ELSE NULL END AS classes6,
  CASE WHEN s.classes7  <= 70 THEN s.classes7  ELSE NULL END AS classes7,
  CASE WHEN s.classes8  <= 70 THEN s.classes8  ELSE NULL END AS classes8,
  CASE WHEN s.classes9  <= 70 THEN s.classes9  ELSE NULL END AS classes9,
  CASE WHEN s.classes10 <= 70 THEN s.classes10 ELSE NULL END AS classes10,
  CASE WHEN s.classes11 <= 70 THEN s.classes11 ELSE NULL END AS classes11,
  CASE WHEN s.classes12 <= 70 THEN s.classes12 ELSE NULL END AS classes12,
  CASE WHEN s.classes13 <= 70 THEN s.classes13 ELSE NULL END AS classes13,
  CASE WHEN s.classes14 <= 70 THEN s.classes14 ELSE NULL END AS classes14,
  CASE WHEN s.classes15 <= 70 THEN s.classes15 ELSE NULL END AS classes15,
  CASE WHEN s.classes16 <= 70 THEN s.classes16 ELSE NULL END AS classes16,
  s.CastingAnim,
  s.TargetAnim,
  s.TravelType,
  s.SpellAffectIndex,
  s.disallow_sit,
  s.spellanim,
  s.uninterruptable,
  s.ResistDiff,
  s.dot_stacking_exempt,
  s.deleteable,
  s.RecourseLink,
  s.no_partial_resist,
  s.short_buff_box,
  s.descnum,
  s.typedescnum,
  s.effectdescnum,
  s.effectdescnum2,
  s.npc_no_los,
  s.reflectable,
  s.bonushate,
  s.ldon_trap,
  s.EndurCost,
  s.EndurTimerIndex,
  s.IsDiscipline,
  s.HateAdded,
  s.EndurUpkeep,
  s.numhitstype,
  s.numhits,
  s.pvpresistbase,
  s.pvpresistcalc,
  s.pvpresistcap,
  s.pvp_duration,
  s.pvp_duration_cap,
  s.pcnpc_only_flag,
  s.cast_not_standing,
  s.can_mgb,
  s.nodispell,
  s.npc_category,
  s.npc_usefulness,
  s.MinResist,
  s.MaxResist,
  s.viral_targets,
  s.viral_timer,
  s.nimbuseffect,
  s.ConeStartAngle,
  s.ConeStopAngle,
  s.sneaking,
  s.not_extendable,
  s.suspendable,
  s.viral_range,
  s.songcap,
  s.no_block,
  s.spellgroup,
  s.rank,
  s.CastRestriction,
  s.allowrest,
  s.InCombat,
  s.OutofCombat,
  s.aemaxtargets,
  s.maxtargets,
  s.persistdeath,
  s.min_dist,
  s.min_dist_mod,
  s.max_dist,
  s.max_dist_mod,
  s.min_range,
  pis.lootdropEntries,
  pis.merchantListEntries,
  pis.tradeskillRecipeEntries,
  pis.questEntries,
""" + generate_spell_category_case()

class SpellNotFoundError(Exception):
  pass

def search_spells(query: str, limit: int = 20) -> List[Dict[str, Any]]:
  sql = f"""
    SELECT {SPELL_TABLE_SELECT_FIELDS}
    FROM spells_new s
    LEFT JOIN items i ON s.id = i.scrolleffect
    LEFT JOIN {DB_PREFIX}_item_sources pis ON i.id = pis.item_id
    WHERE name LIKE %s
      AND (pis.lootdropEntries IS NOT NULL OR
          pis.merchantListEntries IS NOT NULL OR
          pis.tradeskillRecipeEntries IS NOT NULL OR
          pis.questEntries IS NOT NULL)
    GROUP BY s.id
    ORDER BY name ASC
    LIMIT %s
  """
  with getDb().cursor(pymysql.cursors.DictCursor) as cur:
    cur.execute(sql, (f"%{query}%", limit))
    return cur.fetchall()

def get_spells_for_character(charId: int) -> List[Dict[str, Any]]:
  character = get_character(charId)
  if not character:
    raise ValueError(f"Character with ID {charId} not found")

  charClassId = character["class_id"]
  charLevel = character["level"]

  classColumn = f"classes{charClassId}"

  sql = f"""
    SELECT {SPELL_TABLE_SELECT_FIELDS},
      s.{classColumn} AS required_level,
      CASE WHEN cs.id IS NOT NULL THEN 1 ELSE 0 END AS known,
      pis.lootdropEntries,
      pis.merchantListEntries,
      pis.tradeskillRecipeEntries,
      pis.questEntries
    FROM spells_new s
    LEFT JOIN items i ON s.id = i.scrolleffect
    LEFT JOIN character_spells cs ON s.id = cs.spell_id AND cs.id = %s
    LEFT JOIN {DB_PREFIX}_item_sources pis ON i.id = pis.item_id
    WHERE s.{classColumn} > 0 AND s.{classColumn} <= %s AND
        (pis.lootdropEntries IS NOT NULL OR
          pis.merchantListEntries IS NOT NULL OR
          pis.tradeskillRecipeEntries IS NOT NULL OR
          pis.questEntries IS NOT NULL)
    GROUP BY s.id
    ORDER BY s.{classColumn}, s.name
  """
  with getDb().cursor(pymysql.cursors.DictCursor) as cur:
    cur.execute(sql, (charId, charLevel))
    return cur.fetchall()

def get_spell(spellId: int) -> Dict[str, Any]:
  db = getDb()
  with db.cursor(pymysql.cursors.DictCursor) as cur:
    cur.execute(f"""
      SELECT {SPELL_TABLE_SELECT_FIELDS}
      FROM spells_new s
      LEFT JOIN items i ON s.id = i.scrolleffect
      LEFT JOIN {DB_PREFIX}_item_sources pis ON i.id = pis.item_id
      WHERE s.id = %s
      GROUP BY s.id
    """, (spellId,))
    spell = cur.fetchone()
    if not spell:
      raise SpellNotFoundError(f"Spell with ID {spellId} not found.")
  return spell

def get_spell_drops(spellId: int) -> List[Dict[str, Any]]:
  sql = """
    SELECT
      s.id AS spell_id,
      nt.id AS npc_id,
      lde.item_id,
      lde.chance AS base_chance,
      ROUND(le.multiplier, 2) AS multiplier,
      ROUND(lde.chance * le.multiplier, 2) AS effective_chance
    FROM spells_new s
    JOIN items i ON i.scrolleffect = s.id
    JOIN lootdrop_entries lde ON lde.item_id = i.id
    JOIN loottable_entries le ON lde.lootdrop_id = le.lootdrop_id
    JOIN loottable lt ON le.loottable_id = lt.id
    JOIN npc_types nt ON lt.id = nt.loottable_id
    WHERE s.id = %s
    GROUP BY nt.id
    ORDER BY effective_chance DESC
  """

  db = getDb()
  with db.cursor(pymysql.cursors.DictCursor) as cur:
    cur.execute(sql, (spellId,))
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
            'maxlevel': npcInfo.get('level')
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

def get_spell_merchants(spellId: int) -> List[int]:
  db = getDb()
  with db.cursor() as cur:
    cur.execute(f"""
      SELECT pis.merchantListEntries
      FROM spells_new s
      JOIN items i ON i.scrolleffect = s.id
      JOIN {DB_PREFIX}_item_sources pis ON pis.item_id = i.id
      WHERE s.id = %s
    """, (spellId,))
    row = cur.fetchone()

  if not row or not row[0]:
    return []

  return [int(mid) for mid in row[0].split(',')]

def get_spell_recipes(spellId: int) -> List[int]:
  db = getDb()
  with db.cursor() as cur:
    cur.execute(f"""
      SELECT pis.tradeskillRecipeEntries
      FROM spells_new s
      JOIN items i ON i.scrolleffect = s.id
      JOIN {DB_PREFIX}_item_sources pis ON pis.item_id = i.id
      WHERE s.id = %s
    """, (spellId,))
    row = cur.fetchone()

  if not row or not row[0]:
    return []

  return [int(rid) for rid in row[0].split(',')] 
