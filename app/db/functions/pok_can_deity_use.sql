CREATE FUNCTION `pok_can_deity_use`(p_deity_mask INT, p_deity_id INT)
RETURNS TINYINT(1)
DETERMINISTIC
NO SQL
BEGIN
  IF p_deity_mask IS NULL OR p_deity_id IS NULL OR p_deity_id <= 0 THEN
    RETURN 0;
  END IF;
  RETURN (p_deity_mask & (1 << (p_deity_id - 1))) <> 0;
END
