CREATE FUNCTION `parse_ldon_theme_bitmask`(p_mask INT)
RETURNS TEXT
DETERMINISTIC
READS SQL DATA
BEGIN
  DECLARE v_out TEXT;
  DECLARE v_all INT;

  IF p_mask IS NULL OR p_mask = 0 THEN
    RETURN '';
  END IF;

  -- Build ALL mask from any LDoN theme rows present (no upper bound)
  SELECT COALESCE(BIT_OR(1 << (t.ldon_theme_id - 1)), 0)
    INTO v_all
  FROM eqemu_currency_types t
  WHERE t.npc_class_id = 61
    AND t.ldon_theme_id IS NOT NULL
    AND t.ldon_theme_id > 0;

  IF v_all <> 0 AND p_mask = v_all THEN
    RETURN 'ALL';
  END IF;

  -- List theme names present in the mask (ordered by theme id)
  SELECT GROUP_CONCAT(
           TRIM(
             CASE
               WHEN t.name LIKE 'LDoN Points - %'
                 THEN SUBSTRING(t.name, LENGTH('LDoN Points - ') + 1)
               ELSE t.name
             END
           )
           ORDER BY t.ldon_theme_id
           SEPARATOR ', '
         )
    INTO v_out
  FROM eqemu_currency_types t
  WHERE t.npc_class_id = 61
    AND t.ldon_theme_id IS NOT NULL
    AND t.ldon_theme_id > 0
    AND (p_mask & (1 << (t.ldon_theme_id - 1))) <> 0;

  RETURN COALESCE(v_out, '');
END
