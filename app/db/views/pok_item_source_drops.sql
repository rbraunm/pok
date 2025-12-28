SELECT
  lde.item_id                                   AS item_id,
  nt.id                                         AS npc_id,

  -- Per-entry (lootdrop_entries) controls
  lde.chance                                    AS drop_chance,
  lde.trivial_min_level                         AS drop_trivial_min_level,
  lde.trivial_max_level                         AS drop_trivial_max_level,
  lde.npc_min_level                             AS drop_npc_min_level,
  lde.npc_max_level                             AS drop_npc_max_level,
  lt.id                                         AS drop_table_id,
  lt.name                                       AS drop_table_name,
  ld.id                                         AS drop_table_drop_id,
  ld.name                                       AS drop_table_drop_name,
  lde.lootdrop_id                               AS drop_id,
  lde.multiplier                                AS drop_multiplier,
  lde.disabled_chance                           AS drop_disabled_chance,

  -- Loottable->Lootdrop edge (per-roll) controls
  le.multiplier                                 AS drop_rolls_per_kill,      -- number of lootdrop rolls per kill (ignoring global loot multiplier)
  le.probability                                AS drop_chance_per_roll,     -- % chance this lootdrop is rolled on a given loottable roll
  le.mindrop                                    AS drop_items_min_per_roll,
  le.droplimit                                  AS drop_items_max_per_roll,

  -- Selection mode helper (matches EQEmu logic branches)
  CASE
    WHEN COALESCE(le.mindrop,0) > 0 AND COALESCE(le.droplimit,0) > 0 THEN 'weighted+capped'
    WHEN COALESCE(le.mindrop,0) > 0 THEN 'weighted'
    WHEN COALESCE(le.droplimit,0) > 0 THEN 'capped'
    ELSE 'independent'
  END                                           AS drop_selection_mode,

  -- Joint chance in a *single* loottable roll:
  --   P(we roll this lootdrop) * P(this entry passes its chance check)
  -- Does not account for entry multiplier or multiple loottable rolls.
  ROUND(
    (COALESCE(le.probability, 0) * COALESCE(lde.chance, 0)) / 100,
    2
  )                                             AS drop_calculated_chance_simple,

  -- Approximate per-kill chance (independent mode only) that this entry appears at least once,
  -- assuming: global loot multiplier = 1, and ignoring content/level gates.
  --
  -- Let:
  --   p_roll      = normalized le.probability (0–1)
  --   p_entry     = normalized lde.chance (0–1)
  --   M_entry     = max(1, lde.multiplier)         -- tries per call for this entry
  --   M_table     = max(1, le.multiplier)          -- lootdrop rolls per kill
  --   p_item_call = 1 - (1 - p_entry)^M_entry      -- chance entry appears in one lootdrop call
  --   p_kill      = 1 - (1 - p_roll * p_item_call)^M_table
  --
  CASE
    WHEN COALESCE(le.mindrop,0) = 0
         AND COALESCE(le.droplimit,0) = 0
         AND le.probability IS NOT NULL
         AND lde.chance     IS NOT NULL
    THEN ROUND(
      100.0 * (
        1 - POW(
          1 - (
            -- p_roll * p_item_call
            (LEAST(100.0, GREATEST(0.0, le.probability)) / 100.0)
            * (
                1 - POW(
                  1 - (LEAST(100.0, GREATEST(0.0, lde.chance)) / 100.0),
                  GREATEST(1, COALESCE(lde.multiplier, 1))
                )
              )
          ),
          GREATEST(1, COALESCE(le.multiplier, 1))
        )
      ),
      2
    )
    ELSE NULL
  END                                           AS drop_calculated_chance_per_kill,

  -- Theoretical item count range helper:
  -- This is a min–max *possible* number of copies this entry can produce per kill
  -- under the configured mindrop/droplimit/multipliers, ignoring probability.
  CASE
    WHEN COALESCE(le.mindrop,0) = 0
         AND COALESCE(le.droplimit,0) = 0 THEN
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
        GREATEST(
          1,
          COALESCE(
            NULLIF(le.droplimit,0),
            GREATEST(1, COALESCE(le.multiplier,1))
          )
        )
      )
  END                                           AS drop_calculated_item_amount_range,

  -- Era/content gates: raw values for all three layers
  lt.min_expansion                              AS loottable_min_expansion,
  lt.max_expansion                              AS loottable_max_expansion,
  lt.content_flags                              AS loottable_content_flags,
  lt.content_flags_disabled                     AS loottable_content_flags_disabled,

  ld.min_expansion                              AS lootdrop_min_expansion,
  ld.max_expansion                              AS lootdrop_max_expansion,
  ld.content_flags                              AS lootdrop_content_flags,
  ld.content_flags_disabled                     AS lootdrop_content_flags_disabled,

  lde.min_expansion                             AS drop_min_expansion,
  lde.max_expansion                             AS drop_max_expansion,
  lde.content_flags                             AS drop_content_flags,
  lde.content_flags_disabled                    AS drop_content_flags_disabled,

  -- Era/content gates: helper booleans vs current expansion (expansion only, flags left to caller)
  pok_get_eqemu_expansion()                     AS eqemu_current_expansion_id,

  CASE
    WHEN lt.min_expansion <= pok_get_eqemu_expansion()
         AND (lt.max_expansion = -1 OR lt.max_expansion >= pok_get_eqemu_expansion())
    THEN 1 ELSE 0
  END                                           AS loottable_expansion_gate_passes,

  CASE
    WHEN ld.min_expansion <= pok_get_eqemu_expansion()
         AND (ld.max_expansion = -1 OR ld.max_expansion >= pok_get_eqemu_expansion())
    THEN 1 ELSE 0
  END                                           AS lootdrop_expansion_gate_passes,

  CASE
    WHEN lde.min_expansion <= pok_get_eqemu_expansion()
         AND (lde.max_expansion = -1 OR lde.max_expansion >= pok_get_eqemu_expansion())
    THEN 1 ELSE 0
  END                                           AS drop_expansion_gate_passes,

  -- Spawn gate: does this NPC actually have any spawn variants?
  EXISTS (
    SELECT 1
    FROM pok_spawn_variants pv
    WHERE pv.npc_id = nt.id
  )                                             AS npc_has_spawn_variants

FROM lootdrop_entries lde
JOIN loottable_entries le   ON lde.lootdrop_id   = le.lootdrop_id
JOIN loottable lt           ON le.loottable_id   = lt.id
JOIN lootdrop ld            ON lde.lootdrop_id   = ld.id
JOIN npc_types nt           ON lt.id             = nt.loottable_id;
