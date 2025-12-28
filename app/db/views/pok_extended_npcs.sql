SELECT
  -- Identification & Classification
  n.id                                AS npc_id,
  n.Name                              AS npc_name,
  n.lastname                          AS npc_lastname,
  n.class                             AS npc_class_id,
  nc.name                             AS npc_class_name,
  n.race                              AS npc_race_id,
  nr.name                             AS npc_race_name,
  n.bodytype                          AS npc_bodytype_id,
  nbt.name                            AS npc_bodytype_name,

  -- Spawn Info
  n.level                                 AS npc_min_level,
  IF(n.maxlevel > 0, n.maxlevel, n.level) AS npc_max_level,
  n.scalerate                             AS npc_level_scaling_percent,
  n.scalerate / 100                       AS npc_level_scaling_multiplier,
  n.spawn_limit                           AS npc_spawn_limit,
  n.isquest                               AS npc_is_quest,
  n.rare_spawn                            AS npc_is_rare,
  n.raid_target                           AS npc_is_raid,
  n.exclude                               AS npc_is_excluded,
  n.unique_                               AS npc_is_unique,
  n.fixed                                 AS npc_is_fixed,
  n.version                               AS npc_version,
  n.private_corpse                        AS npc_is_private_corpse,
  n.unique_spawn_by_name                  AS npc_is_unique_spawn_by_name,
  n.ignore_despawn                        AS npc_ignores_despawn,

  -- Faction
  n.npc_faction_id           AS npc_faction_profile_id,
  nf.name                    AS npc_faction_profile_name,
  nf.ignore_primary_assist   AS npc_faction_ignore_primary_assist,

  nf.primaryfaction          AS npc_primary_faction_id,
  pfl.name                   AS npc_primary_faction_name,
  pfl.base                   AS npc_primary_faction_base,

  nfeagg.faction_ids         AS npc_faction_hit_faction_ids,
  nfeagg.faction_names       AS npc_faction_hit_faction_names,
  nfeagg.faction_values      AS npc_faction_hit_values,
  n.faction_amount           AS npc_faction_amount_override,

  -- Basic Stats
  n.hp                      AS npc_hp,
  n.mana                    AS npc_mana,

  n.STR                     AS npc_str,
  n.STA                     AS npc_sta,
  n.DEX                     AS npc_dex,
  n.AGI                     AS npc_agi,
  n._INT                    AS npc_int,
  n.WIS                     AS npc_wis,
  n.CHA                     AS npc_cha,

  n.MR                      AS npc_resist_magic,
  n.FR                      AS npc_resist_fire,
  n.CR                      AS npc_resist_cold,
  n.DR                      AS npc_resist_disease,
  n.PR                      AS npc_resist_poison,
  n.Corrup                  AS npc_resist_corruption,
  n.PhR                     AS npc_resist_physical,

  -- Combat
  n.AC                      AS npc_ac,
  n.ATK                     AS npc_atk,
  n.attack_speed            AS npc_melee_attack_speed,
  n.attack_delay            AS npc_melee_attack_delay,
  n.mindmg                  AS npc_melee_attack_min_damage,
  n.maxdmg                  AS npc_melee_attack_max_damage,
  n.attack_count            AS npc_melee_attack_count,
  n.prim_melee_type         AS npc_primary_attack_skill_id,
  pmt.name                  AS npc_primary_attack_skill_name,
  n.sec_melee_type          AS npc_secondary_attack_skill_id,
  smt.name                  AS npc_secondary_attack_skill_name,
  n.ranged_type             AS npc_ranged_attack_skill_id,
  rt.name                   AS npc_ranged_attack_skill_name,
  n.hp_regen_rate           AS npc_hp_regen_per_tick,
  n.hp_regen_per_second     AS npc_hp_regen_per_second, -- stacks with hp regen per tick
  n.mana_regen_rate         AS npc_mana_regen_per_tick,
  n.Accuracy                AS npc_accuracy,
  n.Avoidance               AS npc_avoidance,
  n.slow_mitigation         AS npc_slow_mitigation,
  n.heroic_strikethrough    AS npc_heroic_strikethrough,

  -- Spells & Abilities
  n.npcspecialattks                                               AS npc_abilities_legacy_string,
  n.special_abilities                                             AS npc_abilities_string,
  pok_parse_npc_abilities_names(n.special_abilities, NULL)        AS npc_abilities_names,
  pok_parse_npc_abilities_categories(n.special_abilities, NULL)   AS npc_abilities_categories,
  pok_parse_npc_abilities_descriptions(n.special_abilities, NULL) AS npc_abilities_descriptions,
  pok_parse_npc_abilities_details(n.special_abilities, NULL)      AS npc_abilities_details,
  n.spellscale                                                    AS npc_spell_damage_scale_percent,
  n.spellscale / 100                                              AS npc_spell_damage_scale_multiplier,
  n.healscale                                                     AS npc_spell_heal_scale_percent,
  n.healscale / 100                                               AS npc_spell_heal_scale_multiplier,

  n.npc_spells_id               AS npc_spell_list_id,
  sl.name                       AS npc_spell_list_name,
  slagg.spell_list_spell_ids    AS npc_spell_list_spell_ids,
  slagg.spell_list_spell_names  AS npc_spell_list_spell_names,

  n.npc_spells_effects_id       AS npc_spell_effects_id,
  se.name                       AS npc_spell_effects_name,
  seagg.spell_effect_ids        AS npc_spell_effects_effect_ids,
  seagg.spell_effect_details    AS npc_spell_effects_effect_details,

  -- Charm Stats
  n.charm_ac                AS npc_charm_ac,
  n.charm_atk               AS npc_charm_atk,
  n.charm_attack_delay      AS npc_charm_delay,
  n.charm_min_dmg           AS npc_charm_min_damage,
  n.charm_max_dmg           AS npc_charm_max_damage,
  n.charm_accuracy_rating   AS npc_charm_accuracy,
  n.charm_avoidance_rating  AS npc_charm_avoidance,

  -- Behavior
  n.npc_aggro               AS npc_aggro_other_npcs,
  n.aggroradius             AS npc_aggro_radius,
  n.always_aggro            AS npc_always_aggro_enabled,
  n.assistradius            AS npc_assist_radius,
  n.see_invis               AS npc_can_see_invis,
  n.see_invis_undead        AS npc_can_see_undead_invis,
  n.see_hide                AS npc_can_see_hide,
  n.see_improved_hide       AS npc_can_see_improved_hide,
  n.walkspeed               AS npc_walk_speed,
  n.runspeed                AS npc_run_speed,
  n.stuck_behavior          AS npc_stuck_behavior_id,
  n.no_target_hotkey        AS npc_no_target_hotkey_enabled,
  n.untargetable            AS npc_is_untargetable,
  n.underwater              AS npc_is_underwater_only,
  n.flymode                 AS npc_fly_mode_id,

  n.emoteid                 AS npc_emote_profile_id,
  emagg.emote_events        AS npc_emote_events,
  emagg.emote_types         AS npc_emote_types,
  emagg.emote_texts         AS npc_emote_texts,

  n.qglobal                 AS npc_qglobal_enabled,

  -- Adventure & Trap
  n.adventure_template_id   AS npc_adventure_template_id,
  n.trap_template           AS npc_trap_template_id,

  -- Flags
  n.isbot                   AS npc_is_bot,
  n.findable                AS npc_is_findable,
  n.trackable               AS npc_is_trackable,
  n.multiquest_enabled      AS npc_legacy_multiquest_enabled,

  -- Appearance
  n.show_name               AS npc_show_name_enabled,
  n.size                    AS npc_size,
  n.gender                  AS npc_gender_id,
  n.face                    AS npc_face_id,
  n.model                   AS npc_model_id,
  n.herosforgemodel         AS npc_heros_forge_model_id,
  n.texture                 AS npc_body_texture_id,
  n.luclin_hairstyle        AS npc_luclin_hair_style_id,
  n.luclin_haircolor        AS npc_luclin_hair_color_id,
  n.luclin_eyecolor         AS npc_luclin_primary_eye_color_id,
  n.luclin_eyecolor2        AS npc_luclin_secondary_eye_color_id,
  n.luclin_beardcolor       AS npc_luclin_beard_color_id,
  n.luclin_beard            AS npc_luclin_beard_style_id,
  n.drakkin_heritage        AS npc_drakkin_heritage_id,
  n.drakkin_tattoo          AS npc_drakkin_tattoo_id,
  n.drakkin_details         AS npc_drakkin_details_id,
  n.helmtexture             AS npc_head_armor_texture_id,
  n.armtexture              AS npc_arm_armor_texture_id,
  n.bracertexture           AS npc_forearm_armor_texture_id,
  n.handtexture             AS npc_hand_armor_texture_id,
  n.legtexture              AS npc_leg_armor_texture_id,
  n.feettexture             AS npc_feet_armor_texture_id,
  n.d_melee_texture1        AS npc_primary_melee_texture_id,
  n.d_melee_texture2        AS npc_secondary_melee_texture_id,
  n.ammo_idfile             AS npc_ammo_id_file,
  n.light                   AS npc_light_value_id,
  n.npc_tint_id             AS npc_armor_tint_profile_id,
  n.armortint_id            AS npc_armor_tint_palette_id,
  n.armortint_red           AS npc_armor_tint_red,
  n.armortint_green         AS npc_armor_tint_green,
  n.armortint_blue          AS npc_armor_tint_blue,

  -- Metadata / misc
  n.peqid                   AS npc_peq_reference_id,
  n.exp_mod                 AS npc_exp_mod

