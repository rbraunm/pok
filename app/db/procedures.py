import re
from db import DB_PREFIX
from applogging import get_logger
logger = get_logger(__name__)

PROCEDURE_PREFIX = f"{DB_PREFIX}"
_VALID_IDENT = re.compile(r"^[A-Za-z0-9_]+$")

def _procedureDefs():
  procs = []
  tableName = f"{DB_PREFIX}_item_sources"

  procs.append((
    "populate_item_sources",
    f"""
  DECLARE currentExpansion INT;

  -- Get current expansion
  SELECT rule_value INTO currentExpansion
  FROM rule_values
  WHERE rule_name = 'Expansion:CurrentExpansion';

  -- Clear the existing table
  TRUNCATE TABLE {tableName};

  -- Insert lootdropEntries
  INSERT INTO {tableName} (item_id, lootdropEntries)
  SELECT
    i.id AS item_id,
    GROUP_CONCAT(DISTINCT lde.lootdrop_id ORDER BY lde.lootdrop_id) AS lootdropEntries
  FROM items i
  JOIN lootdrop_entries lde ON lde.item_id = i.id
  JOIN loottable_entries le ON lde.lootdrop_id = le.lootdrop_id
  JOIN loottable lt ON le.loottable_id = lt.id
  JOIN npc_types nt ON lt.id = nt.loottable_id
  JOIN spawnentry se ON nt.id = se.npcID
  JOIN spawn2 s2 ON se.spawngroupID = s2.spawngroupID
  JOIN zone z ON s2.zone = z.short_name
  WHERE (se.chance > 0)
    AND (se.min_expansion <= currentExpansion)
    AND (se.max_expansion = -1 OR se.max_expansion >= currentExpansion)
    AND (s2.min_expansion <= currentExpansion)
    AND (s2.max_expansion = -1 OR s2.max_expansion >= currentExpansion)
    AND (z.min_expansion <= currentExpansion)
    AND (z.max_expansion = -1 OR z.max_expansion >= currentExpansion)
    AND z.expansion <= currentExpansion
  GROUP BY i.id
  ON DUPLICATE KEY UPDATE lootdropEntries = VALUES(lootdropEntries);

  -- Insert merchantListEntries
  INSERT INTO {tableName} (item_id, merchantListEntries)
  SELECT
    ml.item AS item_id,
    GROUP_CONCAT(DISTINCT ml.merchantid ORDER BY ml.merchantid) AS merchantListEntries
  FROM merchantlist ml
  JOIN npc_types nt ON nt.merchant_id = ml.merchantid
  JOIN spawnentry se ON nt.id = se.npcID
  JOIN spawn2 s2 ON se.spawngroupID = s2.spawngroupID
  JOIN zone z ON s2.zone = z.short_name
  WHERE (ml.min_expansion <= currentExpansion)
    AND (ml.max_expansion = -1 OR ml.max_expansion >= currentExpansion)
    AND (se.chance > 0)
    AND (se.min_expansion <= currentExpansion)
    AND (se.max_expansion = -1 OR se.max_expansion >= currentExpansion)
    AND (s2.min_expansion <= currentExpansion)
    AND (s2.max_expansion = -1 OR s2.max_expansion >= currentExpansion)
    AND (z.min_expansion <= currentExpansion)
    AND (z.max_expansion = -1 OR z.max_expansion >= currentExpansion)
    AND z.expansion <= currentExpansion
  GROUP BY ml.item
  ON DUPLICATE KEY UPDATE merchantListEntries = VALUES(merchantListEntries);

  -- Insert tradeskillRecipeEntries
  INSERT INTO {tableName} (item_id, tradeskillRecipeEntries)
  SELECT
    tre.item_id,
    GROUP_CONCAT(DISTINCT tre.recipe_id ORDER BY tre.recipe_id) AS tradeskillRecipeEntries
  FROM tradeskill_recipe_entries tre
  JOIN tradeskill_recipe tr ON tre.recipe_id = tr.id
  WHERE tre.successcount > 0
    AND tr.enabled = 1
    AND (tr.min_expansion = -1 OR tr.min_expansion <= currentExpansion)
    AND (tr.max_expansion = -1 OR tr.max_expansion >= currentExpansion)
  GROUP BY tre.item_id
  ON DUPLICATE KEY UPDATE tradeskillRecipeEntries = VALUES(tradeskillRecipeEntries);

  -- Placeholder for questEntries
  -- Implement when quest logic is defined
"""
  ))
  return procs

