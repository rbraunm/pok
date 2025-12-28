CREATE TABLE `pok_item_sources`(
  item_id                 INT PRIMARY KEY,
  lootdropEntries         TEXT,
  merchantListEntries     TEXT,
  tradeskillRecipeEntries TEXT,
  questEntries            TEXT,
  KEY `lootdrop_notnull` (`lootdropEntries`(192)),
  KEY `merchant_notnull` (`merchantListEntries`(192)),
  KEY `recipe_notnull` (`tradeskillRecipeEntries`(192)),
  KEY `quest_notnull` (`questEntries`(192)),
  KEY `item_sources_cols` (`lootdropEntries`(192), `merchantListEntries`(192), `tradeskillRecipeEntries`(192), `questEntries`(192))
);

SELECT
  ids.item_id,
  loot.lootdropEntries,
  merch.merchantListEntries,
  trade.tradeskillRecipeEntries,
  NULL AS questEntries
FROM (
  SELECT i.id AS item_id
  FROM items i
  JOIN lootdrop_entries lde ON lde.item_id = i.id
  JOIN loottable_entries le ON lde.lootdrop_id = le.lootdrop_id
  JOIN loottable lt ON le.loottable_id = lt.id
  JOIN npc_types nt ON lt.id = nt.loottable_id
  JOIN spawnentry se ON nt.id = se.npcID
  JOIN spawn2 s2 ON se.spawngroupID = s2.spawngroupID
  JOIN zone z ON s2.zone = z.short_name
  WHERE (se.chance > 0)
    AND (se.min_expansion <= (SELECT rule_value FROM rule_values WHERE rule_name = 'Expansion:CurrentExpansion'))
    AND (se.max_expansion = -1 OR se.max_expansion >= (SELECT rule_value FROM rule_values WHERE rule_name = 'Expansion:CurrentExpansion'))
    AND (s2.min_expansion <= (SELECT rule_value FROM rule_values WHERE rule_name = 'Expansion:CurrentExpansion'))
    AND (s2.max_expansion = -1 OR s2.max_expansion >= (SELECT rule_value FROM rule_values WHERE rule_name = 'Expansion:CurrentExpansion'))
    AND (z.min_expansion  <= (SELECT rule_value FROM rule_values WHERE rule_name = 'Expansion:CurrentExpansion'))
    AND (z.max_expansion  = -1 OR z.max_expansion >= (SELECT rule_value FROM rule_values WHERE rule_name = 'Expansion:CurrentExpansion'))
    AND z.expansion <= (SELECT rule_value FROM rule_values WHERE rule_name = 'Expansion:CurrentExpansion')
  UNION
  SELECT ml.item AS item_id
  FROM merchantlist ml
  JOIN npc_types nt ON nt.merchant_id = ml.merchantid
  JOIN spawnentry se ON nt.id = se.npcID
  JOIN spawn2 s2 ON se.spawngroupID = s2.spawngroupID
  JOIN zone z ON s2.zone = z.short_name
  WHERE (ml.min_expansion <= (SELECT rule_value FROM rule_values WHERE rule_name = 'Expansion:CurrentExpansion'))
    AND (ml.max_expansion = -1 OR ml.max_expansion >= (SELECT rule_value FROM rule_values WHERE rule_name = 'Expansion:CurrentExpansion'))
    AND (se.chance > 0)
    AND (se.min_expansion <= (SELECT rule_value FROM rule_values WHERE rule_name = 'Expansion:CurrentExpansion'))
    AND (se.max_expansion = -1 OR se.max_expansion >= (SELECT rule_value FROM rule_values WHERE rule_name = 'Expansion:CurrentExpansion'))
    AND (s2.min_expansion <= (SELECT rule_value FROM rule_values WHERE rule_name = 'Expansion:CurrentExpansion'))
    AND (s2.max_expansion = -1 OR s2.max_expansion >= (SELECT rule_value FROM rule_values WHERE rule_name = 'Expansion:CurrentExpansion'))
    AND (z.min_expansion  <= (SELECT rule_value FROM rule_values WHERE rule_name = 'Expansion:CurrentExpansion'))
    AND (z.max_expansion  = -1 OR z.max_expansion >= (SELECT rule_value FROM rule_values WHERE rule_name = 'Expansion:CurrentExpansion'))
    AND z.expansion <= (SELECT rule_value FROM rule_values WHERE rule_name = 'Expansion:CurrentExpansion')
  UNION
  SELECT tre.item_id
  FROM tradeskill_recipe_entries tre
  JOIN tradeskill_recipe tr ON tre.recipe_id = tr.id
  WHERE tre.successcount > 0
    AND tr.enabled = 1
    AND (tr.min_expansion = -1 OR tr.min_expansion <= (SELECT rule_value FROM rule_values WHERE rule_name = 'Expansion:CurrentExpansion'))
    AND (tr.max_expansion = -1 OR tr.max_expansion >= (SELECT rule_value FROM rule_values WHERE rule_name = 'Expansion:CurrentExpansion'))
) AS ids
LEFT JOIN (
  SELECT
    i.id AS item_id,
    GROUP_CONCAT(DISTINCT lde.lootdrop_id ORDER BY lde.lootdrop_id) AS lootdropEntries
  FROM items i
  JOIN lootdrop_entries lde ON lde.item_id = i.id
  JOIN loottable_entries le ON lde.lootdrop_id = le.lootdrop_id
  JOIN loottable lt ON le.loottable_id = lt.id
  JOIN npc_types nt ON lt.id = nt.loottable_id
  JOIN spawnentry se ON nt.id = se.npcID
  JOIN spawn2 s2 ON se.spawngroupID = s2.spawngroupID
  JOIN zone z ON s2.zone = z.short_name
  WHERE (se.chance > 0)
    AND (se.min_expansion <= (SELECT rule_value FROM rule_values WHERE rule_name = 'Expansion:CurrentExpansion'))
    AND (se.max_expansion = -1 OR se.max_expansion >= (SELECT rule_value FROM rule_values WHERE rule_name = 'Expansion:CurrentExpansion'))
    AND (s2.min_expansion <= (SELECT rule_value FROM rule_values WHERE rule_name = 'Expansion:CurrentExpansion'))
    AND (s2.max_expansion = -1 OR s2.max_expansion >= (SELECT rule_value FROM rule_values WHERE rule_name = 'Expansion:CurrentExpansion'))
    AND (z.min_expansion  <= (SELECT rule_value FROM rule_values WHERE rule_name = 'Expansion:CurrentExpansion'))
    AND (z.max_expansion  = -1 OR z.max_expansion >= (SELECT rule_value FROM rule_values WHERE rule_name = 'Expansion:CurrentExpansion'))
    AND z.expansion <= (SELECT rule_value FROM rule_values WHERE rule_name = 'Expansion:CurrentExpansion')
  GROUP BY i.id
) AS loot USING (item_id)
LEFT JOIN (
  SELECT
    ml.item AS item_id,
    GROUP_CONCAT(DISTINCT ml.merchantid ORDER BY ml.merchantid) AS merchantListEntries
  FROM merchantlist ml
  JOIN npc_types nt ON nt.merchant_id = ml.merchantid
  JOIN spawnentry se ON nt.id = se.npcID
  JOIN spawn2 s2 ON se.spawngroupID = s2.spawngroupID
  JOIN zone z ON s2.zone = z.short_name
  WHERE (ml.min_expansion <= (SELECT rule_value FROM rule_values WHERE rule_name = 'Expansion:CurrentExpansion'))
    AND (ml.max_expansion = -1 OR ml.max_expansion >= (SELECT rule_value FROM rule_values WHERE rule_name = 'Expansion:CurrentExpansion'))
    AND (se.chance > 0)
    AND (se.min_expansion <= (SELECT rule_value FROM rule_values WHERE rule_name = 'Expansion:CurrentExpansion'))
    AND (se.max_expansion = -1 OR se.max_expansion >= (SELECT rule_value FROM rule_values WHERE rule_name = 'Expansion:CurrentExpansion'))
    AND (s2.min_expansion <= (SELECT rule_value FROM rule_values WHERE rule_name = 'Expansion:CurrentExpansion'))
    AND (s2.max_expansion = -1 OR s2.max_expansion >= (SELECT rule_value FROM rule_values WHERE rule_name = 'Expansion:CurrentExpansion'))
    AND (z.min_expansion  <= (SELECT rule_value FROM rule_values WHERE rule_name = 'Expansion:CurrentExpansion'))
    AND (z.max_expansion  = -1 OR z.max_expansion >= (SELECT rule_value FROM rule_values WHERE rule_name = 'Expansion:CurrentExpansion'))
    AND z.expansion <= (SELECT rule_value FROM rule_values WHERE rule_name = 'Expansion:CurrentExpansion')
  GROUP BY ml.item
) AS merch USING (item_id)
LEFT JOIN (
  SELECT
    tre.item_id AS item_id,
    GROUP_CONCAT(DISTINCT tre.recipe_id ORDER BY tre.recipe_id) AS tradeskillRecipeEntries
  FROM tradeskill_recipe_entries tre
  JOIN tradeskill_recipe tr ON tre.recipe_id = tr.id
  WHERE tre.successcount > 0
    AND tr.enabled = 1
    AND (tr.min_expansion = -1 OR tr.min_expansion <= (SELECT rule_value FROM rule_values WHERE rule_name = 'Expansion:CurrentExpansion'))
    AND (tr.max_expansion = -1 OR tr.max_expansion >= (SELECT rule_value FROM rule_values WHERE rule_name = 'Expansion:CurrentExpansion'))
  GROUP BY tre.item_id
) AS trade USING (item_id);
