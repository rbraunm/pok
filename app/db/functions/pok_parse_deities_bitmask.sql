CREATE FUNCTION `pok_parse_deities_bitmask`(p_mask BIGINT)
RETURNS TEXT
DETERMINISTIC
READS SQL DATA
BEGIN
  DECLARE v_out TEXT;
  DECLARE v_base INT;           -- smallest deity id > 200
  DECLARE v_cnt  INT;           -- number of deities > 200
  DECLARE v_all_mask BIGINT UNSIGNED;
  DECLARE v_masked   BIGINT UNSIGNED;

  IF p_mask IS NULL OR p_mask = 0 THEN
    RETURN '';
  END IF;

  SELECT MIN(id), COUNT(*)
    INTO v_base, v_cnt
  FROM pok_eqemu_deities
  WHERE id > 200;

  IF v_base IS NULL OR v_cnt = 0 THEN
    RETURN '';
  END IF;

  -- Build the “all” mask from how many rows exist
  SET v_all_mask = ((CAST(1 AS UNSIGNED) << v_cnt) - 1);
  SET v_masked   = (CAST(p_mask AS UNSIGNED) & v_all_mask);

  -- If all known deity bits are present, show "All"
  IF v_masked = v_all_mask THEN
    RETURN 'All';
  END IF;

  -- Otherwise list matching short_names in id order
  SELECT GROUP_CONCAT(d.short_name ORDER BY d.id SEPARATOR ' ')
    INTO v_out
  FROM pok_eqemu_deities AS d
  WHERE d.id > 200
    AND (v_masked & (CAST(1 AS UNSIGNED) << (d.id - v_base))) <> 0;

  RETURN COALESCE(v_out, '');
END