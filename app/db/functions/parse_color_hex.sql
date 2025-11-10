CREATE FUNCTION `parse_color_hex`(p_color INT UNSIGNED)
RETURNS VARCHAR(7)
DETERMINISTIC
NO SQL
SQL SECURITY INVOKER
BEGIN
  IF p_color IS NULL OR p_color = 0 THEN
    RETURN '';
  END IF;

  RETURN CONCAT(
    '#',
    LPAD(HEX((p_color >> 16) & 255), 2, '0'),  -- RR
    LPAD(HEX((p_color >>  8) & 255), 2, '0'),  -- GG
    LPAD(HEX( p_color        & 255), 2, '0')   -- BB
  );
END
