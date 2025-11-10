SELECT
  lde.item_id                                   AS item_id,

  -- Per-entry (lootdrop_entries) controls
  lde.chance                                    AS drop_chance,
  lde.trivial_min_level                         AS drop_trivial_min_level,
  lde.trivial_max_level                         AS drop_trivial_max_level,
  lde.npc_min_level                             AS drop_npc_min_level,
  lde.npc_max_level                             AS drop_npc_max_level,
  lde.multiplier                                AS drop_multiplier,

  -- Loottable->Lootdrop edge (per-roll) controls
  le.multiplier                                 AS drop_rolls_per_kill,
  le.probability                                AS drop_chance_per_roll,
  le.mindrop                                    AS drop_items_min_per_roll,
  le.droplimit                                  AS drop_items_max_per_roll,

  -- Selection mode helper
  CASE
    WHEN COALESCE(le.mindrop,0) > 0 AND COALESCE(le.droplimit,0) > 0 THEN 'weighted+capped'
    WHEN COALESCE(le.mindrop,0) > 0 THEN 'weighted'
    WHEN COALESCE(le.droplimit,0) > 0 THEN 'capped'
    ELSE 'independent'
  END                                           AS drop_selection_mode,

  -- Simple path (per roll) = roll chance * entry chance
  ROUND((COALESCE(le.probability, 0) * COALESCE(lde.chance, 0)) / 100, 2)
                                               AS drop_calculated_chance_simple,

  -- Per-kill chance for independent selection with multiplier > 0
  CASE
    WHEN COALESCE(le.mindrop,0) = 0 AND COALESCE(le.droplimit,0) = 0
         AND COALESCE(le.multiplier,0) > 0
         AND le.probability IS NOT NULL
         AND lde.chance     IS NOT NULL
    THEN ROUND(
      100.0 * (1 - POW(
        1 - (LEAST(100.0, GREATEST(0.0, le.probability)) / 100.0)
            * (LEAST(100.0, GREATEST(0.0, lde.chance)) / 100.0),
        GREATEST(1, le.multiplier)
      )), 2)
    ELSE NULL
  END                                                         AS drop_calculated_chance_per_kill,

  -- Expected item count range helper (unchanged)
  CASE
    WHEN COALESCE(le.mindrop,0) = 0 AND COALESCE(le.droplimit,0) = 0 THEN
      CASE
        WHEN GREATEST(1, COALESCE(le.multiplier,1)) = 1
          THEN CAST(GREATEST(1, COALESCE(lde.multiplier,1)) AS CHAR)
        ELSE CONCAT(
          GREATEST(1, COALESCE(lde.multiplier,1)), '-',
          GREATEST(1, COALESCE(lde.multiplier,1)) * GREATEST(1, COALESCE(le.multiplier,1))
        )
      END
    ELSE
      CONCAT(
        GREATEST(1, COALESCE(lde.multiplier,1)) * GREATEST(1, COALESCE(le.mindrop,1)),
        '-',
        GREATEST(1, COALESCE(lde.multiplier,1)) *
        GREATEST(1, COALESCE(NULLIF(le.droplimit,0), GREATEST(1, COALESCE(le.multiplier,1))))
      )
  END                                                         AS drop_calculated_item_amount_range,

  -- NPC
  nt.id                                                       AS npc_id,
  nt.name                                                     AS npc_name,
  nt.lastname                                                 AS npc_label,
  nt.level                                                    AS npc_level,
  nt.class                                                    AS npc_class_id,
  pec.name                                                    AS npc_class_name,
  nt.hp                                                       AS npc_hp,
  nt.mindmg                                                   AS npc_mindmg,
  nt.maxdmg                                                   AS npc_maxdmg,
  nt.npc_faction_id                                           AS npc_faction_id,
  fl.name                                                     AS npc_faction_name,
  nt.special_abilities                                        AS npc_ability_ids,
  pok_parse_npc_abilities(nt.special_abilities, 'offense')    AS npc_abilities_offense,
  pok_parse_npc_abilities(nt.special_abilities, 'defense')    AS npc_abilities_defense,
  pok_parse_npc_abilities(nt.special_abilities, 'behavior')   AS npc_abilities_behavior,
  pok_parse_npc_abilities(nt.special_abilities, 'immunity')   AS npc_abilities_immunity,
  nt.raid_target                                              AS npc_raid,
  nt.rare_spawn                                               AS npc_rare

FROM lootdrop_entries        lde
JOIN loottable_entries       le   ON lde.lootdrop_id   = le.lootdrop_id
JOIN loottable               lt   ON le.loottable_id   = lt.id
JOIN lootdrop                ld   ON lde.lootdrop_id   = ld.id
JOIN npc_types               nt   ON lt.id             = nt.loottable_id
LEFT JOIN npc_faction        nf   ON nt.npc_faction_id = nf.id
LEFT JOIN faction_list       fl   ON nf.primaryFaction = fl.id
LEFT JOIN pok_eqemu_classes  pec  ON nt.class          = pec.id

-- Era gates for loot layers only
WHERE (lt.min_expansion <= pok_get_eqemu_expansion())
  AND (lt.max_expansion = -1 OR lt.max_expansion >= pok_get_eqemu_expansion())
  AND (ld.min_expansion <= pok_get_eqemu_expansion())
  AND (ld.max_expansion = -1 OR ld.max_expansion >= pok_get_eqemu_expansion())
  AND EXISTS (
      SELECT 1
      FROM pok_spawn_variants pv
      WHERE pv.npc_id = nt.id
    );
