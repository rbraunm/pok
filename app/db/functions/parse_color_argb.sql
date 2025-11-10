CREATE FUNCTION `parse_color_argb`(p_color INT UNSIGNED)
RETURNS VARCHAR(15)
DETERMINISTIC
NO SQL
SQL SECURITY INVOKER
BEGIN
  IF p_color IS NULL OR p_color = 0 THEN
    RETURN '';
  END IF;

  RETURN CONCAT(
    ((p_color >> 24) & 255), ',',     -- A
    ((p_color >> 16) & 255), ',',     -- R
    ((p_color >>  8) & 255), ',',     -- G
    ( p_color        & 255)           -- B
  );
END
