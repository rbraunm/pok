CREATE FUNCTION `pok_parse_time`(p_value DECIMAL(20,6), p_unit VARCHAR(8))
RETURNS VARCHAR(64)
DETERMINISTIC
NO SQL
SQL SECURITY INVOKER
BEGIN
  DECLARE unit_norm VARCHAR(8);
  DECLARE seconds   DECIMAL(20,6);
  DECLARE secs_total BIGINT;
  DECLARE secs_rem   BIGINT;
  DECLARE weeks      BIGINT;
  DECLARE days       BIGINT;
  DECLARE hours      BIGINT;
  DECLARE minutes    BIGINT;
  DECLARE secs       BIGINT;
  DECLARE out_txt    VARCHAR(64);

  IF p_value IS NULL THEN
    RETURN '';
  END IF;

  SET unit_norm = LOWER(TRIM(p_unit));
  IF unit_norm IS NULL OR unit_norm NOT IN ('s','ms') THEN
    RETURN '';
  END IF;

  IF p_value < 0 THEN
    SET p_value = 0;
  END IF;

  SET seconds = IF(unit_norm = 'ms', p_value / 1000.0, p_value);

  IF seconds = 0 THEN
    RETURN 'Instant';
  END IF;

  IF seconds < 60 THEN
    RETURN CONCAT(CAST(ROUND(seconds, 2) AS DECIMAL(20,2)), 's');
  END IF;

  SET secs_total = FLOOR(seconds);

  SET weeks      = FLOOR(secs_total / (7*24*60*60));
  SET secs_rem   = secs_total % (7*24*60*60);

  SET days       = FLOOR(secs_rem / (24*60*60));
  SET secs_rem   = secs_rem % (24*60*60);

  SET hours      = FLOOR(secs_rem / (60*60));
  SET secs_rem   = secs_rem % (60*60);

  SET minutes    = FLOOR(secs_rem / 60);
  SET secs       = secs_rem % 60;

  SET out_txt = '';

  IF weeks > 0 THEN
    SET out_txt = CONCAT(out_txt, weeks, 'w');
  END IF;
  IF days > 0 THEN
    SET out_txt = CONCAT(out_txt, IF(out_txt='','',', '), days, 'd');
  END IF;
  IF hours > 0 THEN
    SET out_txt = CONCAT(out_txt, IF(out_txt='','',', '), hours, 'h');
  END IF;
  IF minutes > 0 THEN
    SET out_txt = CONCAT(out_txt, IF(out_txt='','',', '), minutes, 'm');
  END IF;
  IF secs > 0 THEN
    SET out_txt = CONCAT(out_txt, IF(out_txt='','',', '), secs, 's');
  END IF;

  RETURN out_txt;
END
