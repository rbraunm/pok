CREATE FUNCTION `pok_parse_races_bitmask`(p_mask INT)
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

  SELECT GROUP_CONCAT(r.short_name ORDER BY r.id SEPARATOR ' ')
    INTO v_out
  FROM pok_eqemu_races r
  WHERE (p_mask & (1 << (r.id - 1))) <> 0;

  RETURN COALESCE(v_out, '');
END
