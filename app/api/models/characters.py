from typing import List, Dict, Any
from api.db import getDb

def search_characters(query: str, limit: int = 20) -> List[Dict[str, Any]]:
  sql = """
    SELECT id, name, class, level, race, deity
    FROM character_data
    WHERE name LIKE %s
    ORDER BY name ASC
    LIMIT %s
  """
  with getDb().cursor() as cur:
    cur.execute(sql, (f"%{query}%", limit))
    return cur.fetchall()

def get_character(char_id: int) -> Dict[str, Any] | None:
  sql = """
    SELECT id, name, class, level, race, deity
    FROM character_data
    WHERE id = %s
  """
  with getDb().cursor() as cur:
    cur.execute(sql, (char_id,))
    return cur.fetchone()
