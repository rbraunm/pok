from typing import List, Dict, Any
import pymysql.cursors
from api.db import getDb

NPC_TYPES_TABLE_SELECT_FIELDS = """
  nt.id,
  nt.name,
  nt.lastname,
  nt.level,
  nt.race,
  nt.class,
  nt.bodytype,
  nt.hp,
  nt.mana,
  nt.gender,
  nt.texture,
  nt.helmtexture,
  nt.size,
  nt.hp_regen_rate,
  nt.mana_regen_rate,
  nt.mindmg,
  nt.maxdmg,
  nt.npc_faction_id,
  nt.special_abilities,
  nt.npc_spells_id,
  nt.loottable_id,
  nt.prim_melee_type,
  nt.sec_melee_type,
  nt.runspeed,
  nt.AC,
  nt.ATK,
  nt.Accuracy,
  nt.slow_mitigation,
  nt.attack_delay,
  nt.attack_speed
"""

class NpcNotFoundError(Exception):
  pass

def search_npcs(query: str, limit: int = 20) -> List[Dict[str, Any]]:
  sql = f"""
    SELECT {NPC_TYPES_TABLE_SELECT_FIELDS}
    FROM npc_types nt
    WHERE name LIKE %s
    ORDER BY name ASC
    LIMIT %s
  """
  with getDb().cursor(pymysql.cursors.DictCursor) as cur:
    cur.execute(sql, (f"%{query}%", limit))
    return cur.fetchall()

def get_npc(npcId: int) -> Dict[str, Any]:
  db = getDb()
  with db.cursor(pymysql.cursors.DictCursor) as cur:
    cur.execute(f"""
      SELECT {NPC_TYPES_TABLE_SELECT_FIELDS}
      FROM npc_types nt
      WHERE id = %s
    """, (npcId,))
    npc = cur.fetchone()
    if not npc:
      raise NpcNotFoundError(f"NPC with ID {npcId} not found.")
  return npc

def get_npc_spawnpoints(npcId: int) -> Dict[str, Any]:
  db = getDb()
  with db.cursor(pymysql.cursors.DictCursor) as cur:
    cur.execute("""
      SELECT rule_value
      FROM rule_values
      WHERE rule_name = 'Expansion:CurrentExpansion'
    """)
    expansionRow = cur.fetchone()
    if not expansionRow:
      raise Exception("Current expansion rule not set.")
    currentExpansion = int(expansionRow['rule_value'])

    sql = f"""
      SELECT
        {NPC_TYPES_TABLE_SELECT_FIELDS},
        z.short_name AS zone_shortname,
        z.long_name AS zone_longname,
        ROUND(s2.x, 1) AS x,
        ROUND(s2.y, 1) AS y,
        ROUND(s2.z, 1) AS z,
        s2.respawntime
      FROM npc_types nt
      LEFT JOIN spawnentry se ON nt.id = se.npcID
      LEFT JOIN spawn2 s2 ON se.spawngroupID = s2.spawngroupID
      LEFT JOIN zone z ON s2.zone = z.short_name
      WHERE nt.id = %s
        AND (
          (se.min_expansion = -1 OR se.min_expansion <= %s)
          AND (se.max_expansion = -1 OR se.max_expansion >= %s)
        )
        AND (
          (z.min_expansion = -1 OR z.min_expansion <= %s)
          AND (z.max_expansion = -1 OR z.max_expansion >= %s)
        )
        AND (
          z.expansion <= %s
        )
      ORDER BY z.long_name, s2.id
    """

    cur.execute(sql, (npcId, currentExpansion, currentExpansion, currentExpansion, currentExpansion, currentExpansion))
    rows = cur.fetchall()

  if not rows:
    return {}

  npcFieldNames = [f.split('.')[-1] for f in NPC_TYPES_TABLE_SELECT_FIELDS.replace('\n', '').replace(' ', '').split(',')]
  npcInfo = {k: v for k, v in rows[0].items() if k in npcFieldNames}

  zoneGrouped = {}
  for row in rows:
    zoneKey = row['zone_shortname']
    if zoneKey not in zoneGrouped:
      zoneGrouped[zoneKey] = {
        'zone_longname': row['zone_longname'],
        'spawnpoints': []
      }
    zoneGrouped[zoneKey]['spawnpoints'].append({
      'x': row['x'],
      'y': row['y'],
      'z': row['z'],
      'respawntime': row['respawntime']
    })

  npcInfo['zones'] = zoneGrouped
  return npcInfo

__all__ = [
  "get_npc",
  "search_npcs",
  "get_npc_spawnpoints"
]
