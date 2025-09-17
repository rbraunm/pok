import sys
import re
from db import DB_PREFIX
from applogging import get_logger

logger = get_logger(__name__)

PROCEDURE_SQL = [
  f"""
CREATE PROCEDURE {DB_PREFIX}_populate_item_sources()
BEGIN
  DECLARE currentExpansion INT;

  -- Get current expansion
  SELECT rule_value INTO currentExpansion
  FROM rule_values
  WHERE rule_name = 'Expansion:CurrentExpansion';

  -- Clear the existing table
  TRUNCATE TABLE {DB_PREFIX}_item_sources;

  -- Insert lootdropEntries
  INSERT INTO {DB_PREFIX}_item_sources (item_id, lootdropEntries)
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
  INSERT INTO {DB_PREFIX}_item_sources (item_id, merchantListEntries)
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
  INSERT INTO {DB_PREFIX}_item_sources (item_id, tradeskillRecipeEntries)
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

  -- Placeholder for questEntries (to be implemented later)
END
""",
]

def _drop_prefixed_procedures(cur):
  cur.execute("""
    SELECT ROUTINE_NAME
    FROM information_schema.routines
    WHERE ROUTINE_SCHEMA = DATABASE()
      AND ROUTINE_TYPE = 'PROCEDURE'
      AND LEFT(ROUTINE_NAME, CHAR_LENGTH(CONCAT(%s, '_'))) = CONCAT(%s, '_')
  """, (DB_PREFIX, DB_PREFIX))
  for r in cur.fetchall() or []:
    name = r["ROUTINE_NAME"] if isinstance(r, dict) else r[0]
    cur.execute(f"DROP PROCEDURE IF EXISTS `{name}`")
    logger.info(f"Dropped procedure `{name}`")

def initializeProcedures(db):
  logger.info("Initializing procedures...")
  created = 0
  with db.cursor() as cur:
    cur.execute(
      """
      SELECT COUNT(*) AS cnt
      FROM information_schema.routines
      WHERE ROUTINE_SCHEMA = DATABASE()
        AND ROUTINE_TYPE = 'PROCEDURE'
        AND LEFT(ROUTINE_NAME, CHAR_LENGTH(CONCAT(%s, '_'))) = CONCAT(%s, '_')
      """,
      (DB_PREFIX, DB_PREFIX)
    )
    row = cur.fetchone() or {}
    to_drop = int((row["cnt"] if isinstance(row, dict) else row[0]) or 0)

    _drop_prefixed_procedures(cur)

    for sql in PROCEDURE_SQL:
      m = re.search(r'CREATE\s+PROCEDURE\s+`?([A-Za-z0-9_]+)`?', sql, re.IGNORECASE)
      name = m.group(1) if m else None
      cur.execute(sql)
      created += 1
      logger.info(f"Created procedure `{name}`" if name else "Created procedure")

  db.commit()
  logger.info(f"Procedures init complete: dropped={to_drop}, created={created}.")

def callStoredProcedure(db, procedureName, args=None, returnAll=False):
  if not procedureName:
    raise ValueError("procedureName is required")
  logger.info(f"Calling stored procedure `{procedureName}`")
  args = tuple(args or ())
  placeholders = ", ".join(["%s"] * len(args))
  sql = f"CALL {procedureName}({placeholders})" if placeholders else f"CALL {procedureName}()"
  results = []
  with db.cursor() as cur:
    cur.execute(sql, args)
    try:
      rows = cur.fetchall()
      if rows:
        results.append(rows)
    except Exception:
      logger.exception("Exception reading first result set")
    while hasattr(cur, "nextset") and cur.nextset():
      try:
        rows = cur.fetchall()
        if rows:
          results.append(rows)
      except Exception:
        logger.exception("Exception reading additional result set")
  db.commit()
  if not results:
    return None
  if returnAll or len(results) > 1:
    return results
  return results[0]

