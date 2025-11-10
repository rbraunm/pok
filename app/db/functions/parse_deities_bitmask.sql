CREATE FUNCTION `parse_deities_bitmask`(p_mask INT)
RETURNS TEXT
DETERMINISTIC
READS SQL DATA
BEGIN
  DECLARE v_out TEXT;

  IF p_mask IS NULL OR p_mask = 0 THEN
    RETURN '';
  END IF;

  SELECT GROUP_CONCAT(d.short_name ORDER BY d.id SEPARATOR ' ')
    INTO v_out
  FROM pok_eqemu_deities d
  WHERE (p_mask & (1 << (d.id - 1))) <> 0;

  RETURN COALESCE(v_out, '');
END
