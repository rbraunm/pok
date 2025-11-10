CREATE TABLE `eqemu_lore_groups` (
  id INT UNSIGNED PRIMARY KEY,
  group_size INT UNSIGNED NOT NULL,
  `name` VARCHAR(64) NOT NULL
) COMMENT='Lore groups';

SELECT
  g.lore_group_id     AS id,
  g.group_size        AS group_size,
  TRIM(
    CASE
      -- Strip " Mk. <roman|digit>" or " Model <roman|digit>"
      WHEN TRIM(m.Name) REGEXP ' Mk\\.?[[:space:]]*([IVXLCDM]+|[0-9]+)$'
        THEN TRIM(SUBSTRING_INDEX(TRIM(m.Name), ' Mk', 1))
      WHEN TRIM(m.Name) REGEXP ' Model[[:space:]]*([IVXLCDM]+|[0-9]+)$'
        THEN TRIM(SUBSTRING_INDEX(TRIM(m.Name), ' Model', 1))

      -- Strip TWO trailing Roman tokens (I–L), e.g., "… XXI II"
      WHEN (
        CASE
          WHEN TRIM(m.Name) REGEXP ' Mk\\.?[[:space:]]*([IVXLCDM]+|[0-9]+)$'
            THEN TRIM(SUBSTRING_INDEX(TRIM(m.Name), ' Mk', 1))
          WHEN TRIM(m.Name) REGEXP ' Model[[:space:]]*([IVXLCDM]+|[0-9]+)$'
            THEN TRIM(SUBSTRING_INDEX(TRIM(m.Name), ' Model', 1))
          ELSE TRIM(m.Name)
        END
      ) REGEXP '[[:space:]](L|XL|X{0,3}(IX|IV|V?I{0,3}))[[:space:]](L|XL|X{0,3}(IX|IV|V?I{0,3}))$'
        THEN TRIM(
               SUBSTRING(
                 (
                   CASE
                     WHEN TRIM(m.Name) REGEXP ' Mk\\.?[[:space:]]*([IVXLCDM]+|[0-9]+)$'
                       THEN TRIM(SUBSTRING_INDEX(TRIM(m.Name), ' Mk', 1))
                     WHEN TRIM(m.Name) REGEXP ' Model[[:space:]]*([IVXLCDM]+|[0-9]+)$'
                       THEN TRIM(SUBSTRING_INDEX(TRIM(m.Name), ' Model', 1))
                     ELSE TRIM(m.Name)
                   END
                 ),
                 1,
                 LENGTH(
                   CASE
                     WHEN TRIM(m.Name) REGEXP ' Mk\\.?[[:space:]]*([IVXLCDM]+|[0-9]+)$'
                       THEN TRIM(SUBSTRING_INDEX(TRIM(m.Name), ' Mk', 1))
                     WHEN TRIM(m.Name) REGEXP ' Model[[:space:]]*([IVXLCDM]+|[0-9]+)$'
                       THEN TRIM(SUBSTRING_INDEX(TRIM(m.Name), ' Model', 1))
                     ELSE TRIM(m.Name)
                   END
                 )
                 - CHAR_LENGTH(SUBSTRING_INDEX(
                     (
                       CASE
                         WHEN TRIM(m.Name) REGEXP ' Mk\\.?[[:space:]]*([IVXLCDM]+|[0-9]+)$'
                           THEN TRIM(SUBSTRING_INDEX(TRIM(m.Name), ' Mk', 1))
                         WHEN TRIM(m.Name) REGEXP ' Model[[:space:]]*([IVXLCDM]+|[0-9]+)$'
                           THEN TRIM(SUBSTRING_INDEX(TRIM(m.Name), ' Model', 1))
                         ELSE TRIM(m.Name)
                       END
                     ), ' ', -2)) - 1
               )
             )

      -- Strip ONE trailing Roman token (I–L)
      WHEN (
        CASE
          WHEN TRIM(m.Name) REGEXP ' Mk\\.?[[:space:]]*([IVXLCDM]+|[0-9]+)$'
            THEN TRIM(SUBSTRING_INDEX(TRIM(m.Name), ' Mk', 1))
          WHEN TRIM(m.Name) REGEXP ' Model[[:space:]]*([IVXLCDM]+|[0-9]+)$'
            THEN TRIM(SUBSTRING_INDEX(TRIM(m.Name), ' Model', 1))
          ELSE TRIM(m.Name)
        END
      ) REGEXP '[[:space:]](L|XL|X{0,3}(IX|IV|V?I{0,3}))$'
        THEN TRIM(
               SUBSTRING(
                 (
                   CASE
                     WHEN TRIM(m.Name) REGEXP ' Mk\\.?[[:space:]]*([IVXLCDM]+|[0-9]+)$'
                       THEN TRIM(SUBSTRING_INDEX(TRIM(m.Name), ' Mk', 1))
                     WHEN TRIM(m.Name) REGEXP ' Model[[:space:]]*([IVXLCDM]+|[0-9]+)$'
                       THEN TRIM(SUBSTRING_INDEX(TRIM(m.Name), ' Model', 1))
                     ELSE TRIM(m.Name)
                   END
                 ),
                 1,
                 LENGTH(
                   CASE
                     WHEN TRIM(m.Name) REGEXP ' Mk\\.?[[:space:]]*([IVXLCDM]+|[0-9]+)$'
                       THEN TRIM(SUBSTRING_INDEX(TRIM(m.Name), ' Mk', 1))
                     WHEN TRIM(m.Name) REGEXP ' Model[[:space:]]*([IVXLCDM]+|[0-9]+)$'
                       THEN TRIM(SUBSTRING_INDEX(TRIM(m.Name), ' Model', 1))
                     ELSE TRIM(m.Name)
                   END
                 )
                 - CHAR_LENGTH(SUBSTRING_INDEX(
                     (
                       CASE
                         WHEN TRIM(m.Name) REGEXP ' Mk\\.?[[:space:]]*([IVXLCDM]+|[0-9]+)$'
                           THEN TRIM(SUBSTRING_INDEX(TRIM(m.Name), ' Mk', 1))
                         WHEN TRIM(m.Name) REGEXP ' Model[[:space:]]*([IVXLCDM]+|[0-9]+)$'
                           THEN TRIM(SUBSTRING_INDEX(TRIM(m.Name), ' Model', 1))
                         ELSE TRIM(m.Name)
                       END
                     ), ' ', -1)) - 1
               )
             )

      ELSE TRIM(m.Name)
    END
  ) AS `name`
FROM (
  SELECT
    i.loregroup AS lore_group_id,
    COUNT(*)    AS group_size,
    MAX(i.id)   AS example_item_id
  FROM items i
  WHERE i.loregroup > 0
  GROUP BY i.loregroup
) AS g
JOIN items m
  ON m.id = g.example_item_id
ORDER BY g.lore_group_id ASC;
