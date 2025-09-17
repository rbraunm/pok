import sys
import re
from applogging import get_logger
from db import DB_PREFIX

logger = get_logger(__name__)

FUNCTION_SQL = [
  f"""
CREATE FUNCTION {DB_PREFIX}_parse_npc_abilities(sa TEXT, p_category VARCHAR(16))
RETURNS TEXT
DETERMINISTIC
READS SQL DATA
BEGIN
  DECLARE s TEXT;
  DECLARE token TEXT;
  DECLARE id_text TEXT;
  DECLARE ability_id INT;
  DECLARE result TEXT DEFAULT NULL;
  DECLARE seen_ids TEXT DEFAULT '';
  DECLARE delim_pos INT;
  DECLARE caret_pos INT;
  DECLARE ability_name VARCHAR(64);
  DECLARE matched INT;
  DECLARE loop_guard INT DEFAULT 0;
  DECLARE v_category VARCHAR(16);

  -- Normalize category
  SET v_category = TRIM(IFNULL(p_category, ''));

  IF v_category <> '' AND v_category NOT IN ('offense','defense','behavior','immunity') THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Invalid category';
  END IF;

  -- Null/blank input => no abilities
  IF sa IS NULL OR TRIM(sa) = '' OR UPPER(TRIM(sa)) = 'NULL' THEN
    RETURN NULL;
  END IF;

  SET s = sa;

  parse_loop: LOOP
    SET loop_guard = loop_guard + 1;
    IF loop_guard > 512 THEN LEAVE parse_loop; END IF;

    -- Split on ^
    SET caret_pos = LOCATE('^', s);
    IF caret_pos > 0 THEN
      SET token = TRIM(SUBSTRING(s, 1, caret_pos - 1));
      SET s     = SUBSTRING(s, caret_pos + 1);
    ELSE
      SET token = TRIM(s);
      SET s     = '';
    END IF;

    IF token = '' THEN
      IF s = '' THEN LEAVE parse_loop; ELSE ITERATE parse_loop; END IF;
    END IF;

    -- Take numeric id before first comma (e.g., '21,1' -> 21)
    SET delim_pos = LOCATE(',', token);
    SET id_text   = TRIM(IF(delim_pos > 0, SUBSTRING(token, 1, delim_pos - 1), token));

    IF id_text REGEXP '^[0-9]+$' THEN
      SET ability_id = CAST(id_text AS UNSIGNED);

      -- Only process once per ability id
      IF ability_id > 0 AND FIND_IN_SET(ability_id, seen_ids) = 0 THEN
        -- Reset before SELECT; otherwise stale values cause duplicates
        SET ability_name = NULL;

        SELECT display_name
          INTO ability_name
        FROM {DB_PREFIX}_eqemu_special_abilities
        WHERE id = ability_id
          AND (v_category = '' OR category = v_category)
        LIMIT 1;

        SET matched = ROW_COUNT();

        IF matched > 0 AND ability_name IS NOT NULL THEN
          SET seen_ids = IF(seen_ids = '', id_text, CONCAT(seen_ids, ',', id_text));
          SET result   = IFNULL(result, '');
          SET result   = IF(result = '', ability_name, CONCAT(result, ', ', ability_name));
        END IF;
      END IF;
    END IF;

    IF s = '' THEN LEAVE parse_loop; END IF;
  END LOOP;

  RETURN result;
END
""",
  f"""
CREATE FUNCTION {DB_PREFIX}_parse_faction_value(p_value INT)
RETURNS VARCHAR(32)
DETERMINISTIC
NO SQL
BEGIN
  IF p_value IS NULL THEN
    RETURN NULL;
  END IF;

  IF p_value >= 1100 THEN
    RETURN 'Ally';
  ELSEIF p_value >= 750 THEN
    RETURN 'Warmly';
  ELSEIF p_value >= 500 THEN
    RETURN 'Kindly';
  ELSEIF p_value >= 100 THEN
    RETURN 'Amiable';
  ELSEIF p_value >= 0 THEN
    RETURN 'Indifferent';
  ELSEIF p_value >= -100 THEN
    RETURN 'Apprehensive';
  ELSEIF p_value >= -500 THEN
    RETURN 'Dubious';
  ELSEIF p_value >= -750 THEN
    RETURN 'Threateningly';
  ELSE
    RETURN 'Ready to Attack';
  END IF;
END
""",
  f"""
CREATE FUNCTION {DB_PREFIX}_parse_classes_bitmask(p_mask INT)
RETURNS TEXT
DETERMINISTIC
READS SQL DATA
BEGIN
  DECLARE v_out TEXT;

  IF p_mask = 65535 THEN
    RETURN 'ALL';
  END IF;

  IF p_mask IS NULL OR p_mask = 0 THEN
    RETURN '';
  END IF;

  SELECT GROUP_CONCAT(c.short_name ORDER BY c.id SEPARATOR ' ')
    INTO v_out
  FROM {DB_PREFIX}_eqemu_classes c
  WHERE c.category = 'player_class'
    AND (p_mask & (1 << (c.id - 1))) <> 0;

  RETURN COALESCE(v_out, '');
END
""",
]

def _drop_prefixed_functions(cur):
  cur.execute(
    """
    SELECT ROUTINE_NAME
    FROM information_schema.routines
    WHERE ROUTINE_SCHEMA = DATABASE()
      AND ROUTINE_TYPE = 'FUNCTION'
      AND LEFT(ROUTINE_NAME, CHAR_LENGTH(CONCAT(%s, '_'))) = CONCAT(%s, '_')
    """,
    (DB_PREFIX, DB_PREFIX)
  )
  for row in cur.fetchall() or []:
    name = row["ROUTINE_NAME"] if isinstance(row, dict) else row[0]
    cur.execute(f"DROP FUNCTION IF EXISTS `{name}`")
    logger.info(f"Dropped function `{name}`")

def initializeFunctions(db):
  logger.info("Initializing functions...")
  created = 0
  with db.cursor() as cur:
    cur.execute(
      """
      SELECT COUNT(*) AS cnt
      FROM information_schema.routines
      WHERE ROUTINE_SCHEMA = DATABASE()
        AND ROUTINE_TYPE = 'FUNCTION'
        AND LEFT(ROUTINE_NAME, CHAR_LENGTH(CONCAT(%s, '_'))) = CONCAT(%s, '_')
      """,
      (DB_PREFIX, DB_PREFIX)
    )
    row = cur.fetchone() or {}
    to_drop = int((row["cnt"] if isinstance(row, dict) else row[0]) or 0)

    _drop_prefixed_functions(cur)

    for sql in FUNCTION_SQL:
      m = re.search(r'CREATE\s+FUNCTION\s+`?([A-Za-z0-9_]+)`?', sql, re.IGNORECASE)
      name = m.group(1) if m else None
      cur.execute(sql)
      created += 1
      logger.info(f"Created function `{name}`" if name else "Created function")

  db.commit()
  logger.info(f"Functions init complete: dropped={to_drop}, created={created}.")
