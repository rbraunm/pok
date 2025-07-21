from typing import List, Dict, Any
import pymysql.cursors
from api.db import getDb

SPELL_TABLE_SELECT_FIELDS = """
  id,
  name,
  spelllevel,
  classes,
  mana,
  casttime,
  recasttime,
  recovery_time,
  buffduration,
  buffdurationformula,
  range,
  aoerange,
  pushback,
  resisttype,
  skill,
  targettype,
  icon,
  memicon,
  components1,
  component_counts1,
  components2,
  component_counts2,
  components3,
  component_counts3,
  components4,
  component_counts4,
  you_cast,
  cast_on_you,
  cast_on_other,
  spell_fades
"""

class SpellNotFoundError(Exception):
  pass

def search_spells(query: str, limit: int = 20) -> List[Dict[str, Any]]:
  sql = f"""
    SELECT {SPELL_TABLE_SELECT_FIELDS}
    FROM spells_new
    WHERE name LIKE %s
    ORDER BY name ASC
    LIMIT %s
  """
  with getDb().cursor(pymysql.cursors.DictCursor) as cur:
    cur.execute(sql, (f"%{query}%", limit))
    return cur.fetchall()

def get_spells_for_character(char_id: int) -> List[Dict[str, Any]]:
  sql = f"""
    SELECT {SPELL_TABLE_SELECT_FIELDS}
    FROM character_spells cs
    JOIN spells_new s ON cs.spell_id = s.id
    WHERE cs.char_id = %s
    ORDER BY s.spelllevel, s.name
  """
  with getDb().cursor(pymysql.cursors.DictCursor) as cur:
    cur.execute(sql, (char_id,))
    return cur.fetchall()

def get_spell(spellId: int) -> Dict[str, Any]:
  db = getDb()
  with db.cursor(pymysql.cursors.DictCursor) as cur:
    cur.execute(f"""
      SELECT {SPELL_TABLE_SELECT_FIELDS}
      FROM spells_new
      WHERE id = %s
    """, (spellId,))
    spell = cur.fetchone()
    if not spell:
      raise SpellNotFoundError(f"Spell with ID {spellId} not found.")
  return spell

__all__ = [
  "get_spell",
  "get_spells_for_character",
  "search_spells"
]
