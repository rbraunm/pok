CREATE FUNCTION `parse_augment_types_bitmask`(p_mask BIGINT UNSIGNED)
RETURNS TEXT
DETERMINISTIC
READS SQL DATA
BEGIN
  DECLARE v_out TEXT DEFAULT '';
  DECLARE v_fullmask BIGINT UNSIGNED DEFAULT 0;
  DECLARE v_mask BIGINT UNSIGNED;

  -- normalize input
  SET v_mask = COALESCE(p_mask, 0);

  -- Build dynamic mask covering all known aug types in your table
  SELECT COALESCE(SUM((CAST(1 AS UNSIGNED) << (id - 1))), 0)
    INTO v_fullmask
  FROM pok_eqemu_augment_types;

  IF v_mask = 0 THEN
    RETURN '';
  END IF;

  -- Treat any superset of known bits as ALL (even if extra unknown bits are present)
  IF (v_mask & v_fullmask) = v_fullmask THEN
    RETURN 'ALL';
  END IF;

  -- Otherwise list the known type IDs present in the mask
  SELECT GROUP_CONCAT(CAST(at.id AS CHAR) ORDER BY at.id SEPARATOR ' ')
    INTO v_out
  FROM pok_eqemu_augment_types at
  WHERE (v_mask & (CAST(1 AS UNSIGNED) << (at.id - 1))) <> 0;

  RETURN COALESCE(v_out, '');
END
