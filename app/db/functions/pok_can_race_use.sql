CREATE FUNCTION `pok_can_race_use`(p_races_mask INT, p_race_id INT)
RETURNS TINYINT(1)
DETERMINISTIC
NO SQL
BEGIN
  IF p_races_mask IS NULL OR p_race_id IS NULL OR p_race_id <= 0 THEN
    RETURN 0;
  END IF;
  RETURN (p_races_mask & (1 << (p_race_id - 1))) <> 0;
END
