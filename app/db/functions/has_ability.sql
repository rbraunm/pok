CREATE FUNCTION `has_ability`(p_sa TEXT, p_ability_id INT)
RETURNS TINYINT(1)
DETERMINISTIC
NO SQL
BEGIN
  DECLARE s TEXT;
  DECLARE token TEXT;
  DECLARE id_text TEXT;
  DECLARE delim_pos INT;
  DECLARE caret_pos INT;
  DECLARE parsed_id INT;
  DECLARE loop_guard INT DEFAULT 0;

  IF p_sa IS NULL OR TRIM(p_sa) = '' OR UPPER(TRIM(p_sa)) = 'NULL' THEN
    RETURN 0;
  END IF;

  IF p_ability_id IS NULL OR p_ability_id <= 0 THEN
    RETURN 0;
  END IF;

  SET s = p_sa;

  parse_loop: LOOP
    SET loop_guard = loop_guard + 1;
    IF loop_guard > 512 THEN LEAVE parse_loop; END IF;

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

    SET delim_pos = LOCATE(',', token);
    SET id_text   = TRIM(IF(delim_pos > 0, SUBSTRING(token, 1, delim_pos - 1), token));

    IF id_text REGEXP '^[0-9]+$' THEN
      SET parsed_id = CAST(id_text AS UNSIGNED);
      IF parsed_id = p_ability_id THEN
        RETURN 1;
      END IF;
    END IF;

    IF s = '' THEN LEAVE parse_loop; END IF;
  END LOOP;

  RETURN 0;
END
