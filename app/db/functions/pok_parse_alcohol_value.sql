CREATE FUNCTION `pok_parse_alcohol_value`(p_itemtype INT, p_casttime INT)
RETURNS INT
DETERMINISTIC
NO SQL
SQL SECURITY INVOKER
BEGIN
IF p_itemtype = 38 AND p_casttime > 0 THEN
  RETURN p_casttime;
END IF;
RETURN NULL;

END
