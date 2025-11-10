CREATE FUNCTION `parse_classes_bitmask`(p_mask INT)
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
  FROM pok_eqemu_classes c
  WHERE c.category = 'player_class'
    AND (p_mask & (1 << (c.id - 1))) <> 0;

  RETURN COALESCE(v_out, '');
END