def dropProcedures(db):
  logger.info("Checking procedures...")
  likePattern = f"{DB_PREFIX}_%"
  with db.cursor() as cur:
    cur.execute("""
      SELECT ROUTINE_NAME
      FROM information_schema.routines
      WHERE routine_type = 'PROCEDURE'
        AND ROUTINE_NAME LIKE %s
    """, (likePattern),)
    rows = cur.fetchall()
    names = [r["ROUTINE_NAME"] if isinstance(r, dict) else r[0] for r in rows]

    for name in names:
      try:
        cur.execute(f"DROP PROCEDURE IF EXISTS {name}")
        logger.info(f"Dropped `{name}`")
      except Exception as e:
        logger.exception("Exception in db/procedures.py")
        logger.exception(f"FAILED to drop `{name}`: {e}")

def createProcedures(db):
  logger.info("Creating procedures...")
  defs = _procedureDefs()
  with db.cursor() as cur:
    for baseName, body in defs:
      procName = f"{PROCEDURE_PREFIX}_{baseName}"
      try:
        cur.execute(f"CREATE PROCEDURE {procName}() BEGIN\n{body}\nEND")
        logger.info(f"Created procedure `{procName}`")
      except Exception as e:
        logger.exception("Exception in db/procedures.py")
        logger.exception(f"FAILED to create procedure `{procName}`: {e}")
  db.commit()

def initializeProcedures(db):
  dropProcedures(db)
  createProcedures(db)

def _normalizeProcName(name: str) -> str:
  if not name:
    raise ValueError("procedureName is required")
  if "." in name or "`" in name:
    raise ValueError("Cross-schema or quoted procedure names are not allowed")

  if name.startswith(PROCEDURE_PREFIX):
    base = name[len(PROCEDURE_PREFIX):]
    if not _VALID_IDENT.match(base):
      raise ValueError(f"Invalid procedure name: {name!r}")
    return name

  if not _VALID_IDENT.match(name):
    raise ValueError(f"Invalid procedure name: {name!r}")
  return f"{PROCEDURE_PREFIX}_{name}"


def callStoredProcedure(db, procedureName, args=None, returnAll=False):
  """
  Call a stored procedure that belongs to this app (enforced by DB_PREFIX).
  - procedureName: 'base' (e.g. 'populate_item_sources') or full (e.g. 'pok_populate_item_sources')
  - If the procedure emits result set(s), return the first by default, or all if returnAll=True.
  - If no result sets are produced, return None.
  """
  fullName = _normalizeProcName(procedureName)
  logger.info(f"Calling stored procedure `{procedureName}`")
  args = tuple(args or ())
  placeholders = ", ".join(["%s"] * len(args))
  sql = f"CALL {fullName}({placeholders})" if placeholders else f"CALL {fullName}()"

  results = []
  with db.cursor() as cur:
    cur.execute(sql, args)

    # First result set (if any)
    try:
      rows = cur.fetchall()
      if rows:
        results.append(rows)
    except Exception:
      logger.exception("Exception in db/procedures.py")
      pass

    # Additional result sets (if any)
    while hasattr(cur, "nextset") and cur.nextset():
      try:
        rows = cur.fetchall()
        if rows:
          results.append(rows)
      except Exception:
        logger.exception("Exception in db/procedures.py")
        pass

  db.commit()

  if not results:
    return None
  if returnAll or len(results) > 1:
    return results
  return results[0]
