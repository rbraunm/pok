import sys
import re
from applogging import get_logger
from db import DB_PREFIX

logger = get_logger(__name__)

VIEW_SQL = [
  f"""
CREATE VIEW {DB_PREFIX}_items_purchased_coin AS
SELECT
  CAST(NULL AS SIGNED) AS item_id,
  'purchased_coin'     AS source_type,
  CAST(NULL AS SIGNED) AS source_id,
  CAST(NULL AS SIGNED) AS source_ref,
  NULL                 AS zone_short,
  NULL                 AS zone_long,
  NULL                 AS extra
WHERE 0
""",
  f"""
CREATE VIEW {DB_PREFIX}_items_ground_spawns AS
SELECT
  CAST(NULL AS SIGNED) AS item_id,
  'ground_spawn'       AS source_type,
  CAST(NULL AS SIGNED) AS source_id,
  CAST(NULL AS SIGNED) AS source_ref,
  NULL                 AS zone_short,
  NULL                 AS zone_long,
  NULL                 AS extra
WHERE 0
""",
  f"""
CREATE VIEW {DB_PREFIX}_items_foraged AS
SELECT
  CAST(NULL AS SIGNED) AS item_id,
  'foraged'            AS source_type,
  CAST(NULL AS SIGNED) AS source_id,
  CAST(NULL AS SIGNED) AS source_ref,
  NULL                 AS zone_short,
  NULL                 AS zone_long,
  NULL                 AS extra
WHERE 0
""",
  f"""
CREATE VIEW {DB_PREFIX}_items_fished AS
SELECT
  CAST(NULL AS SIGNED) AS item_id,
  'fished'             AS source_type,
  CAST(NULL AS SIGNED) AS source_id,
  CAST(NULL AS SIGNED) AS source_ref,
  NULL                 AS zone_short,
  NULL                 AS zone_long,
  NULL                 AS extra
WHERE 0
""",
  f"""
CREATE VIEW {DB_PREFIX}_items_starting_items AS
SELECT
  CAST(NULL AS SIGNED) AS item_id,
  'starting_item'      AS source_type,
  CAST(NULL AS SIGNED) AS source_id,
  CAST(NULL AS SIGNED) AS source_ref,
  NULL                 AS zone_short,
  NULL                 AS zone_long,
  NULL                 AS extra
WHERE 0
""",
  f"""
CREATE VIEW {DB_PREFIX}_items_crafted AS
SELECT
  CAST(NULL AS SIGNED) AS item_id,
  'crafted'            AS source_type,
  CAST(NULL AS SIGNED) AS source_id,
  CAST(NULL AS SIGNED) AS source_ref,
  NULL                 AS zone_short,
  NULL                 AS zone_long,
  NULL                 AS extra
WHERE 0
""",
  f"""
CREATE VIEW {DB_PREFIX}_items_npc_loot AS
SELECT
  CAST(NULL AS SIGNED) AS item_id,
  'npc_loot'           AS source_type,
  CAST(NULL AS SIGNED) AS source_id,
  CAST(NULL AS SIGNED) AS source_ref,
  NULL                 AS zone_short,
  NULL                 AS zone_long,
  NULL                 AS extra
WHERE 0
""",
  f"""
CREATE VIEW {DB_PREFIX}_items_global_loot AS
SELECT
  CAST(NULL AS SIGNED) AS item_id,
  'global_loot'        AS source_type,
  CAST(NULL AS SIGNED) AS source_id,
  CAST(NULL AS SIGNED) AS source_ref,
  NULL                 AS zone_short,
  NULL                 AS zone_long,
  NULL                 AS extra
WHERE 0
""",
  f"""
CREATE VIEW {DB_PREFIX}_items_object_chest_loot AS
SELECT
  CAST(NULL AS SIGNED) AS item_id,
  'object_chest_loot'  AS source_type,
  CAST(NULL AS SIGNED) AS source_id,
  CAST(NULL AS SIGNED) AS source_ref,
  NULL                 AS zone_short,
  NULL                 AS zone_long,
  NULL                 AS extra
WHERE 0
""",
  f"""
CREATE VIEW {DB_PREFIX}_items_purchased_alt_currency AS
SELECT
  CAST(NULL AS SIGNED) AS item_id,
  'purchased_alt_currency' AS source_type,
  CAST(NULL AS SIGNED) AS source_id,
  CAST(NULL AS SIGNED) AS source_ref,
  NULL                 AS zone_short,
  NULL                 AS zone_long,
  NULL                 AS extra
WHERE 0
""",
  f"""
CREATE VIEW {DB_PREFIX}_items_task_rewards AS
SELECT
  CAST(NULL AS SIGNED) AS item_id,
  'task_reward'        AS source_type,
  CAST(NULL AS SIGNED) AS source_id,
  CAST(NULL AS SIGNED) AS source_ref,
  NULL                 AS zone_short,
  NULL                 AS zone_long,
  NULL                 AS extra
WHERE 0
""",
  f"""
CREATE VIEW {DB_PREFIX}_items_summoned_by_spells AS
SELECT
  CAST(NULL AS SIGNED) AS item_id,
  'summoned_by_spells' AS source_type,
  CAST(NULL AS SIGNED) AS source_id,
  CAST(NULL AS SIGNED) AS source_ref,
  NULL                 AS zone_short,
  NULL                 AS zone_long,
  NULL                 AS extra
WHERE 0
""",
  f"""
CREATE VIEW {DB_PREFIX}_items_quest_granted AS
SELECT
  CAST(NULL AS SIGNED) AS item_id,
  'quest_granted'      AS source_type,
  CAST(NULL AS SIGNED) AS source_id,
  CAST(NULL AS SIGNED) AS source_ref,
  NULL                 AS zone_short,
  NULL                 AS zone_long,
  NULL                 AS extra
WHERE 0
""",
  f"""
CREATE VIEW {DB_PREFIX}_items_scripted_ground_objects AS
SELECT
  CAST(NULL AS SIGNED) AS item_id,
  'scripted_ground_object' AS source_type,
  CAST(NULL AS SIGNED) AS source_id,
  CAST(NULL AS SIGNED) AS source_ref,
  NULL                 AS zone_short,
  NULL                 AS zone_long,
  NULL                 AS extra
WHERE 0
""",
  f"""
CREATE VIEW {DB_PREFIX}_items_instance_chest_rewards AS
SELECT
  CAST(NULL AS SIGNED) AS item_id,
  'instance_chest_reward' AS source_type,
  CAST(NULL AS SIGNED) AS source_id,
  CAST(NULL AS SIGNED) AS source_ref,
  NULL                 AS zone_short,
  NULL                 AS zone_long,
  NULL                 AS extra
WHERE 0
""",
  f"""
CREATE VIEW {DB_PREFIX}_items_pickpocket AS
SELECT
  CAST(NULL AS SIGNED) AS item_id,
  'pickpocket'         AS source_type,
  CAST(NULL AS SIGNED) AS source_id,
  CAST(NULL AS SIGNED) AS source_ref,
  NULL                 AS zone_short,
  NULL                 AS zone_long,
  NULL                 AS extra
WHERE 0
""",
  f"""
CREATE VIEW {DB_PREFIX}_items_begging AS
SELECT
  CAST(NULL AS SIGNED) AS item_id,
  'begging'            AS source_type,
  CAST(NULL AS SIGNED) AS source_id,
  CAST(NULL AS SIGNED) AS source_ref,
  NULL                 AS zone_short,
  NULL                 AS zone_long,
  NULL                 AS extra
WHERE 0
""",
  f"""
CREATE VIEW {DB_PREFIX}_items_account_claims AS
SELECT
  CAST(NULL AS SIGNED) AS item_id,
  'account_claim'      AS source_type,
  CAST(NULL AS SIGNED) AS source_id,
  CAST(NULL AS SIGNED) AS source_ref,
  NULL                 AS zone_short,
  NULL                 AS zone_long,
  NULL                 AS extra
WHERE 0
""",
]