FROM npc_types n
LEFT JOIN pok_eqemu_skills pmt          ON n.prim_melee_type  = pmt.id
LEFT JOIN pok_eqemu_skills smt          ON n.sec_melee_type   = smt.id
LEFT JOIN pok_eqemu_skills rt           ON n.ranged_type      = rt.id
LEFT JOIN pok_eqemu_races nr            ON n.race             = nr.id
LEFT JOIN pok_eqemu_classes nc          ON n.class            = nc.id
LEFT JOIN pok_eqemu_npc_body_types nbt  ON n.bodytype         = nbt.id

-- Spell List
LEFT JOIN npc_spells sl
  ON n.npc_spells_id > 0
 AND n.npc_spells_id = sl.id

LEFT JOIN (
  SELECT
    nse.npc_spells_id,

    GROUP_CONCAT(
      nse.spellid
      ORDER BY nse.priority, nse.spellid
      SEPARATOR '|'
    ) AS spell_list_spell_ids,

    GROUP_CONCAT(
      sn.name
      ORDER BY nse.priority, nse.spellid
      SEPARATOR '|'
    ) AS spell_list_spell_names

  FROM npc_spells_entries AS nse
  JOIN spells_new         AS sn
    ON sn.id = nse.spellid
  GROUP BY
    nse.npc_spells_id
) slagg
  ON slagg.npc_spells_id = sl.id

