CREATE TABLE `pok_eqemu_evolution_lines` (
  id INT UNSIGNED PRIMARY KEY,
  group_size INT UNSIGNED NOT NULL,
  `name` VARCHAR(64) NOT NULL
) COMMENT='Evolution lines';

SELECT
  g.evolve_group_id   AS id,
  g.group_size        AS group_size,
  TRIM(
    CASE
      -- Trim " Mk. <roman|digit>" or " Model <roman|digit>" at end
      WHEN TRIM(m.Name) REGEXP ' Mk\\.?[[:space:]]*([IVXLCDM]+|[0-9]+)$'
        THEN TRIM(SUBSTRING_INDEX(TRIM(m.Name), ' Mk', 1))
      WHEN TRIM(m.Name) REGEXP ' Model[[:space:]]*([IVXLCDM]+|[0-9]+)$'
        THEN TRIM(SUBSTRING_INDEX(TRIM(m.Name), ' Model', 1))

      -- Trim two trailing Roman tokens (I–L), e.g., "… XXI II"
      WHEN TRIM(m.Name) REGEXP '[[:space:]](L|XL|X{0,3}(IX|IV|V?I{0,3}))[[:space:]](L|XL|X{0,3}(IX|IV|V?I{0,3}))$'
        THEN TRIM(SUBSTRING(TRIM(m.Name), 1,
               LENGTH(TRIM(m.Name)) - CHAR_LENGTH(SUBSTRING_INDEX(TRIM(m.Name), ' ', -2)) - 1))

      -- Or one trailing Roman token (I–L)
      WHEN TRIM(m.Name) REGEXP '[[:space:]](L|XL|X{0,3}(IX|IV|V?I{0,3}))$'
        THEN TRIM(SUBSTRING(TRIM(m.Name), 1,
               LENGTH(TRIM(m.Name)) - CHAR_LENGTH(SUBSTRING_INDEX(TRIM(m.Name), ' ', -1)) - 1))

      ELSE TRIM(m.Name)
    END
  ) AS `name`
FROM (
  SELECT
    i.evoid   AS evolve_group_id,
    COUNT(*)  AS group_size,
    MAX(i.id) AS example_item_id
  FROM items i
  WHERE i.evoid > 0
  GROUP BY i.evoid
) AS g
JOIN items m
  ON m.id = g.example_item_id
ORDER BY g.evolve_group_id ASC;