def _drop_prefixed_views(cur):
  cur.execute(
    """
    SELECT TABLE_NAME
    FROM INFORMATION_SCHEMA.VIEWS
    WHERE TABLE_SCHEMA = DATABASE()
      AND LEFT(TABLE_NAME, CHAR_LENGTH(CONCAT(%s, '_'))) = CONCAT(%s, '_')
    """,
    (DB_PREFIX, DB_PREFIX)
  )
  for row in cur.fetchall() or []:
    name = row["TABLE_NAME"] if isinstance(row, dict) else row[0]
    cur.execute(f"DROP VIEW IF EXISTS `{name}`")
    logger.info(f"Dropped view `{name}`")

def initializeViews(db):
  logger.info("Initializing views...")
  created = 0
  with db.cursor() as cur:
    cur.execute(
      """
      SELECT COUNT(*) AS cnt
      FROM INFORMATION_SCHEMA.VIEWS
      WHERE TABLE_SCHEMA = DATABASE()
        AND LEFT(TABLE_NAME, CHAR_LENGTH(CONCAT(%s, '_'))) = CONCAT(%s, '_')
      """,
      (DB_PREFIX, DB_PREFIX)
    )
    row = cur.fetchone() or {}
    to_drop = int((row["cnt"] if isinstance(row, dict) else row[0]) or 0)

    _drop_prefixed_views(cur)

    for sql in VIEW_SQL:
      m = re.search(r'CREATE\s+VIEW\s+`?([A-Za-z0-9_]+)`?', sql, re.IGNORECASE)
      name = m.group(1) if m else None
      cur.execute(sql)
      created += 1
      logger.info(f"Created view `{name}`" if name else "Created view")

  db.commit()
  logger.info(f"Views init complete: dropped={to_drop}, created={created}.")
