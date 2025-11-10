CREATE FUNCTION `get_eqemu_expansion`() RETURNS INT
READS SQL DATA
NOT DETERMINISTIC
BEGIN
  DECLARE v INT DEFAULT NULL;
  -- if the SELECT returns 0 rows, avoid an exception and keep v as NULL
  DECLARE CONTINUE HANDLER FOR NOT FOUND SET v = NULL;

  SELECT CAST(rule_value AS SIGNED)
    INTO v
    FROM rule_values
   WHERE rule_name = 'Expansion:CurrentExpansion'
   LIMIT 1;

  RETURN IFNULL(v, 0);
END
