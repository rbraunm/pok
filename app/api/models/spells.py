from typing import List, Dict, Any
from api import getDb

def search_spells(query: str, limit: int = 20) -> List[Dict[str, Any]]:
  sql = """
    SELECT id, name, spelllevel, classes, mana, casttime, recasttime, resisttype
    FROM spells_new
    WHERE name LIKE %s
    ORDER BY name ASC
    LIMIT %s
  """
  with getDb().cursor() as cur:
    cur.execute(sql, (f"%{query}%", limit))
    return cur.fetchall()

def get_spells_for_character(char_id: int) -> List[Dict[str, Any]]:
  sql = """
    SELECT s.id, s.name, s.spelllevel, s.classes, s.mana, s.casttime, s.recasttime, s.resisttype
    FROM character_spells cs
    JOIN spells_new s ON cs.spell_id = s.id
    WHERE cs.char_id = %s
    ORDER BY s.spelllevel, s.name
  """
  with getDb().cursor() as cur:
    cur.execute(sql, (char_id,))
    return cur.fetchall()

def get_spell(spell_id: int) -> Dict[str, Any] | None:
  sql = "SELECT * FROM spells_new WHERE id = %s"
  with getDb().cursor() as cur:
    cur.execute(sql, (spell_id,))
    return cur.fetchone()
