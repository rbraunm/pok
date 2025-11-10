CREATE FUNCTION `parse_faction_level_name`(p_value INT)
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
