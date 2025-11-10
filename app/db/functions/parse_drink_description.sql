CREATE FUNCTION `parse_drink_description`(p_itemtype INT, p_casttime INT)
RETURNS VARCHAR(64)
DETERMINISTIC
NO SQL
SQL SECURITY INVOKER
BEGIN
IF p_itemtype <> 15 OR p_casttime <= 0 THEN RETURN ''; END IF;
IF p_casttime BETWEEN 1 AND 5 THEN RETURN 'This is a whistle wetter.';
ELSEIF p_casttime BETWEEN 6 AND 20 THEN RETURN 'This is a drink.';
ELSEIF p_casttime BETWEEN 21 AND 30 THEN RETURN 'This is a refreshing drink.';
ELSEIF p_casttime BETWEEN 31 AND 40 THEN RETURN 'This is a lasting drink!';
ELSEIF p_casttime BETWEEN 41 AND 50 THEN RETURN 'This is a flowing drink!';
ELSEIF p_casttime BETWEEN 51 AND 60 THEN RETURN 'This is a enduring drink!';
ELSEIF p_casttime >= 61 THEN RETURN 'This is a miraculous drink!';
ELSE RETURN '';
END IF;

END
