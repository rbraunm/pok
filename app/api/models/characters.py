from typing import List, Dict, Any
from api.db import getDb

CHARACTER_TABLE_SELECT_FIELDS = """
  c.id,
  c.account_id,
  c.birthday,
  c.time_played,
  c.last_login,
  c.title,
  c.name,
  c.last_name,
  c.suffix,
  c.race as race_id,
  c.`class` as class_id,
  c.deity as deity_id,
  c.level,
  c.agi,
  c.cha,
  c.dex,
  c.`int`,
  c.sta,
  c.str,
  c.wis,
  c.cur_hp as hp,
  c.mana,
  c.endurance,
  c.aa_points,
  c.aa_points_old,
  c.aa_points_spent,
  c.aa_points_spent_old,
  c.gender,
  c.face,
  c.eye_color_1,
  c.eye_color_2,
  c.hair_color,
  c.hair_style,
  c.beard,
  c.beard_color,
  c.drakkin_details,
  c.drakkin_heritage,
  c.drakkin_tattoo,
  c.show_helm,
  c.zone_id,
  c.`x`,
  c.`y`,
  c.`z`,
  c.deleted_at
"""

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

CLASS_ABBR_BITMASK = {
  "WAR": 1 << 0,
  "CLR": 1 << 1,
  "PAL": 1 << 2,
  "RNG": 1 << 3,
  "SHD": 1 << 4,
  "DRU": 1 << 5,
  "MNK": 1 << 6,
  "BRD": 1 << 7,
  "ROG": 1 << 8,
  "SHM": 1 << 9,
  "NEC": 1 << 10,
  "WIZ": 1 << 11,
  "MAG": 1 << 12,
  "ENC": 1 << 13,
  "BST": 1 << 14,
  "BER": 1 << 15
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

RACE_ABBR_BITMASK = {
  "HUM": 1 << 0,  # Human
  "BAR": 1 << 1,  # Barbarian
  "ERU": 1 << 2,  # Erudite
  "WEL": 1 << 3,  # Wood Elf
  "HIE": 1 << 4,  # High Elf
  "DEF": 1 << 5,  # Dark Elf
  "HEF": 1 << 6,  # Half Elf
  "DWF": 1 << 7,  # Dwarf
  "TRL": 1 << 8,  # Troll
  "OGR": 1 << 9,  # Ogre 
  "HFL": 1 << 10, # Halfling
  "GNM": 1 << 11, # Gnome
  "IKS": 1 << 12, # Iksar
  "VAH": 1 << 13, # Vah Shir
  "FRG": 1 << 14  # Froglok
}

DEITY_BITMASK = {
  "Agnostic":       1 << 0,
  "Bertoxxulous":   1 << 1,
  "Brell Serilis":  1 << 2,
  "Cazic Thule":    1 << 3,
  "Erollsi Marr":   1 << 4,
  "Bristlebane":    1 << 5,
  "Innoruuk":       1 << 6,
  "Karana":         1 << 7,
  "Mithaniel Marr": 1 << 8,
  "Prexus":         1 << 9,
  "Quellious":      1 << 10,
  "Rallos Zek":     1 << 11,
  "Rodcet Nife":    1 << 12,
  "Solusek Ro":     1 << 13,
  "The Tribunal":   1 << 14,
  "Tunare":         1 << 15,
  "Veeshan":        1 << 16
}

SKILL = {
0: "1H Blunt",
1: "1H Slashing",
2: "2H Blunt",
3: "2H Slashing",
4: "Abjuration",
5: "Alteration",
6: "Apply Poison",
7: "Archery",
8: "Backstab",
9: "Bind Wound",
10: "Bash",
11: "Block",
12: "Brass Instruments",
13: "Channeling",
14: "Conjuration",
15: "Defense",
16: "Disarm",
17: "Disarm Traps",
18: "Divination",
19: "Dodge",
20: "Double Attack",
21: "Dragon Punch",
22: "Dual Wield",
23: "Eagle Strike",
24: "Evocation",
25: "Feign Death",
26: "Flying Kick",
27: "Forage",
28: "Hand to Hand",
29: "Hide",
30: "Kick",
31: "Meditate",
32: "Mend",
33: "Offense",
34: "Parry",
35: "Pick Lock",
36: "1H Piercing",
37: "Riposte",
38: "Round Kick",
39: "Safe Fall",
40: "Sense Heading",
41: "Singing",
42: "Sneak",
43: "Specialize Abjure",
44: "Specialize Alteration",
45: "Specialize Conjuration",
46: "Specialize Divination",
47: "Specialize Evocation",
48: "Pick Pockets",
49: "Stringed Instruments",
50: "Swimming",
51: "Throwing",
52: "Tiger Claw",
53: "Tracking",
54: "Wind Instruments",
55: "Fishing",
56: "Make Poison",
57: "Tinkering",
58: "Research",
59: "Alchemy",
60: "Baking",
61: "Tailoring",
62: "Sense Traps",
63: "Blacksmithing",
64: "Fletching",
65: "Brewing",
66: "Alcohol Tolerance",
67: "Begging",
68: "Jewelry Making",
69: "Pottery",
70: "Percussion Instruments",
71: "Intimidation",
72: "Berserking",
73: "Taunt",
74: "Frenzy",
75: "Remove Trap",
76: "Triple Attack",
77: "2H Piercing"
}

def get_deity_name(deityId: int) -> str:
  bitIndex = deityId - 200
  mask = 1 << bitIndex
  for name, bit in DEITY_BITMASK.items():
    if bit == mask:
      return name
  return f"Unknown Deity ({deityId})"

def search_characters(query: str, limit: int = 20) -> List[Dict[str, Any]]:
  sql = f"""
    SELECT {CHARACTER_TABLE_SELECT_FIELDS}
    FROM character_data c
    WHERE name LIKE %s
      AND deleted_at IS NULL
    ORDER BY name ASC
    LIMIT %s
  """
  with getDb().cursor() as cur:
    cur.execute(sql, (f"%{query}%", limit))
    return cur.fetchall()

def get_character(char_id: int) -> Dict[str, Any] | None:
  sql = f"""
    SELECT {CHARACTER_TABLE_SELECT_FIELDS}
    FROM character_data c
    WHERE id = %s
      AND deleted_at IS NULL
  """
  with getDb().cursor() as cur:
    cur.execute(sql, (char_id,))
    return cur.fetchone()

def list_characters(limit: int = 50, offset: int = 0) -> List[Dict[str, Any]]:
  sql = f"""
    SELECT {CHARACTER_TABLE_SELECT_FIELDS}
    FROM character_data c
    WHERE deleted_at IS NULL
    ORDER BY name ASC
    LIMIT %s OFFSET %s
  """
  with getDb().cursor() as cur:
    cur.execute(sql, (limit, offset))
    return cur.fetchall()
