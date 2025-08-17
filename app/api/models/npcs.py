import re
from typing import List, Dict, Any, Tuple, Optional
import pymysql.cursors
from db import getDb
from api.models.eqemu import get_current_expansion
from applogging import get_logger
logger = get_logger(__name__)

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
  nt.attack_speed,
  nt.raid_target,
  nt.rare_spawn
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
  sql = f"""
    SELECT
      {NPC_TYPES_TABLE_SELECT_FIELDS},
      lde.item_id,
      le.multiplier as loottable_multiplier,
      lde.chance,
      lde.multiplier
    FROM lootdrop_entries lde
    JOIN loottable_entries le ON lde.lootdrop_id = le.lootdrop_id
    JOIN loottable lt ON le.loottable_id = lt.id
    JOIN npc_types nt ON lt.id = nt.loottable_id
    WHERE lde.item_id = %s
    ORDER BY
      GREATEST(le.multiplier, lde.multiplier) DESC,
      LEAST(le.multiplier, lde.multiplier) DESC,
      lde.chance DESC
  """

  db = getDb()
  with db.cursor(pymysql.cursors.DictCursor) as cur:
    cur.execute(sql, (itemId,))
    npcDrops = cur.fetchall()

  # group per (npc_name, zoneShort, drop_table_multiplier, drop_chance, drop_multiplier)
  aggregated: Dict[Tuple[str, str, int, float, int], Dict[str, Any]] = {}

  def _meta_from(npc_info: Dict[str, Any], row: Dict[str, Any]) -> Dict[str, Any]:
    return {
      'id'      : npc_info.get('id') or row.get('id'),
      'name'    : npc_info.get('name'),
      'lastname': npc_info.get('lastname'),
      'race'    : npc_info.get('race'),
      'class'   : npc_info.get('class'),
      'bodytype': npc_info.get('bodytype'),
      'runspeed': npc_info.get('runspeed'),
      'level'   : npc_info.get('level'),
      'maxlevel': npc_info.get('level'),
    }
  
  def _safe_int(v: Any, default: int = 0) -> int:
    try:
      return int(float(v))
    except Exception:
      return default

  def _safe_float(v: Any, default: float = 0.0) -> float:
    try:
      return float(v)
    except Exception:
      return default

  def _qf(v: Any, places: int = 6) -> float:
    """Quantize floats for dictionary keys (avoid 5 vs 5.000000)."""
    return round(_safe_float(v, 0.0), places)

  def _spawnpoint_key(sp: Dict[str, Any]) -> Tuple:
    sid = sp.get('spawn2_id') or sp.get('spawn_id') or sp.get('id')
    if sid is not None:
      return ('id', int(sid))
    x = _safe_float(sp.get('x') if sp.get('x') is not None else sp.get('loc_x'))
    y = _safe_float(sp.get('y') if sp.get('y') is not None else sp.get('loc_y'))
    z = _safe_float(sp.get('z') if sp.get('z') is not None else sp.get('loc_z'))
    grid = sp.get('grid') if sp.get('grid') is not None else sp.get('pathgrid')
    try:
      grid = int(grid) if grid is not None else 0
    except Exception:
      grid = 0
    return ('pos', round(x, 2), round(y, 2), round(z, 2), grid)

  def _merge_ph(phMap, ph):
    """
    Merge placeholder(s) into phMap.

    Accepts:
      - dict: {name|npc_name|npc|id}
      - list/tuple/set of dicts/strings/ints
      - string (supports comma/pipe separated)
      - int/other scalars
    """
    if not ph:
      return

    def _add(name):
      if name is None:
        return
      s = str(name).strip()
      if not s:
        return
      phMap[s] = phMap.get(s, 0) + 1

    def _from_dict(d):
      # Prefer name fields; fall back to id
      return (
        d.get('name') or
        d.get('npc_name') or
        d.get('npc') or
        (str(d.get('id')) if d.get('id') is not None else None)
      )

    # Single dict
    if isinstance(ph, dict):
      _add(_from_dict(ph))
      return

    # Iterable of mixed types
    if isinstance(ph, (list, tuple, set)):
      for x in ph:
        if isinstance(x, dict):
          _add(_from_dict(x))
        else:
          if isinstance(x, str) and (',' in x or '|' in x):
            for token in re.split(r'[,\|]+', x):
              _add(token)
          else:
            _add(x)
      return

    # Scalar (string/int/etc.)
    if isinstance(ph, str) and (',' in ph or '|' in ph):
      for token in re.split(r'[,\|]+', ph):
        _add(token)
    else:
      _add(ph)

  def _aggregate_spawnpoints(points: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    sp_map: Dict[Tuple, Dict[str, Any]] = {}

    for sp in points or []:
      key = _spawnpoint_key(sp)

      if key not in sp_map:
        base: Dict[str, Any] = {}
        # keep identity/position fields; NOTE: use respawntime (not respawn)
        for k in ('spawn2_id', 'spawn_id', 'id', 'x', 'y', 'z', 'heading',
                  'respawntime', 'grid', 'pathgrid', 'room'):
          if k in sp:
            base[k] = sp[k]

        # ensure fields exist
        base['chance'] = 0.0
        base['_ph_map'] = {}

        # normalize respawntime to an int
        base['respawntime'] = _safe_int(base.get('respawntime'), 0)

        sp_map[key] = base

      rec = sp_map[key]

      # accumulate chance from any of the source columns used earlier
      rec['chance'] += _safe_float(sp.get('chance') or sp.get('spawn_chance') or sp.get('prob'))

      # merge PHs
      _merge_ph(rec['_ph_map'], sp.get('ph') or sp.get('ph_list') or sp.get('placeholders'))

      # merge respawntime: prefer smallest positive; replace 0/None
      secs = _safe_int(sp.get('respawntime'), 0)
      cur  = _safe_int(rec.get('respawntime'), 0)
      if secs > 0 and (cur == 0 or secs < cur):
        rec['respawntime'] = secs

    # finalize list
    out: List[Dict[str, Any]] = []
    for rec in sp_map.values():
      ph_map = rec.pop('_ph_map', None)
      if ph_map:
        rec['ph'] = [
          {'name': n, 'chance': c}
          for n, c in sorted(ph_map.items(), key=lambda kv: kv[1], reverse=True)
        ]
      out.append(rec)

    out.sort(key=lambda r: r.get('chance', 0.0), reverse=True)
    return out

  for npc in npcDrops:
    npcSpawnData = get_npc_spawnpoints(npc['id'])
    if not npcSpawnData or not npcSpawnData.get('zones'):
      continue

    npcInfo = {k: v for k, v in npcSpawnData.items() if k != 'zones'}
    zones = npcSpawnData['zones']

    cur_level = npcInfo.get('level')
    score = float(cur_level) if cur_level is not None else float("-inf")
    meta = _meta_from(npcInfo, npc)

    # normalize drop fields for grouping
    dtm = int(npc['loottable_multiplier'])
    dch = _qf(npc['chance'])         # normalized float for key
    dmp = int(npc['multiplier'])

    for zoneShort, zoneData in zones.items():
      zlong = zoneData.get('zone_longname')
      new_points = list(zoneData.get('spawnpoints') or [])
      group_key = (npcInfo['name'], zoneShort, dtm, dch, dmp)

      if group_key not in aggregated:
        aggregated[group_key] = {
          'npc'                 : meta.copy(),   # replaced by best variant for this (name,zone,drop*) group
          '_best_meta'          : meta.copy(),
          '_best_score'         : score,
          '_min_level'          : cur_level,
          '_max_level'          : cur_level,
          'drop_table_multiplier': dtm,
          'drop_chance'         : float(dch),
          'drop_multiplier'     : dmp,
          'zones': {
            zoneShort: {
              'zone_longname': zlong,
              'spawnpoints'  : _aggregate_spawnpoints(new_points)
            }
          }
        }
      else:
        g = aggregated[group_key]

        # expand level range inside this group
        if g['_min_level'] is None or (cur_level is not None and cur_level < g['_min_level']):
          g['_min_level'] = cur_level
        if g['_max_level'] is None or (cur_level is not None and cur_level > g['_max_level']):
          g['_max_level'] = cur_level

        # choose best variant's npc meta (e.g., highest level)
        if score > g['_best_score']:
          g['_best_score'] = score
          g['_best_meta'] = meta.copy()

        # re-aggregate this zone's spawnpoints (sum chances & PHs)
        existing = g['zones'].get(zoneShort, {'zone_longname': zlong, 'spawnpoints': []})
        g['zones'][zoneShort] = {
          'zone_longname': zlong or existing.get('zone_longname'),
          'spawnpoints'  : _aggregate_spawnpoints(list(existing.get('spawnpoints') or []) + new_points)
        }

  # finalize each group
  out: List[Dict[str, Any]] = []
  for g in aggregated.values():
    best = g.pop('_best_meta')
    g['npc'] = best
    g['npc']['level'] = g.pop('_min_level')
    g['npc']['maxlevel'] = g.pop('_max_level')
    g.pop('_best_score', None)
    out.append(g)

  return out

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
