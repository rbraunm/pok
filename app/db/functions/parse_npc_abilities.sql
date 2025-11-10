CREATE FUNCTION `parse_npc_abilities`(sa TEXT, p_category VARCHAR(16))
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

        SELECT name
          INTO ability_name
        FROM pok_eqemu_special_abilities
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