-- Spell Effects
LEFT JOIN npc_spells_effects se
  ON n.npc_spells_effects_id > 0
 AND n.npc_spells_effects_id = se.id

LEFT JOIN (
  SELECT
    nsee.npc_spells_effects_id,
    GROUP_CONCAT(
      nsee.spell_effect_id
      ORDER BY nsee.id
      SEPARATOR '|'
    ) AS spell_effect_ids,
    GROUP_CONCAT(
      CONCAT(
        nsee.spell_effect_id, ':',
        nsee.se_base, ':',
        nsee.se_limit, ':',
        nsee.se_max
      )
      ORDER BY nsee.id
      SEPARATOR '|'
    ) AS spell_effect_details
  FROM npc_spells_effects_entries AS nsee
  GROUP BY
    nsee.npc_spells_effects_id
) seagg
  ON seagg.npc_spells_effects_id = se.id

-- Emotes
LEFT JOIN (
  SELECT
    ne.emoteid,

    GROUP_CONCAT(
      ne.event_
      ORDER BY ne.event_, ne.id
      SEPARATOR '|'
    ) AS emote_events,

    GROUP_CONCAT(
      ne.type
      ORDER BY ne.event_, ne.id
      SEPARATOR '|'
    ) AS emote_types,

    GROUP_CONCAT(
      ne.text
      ORDER BY ne.event_, ne.id
      SEPARATOR '|'
    ) AS emote_texts

  FROM npc_emotes AS ne
  GROUP BY
    ne.emoteid
) AS emagg
  ON n.emoteid > 0
 AND emagg.emoteid = n.emoteid

-- Faction Information
LEFT JOIN npc_faction nf
       ON n.npc_faction_id > 0
      AND n.npc_faction_id = nf.id

LEFT JOIN faction_list pfl
       ON nf.primaryfaction = pfl.id

LEFT JOIN (
  SELECT
    nfe.npc_faction_id,

    GROUP_CONCAT(
      nfe.faction_id
      ORDER BY nfe.faction_id
      SEPARATOR '|'
    ) AS faction_ids,

    GROUP_CONCAT(
      fl.name
      ORDER BY nfe.faction_id
      SEPARATOR '|'
    ) AS faction_names,

    GROUP_CONCAT(
      nfe.value
      ORDER BY nfe.faction_id
      SEPARATOR '|'
    ) AS faction_values
  FROM npc_faction_entries AS nfe
  LEFT JOIN faction_list    AS fl
         ON nfe.faction_id = fl.id
  GROUP BY
    nfe.npc_faction_id
) AS nfeagg
       ON n.npc_faction_id > 0
      AND nfeagg.npc_faction_id = n.npc_faction_id

-- TEST FILTER: remove this WHERE when turning into the view definition
WHERE n.id IN (89000, 44075, 771, 27109, 27110, 35062, 416036);
