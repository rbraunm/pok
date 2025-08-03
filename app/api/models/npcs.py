from typing import List, Dict, Any
import pymysql.cursors
from api.db import getDb
from api.models.eqemu import get_current_expansion

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
    expansionRule = get_current_expansion()

    sql = f"""
      SELECT   
        {NPC_TYPES_TABLE_SELECT_FIELDS},
        z.short_name AS zone_shortname,
        z.long_name AS zone_longname,
        ROUND(s2.y, 1) AS y,
        ROUND(s2.x, 1) AS x,
        ROUND(s2.z, 1) AS z,
        s2.respawntime,
        se.chance,
        ph.placeholder_list AS placeholders 
      FROM npc_types nt
      JOIN spawnentry se ON nt.id = se.npcID
      JOIN spawn2 s2 ON se.spawngroupID = s2.spawngroupID
      JOIN zone z ON s2.zone = z.short_name
      LEFT JOIN (
        SELECT 
          spg.spawngroupID,
          GROUP_CONCAT(CONCAT(n2.name, ' (', spg.chance, '%%)') ORDER BY n2.name SEPARATOR ', ') AS placeholder_list
        FROM spawnentry spg
        JOIN npc_types n2 ON n2.id = spg.npcID
        WHERE spg.chance > 0 AND spg.npcID <> %s
        GROUP BY spg.spawngroupID
      ) ph ON ph.spawngroupID = s2.spawngroupID
      WHERE nt.id = %s
        AND se.chance > 0
        AND ((se.min_expansion = -1 OR se.min_expansion <= %s)
         AND (se.max_expansion = -1 OR se.max_expansion >= %s))
        AND ((z.min_expansion = -1 OR z.min_expansion <= %s)
         AND (z.max_expansion = -1 OR z.max_expansion >= %s))
        AND z.expansion <= %s
      ORDER BY z.long_name, s2.id
    """

    cur.execute(sql, (
      npcId, npcId,
      expansionRule, expansionRule,
      expansionRule, expansionRule,
      expansionRule
    ))
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
      'y': row['y'],
      'x': row['x'],
      'z': row['z'],
      'respawntime': row['respawntime'],
      'chance': row['chance'],
      'placeholders': row.get('placeholders')
    })

  npcInfo['zones'] = zoneGrouped
  return npcInfo


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
    expansionRule = get_current_expansion()
    cur.execute("""
      SELECT
        nt.id as npcId,
        nt.merchant_id as merchantId,
        nt.Name,
        i.price,
        z.short_name AS zone_shortname,
        z.long_name AS zone_longname,
        ROUND(s2.y, 1) AS y,
        ROUND(s2.x, 1) AS x,
        ROUND(s2.z, 1) AS z,
        s2.respawntime,
        se.chance
      FROM merchantlist ml
      LEFT JOIN npc_types nt ON nt.merchant_id = ml.merchantid
      LEFT JOIN spawnentry se ON nt.id = se.npcID
      LEFT JOIN spawn2 s2 ON se.spawngroupID = s2.spawngroupID
      LEFT JOIN zone z ON s2.zone = z.short_name
      LEFT JOIN items i ON ml.item = i.id
      WHERE (ml.min_expansion <= %s)
        AND (ml.max_expansion = -1 OR ml.max_expansion >= %s)
        AND (se.chance > 0)
        AND (se.min_expansion <= %s)
        AND (se.max_expansion = -1 OR se.max_expansion >= %s)
        AND (s2.min_expansion <= %s)
        AND (s2.max_expansion = -1 OR s2.max_expansion >= %s)
        AND (z.min_expansion <= %s)
        AND (z.max_expansion = -1 OR z.max_expansion >= %s)
        AND z.expansion <= %s
        AND ml.item = %s
      ORDER BY z.long_name, nt.Name;
    """, (expansionRule, expansionRule, expansionRule, expansionRule, 
          expansionRule, expansionRule, expansionRule, expansionRule, 
          expansionRule, itemId,))
    rows = cur.fetchall()

  return [dict(row) for row in rows]
