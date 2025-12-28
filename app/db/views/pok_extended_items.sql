SELECT
  -- Identity / Classification
  i.id                                          AS item_id,
  i.Name                                        AS item_name,
  i.itemclass                                   AS item_class_id,
  ic.name                                       AS item_class_name,
  i.itemtype                                    AS item_type_id,
  itn.name                                      AS item_type_name,
  i.subtype                                     AS item_subtype_id,
  isn.name                                      AS item_subtype_name,
  CASE WHEN i.benefitflag > 0 THEN 1 ELSE 0 END AS item_is_benefit,
  i.benefitflag                                 AS item_benefit_category_id,
  bc.name                                       AS item_benefit_category_name,

  -- Equip / Usage Constraints
  i.slots                                 AS item_slots_bitmask,
  pok_parse_slots_bitmask(i.slots)        AS item_slots_names,
  i.classes                               AS item_classes_bitmask,
  pok_parse_classes_bitmask(i.classes)    AS item_classes_shortnames,
  i.races                                 AS item_races_bitmask,
  pok_parse_races_bitmask(i.races)        AS item_races_shortnames,
  i.deity                                 AS item_deities_bitmask,
  pok_parse_deities_bitmask(i.deity)      AS item_deities_names,
  i.reqlevel                              AS item_req_level,
  i.reclevel                              AS item_rec_level,
  i.recskill                              AS item_rec_skill_level,
  i.size                                  AS item_size_id,
  isz.name                                AS item_size_name,
  i.stackable                             AS item_is_stackable,
  i.stacksize                             AS item_stack_size,
  i.weight                                AS item_weight,
  i.minstatus                             AS item_min_player_status_value,
  accr.id                                 AS item_min_player_status_id,
  accr.name                               AS item_min_player_status_name,

  -- Power Source
  i.purity                AS item_purity,
  i.powersourcecapacity   AS item_power_source_capacity,

  -- Primary Stats
  i.astr                  AS item_str,
  i.asta                  AS item_sta,
  i.adex                  AS item_dex,
  i.aagi                  AS item_agi,
  i.aint                  AS item_int,
  i.awis                  AS item_wis,
  i.acha                  AS item_cha,

  i.mr                    AS item_resist_magic,
  i.fr                    AS item_resist_fire,
  i.cr                    AS item_resist_cold,
  i.dr                    AS item_resist_disease,
  i.pr                    AS item_resist_poison,
  i.svcorruption          AS item_resist_corruption,

  i.ac                    AS item_ac,
  i.hp                    AS item_hp,
  i.mana                  AS item_mana,
  i.endur                 AS item_endur,

  i.attack                AS item_attack,
  i.accuracy              AS item_accuracy,
  i.avoidance             AS item_avoidance,
  i.haste                 AS item_haste,

  -- Heroic Stats
  i.heroic_str            AS item_heroic_str,
  i.heroic_sta            AS item_heroic_sta,
  i.heroic_dex            AS item_heroic_dex,
  i.heroic_agi            AS item_heroic_agi,
  i.heroic_int            AS item_heroic_int,
  i.heroic_wis            AS item_heroic_wis,
  i.heroic_cha            AS item_heroic_cha,

  i.heroic_mr             AS item_heroic_resist_magic,
  i.heroic_fr             AS item_heroic_resist_fire,
  i.heroic_cr             AS item_heroic_resist_cold,
  i.heroic_dr             AS item_heroic_resist_disease,
  i.heroic_pr             AS item_heroic_resist_poison,
  i.heroic_svcorrup       AS item_heroic_resist_corruption,

  -- Regeneration / Mitigation
  i.shielding             AS item_shielding,
  i.spellshield           AS item_spell_shield,
  i.dotshielding          AS item_dot_shielding,
  i.strikethrough         AS item_strikethrough,
  i.stunresist            AS item_stun_resist,
  i.damageshield          AS item_damage_shield,
  i.dsmitigation          AS item_damage_shield_mitigation,
  i.regen                 AS item_regen_hp,
  i.manaregen             AS item_regen_mana,
  i.enduranceregen        AS item_regen_endurance,
  i.clairvoyance          AS item_clairvoyance,
  i.healamt               AS item_heal_amount,
  i.spelldmg              AS item_spell_damage,

  -- Weapon specifics
  i.damage                                                  AS item_damage,
  i.delay                                                   AS item_delay,
  ROUND(i.damage / NULLIF(i.delay, 0), 4)                   AS item_ratio,
  i.range                                                   AS item_range,
  i.backstabdmg                                             AS item_backstab_damage,
  i.elemdmgtype                                             AS item_elemental_damage_type_id,
  et.name                                                   AS item_elemental_damage_type_name,
  i.elemdmgamt                                              AS item_elemental_damage_value,
  i.extradmgskill                                           AS item_extra_damage_skill_id,
  CASE WHEN i.extradmgamt <> 0 THEN eds.name ELSE NULL END  AS item_extra_damage_skill_name,
  i.extradmgamt                                             AS item_extra_damage_value,
  i.skillmodtype                                            AS item_modify_skill_id,
  CASE WHEN i.skillmodvalue <> 0 THEN ms.name ELSE NULL END AS item_modify_skill_name,
  i.skillmodvalue                                           AS item_modify_skill_value,
  i.skillmodmax                                             AS item_modify_skill_max,
  i.combateffects                                           AS item_combat_effects,

  i.banedmgbody                                             AS item_bane_body_type_id,
  bt.name                                                   AS item_bane_body_type_name,
  i.banedmgamt                                              AS item_bane_body_damage,

  i.banedmgrace                                             AS item_bane_race_type_id,
  br.name                                                   AS item_bane_race_type_name,
  i.banedmgraceamt                                          AS item_bane_race_damage,

  -- Augment
  i.augrestrict                                AS item_augment_restriction_id,
  ar.name                                      AS item_augment_restriction_name,
  i.augtype                                    AS item_augment_types_bitmask,
  pok_parse_augment_types_bitmask(i.augtype)   AS item_augment_types_names,
  i.augdistiller                               AS item_augment_distiller_id,
  ad.name                                      AS item_augment_distiller_name,

  -- Augment Slots
  i.augslot1type        AS item_augment_slot_1_type_id,
  as1t.description      AS item_augment_slot_1_type_description,
  i.augslot1visible     AS item_is_augment_slot_1_visible,

  i.augslot2type        AS item_augment_slot_2_type_id,
  as2t.description      AS item_augment_slot_2_type_description,
  i.augslot2visible     AS item_is_augment_slot_2_visible,

  i.augslot3type        AS item_augment_slot_3_type_id,
  as3t.description      AS item_augment_slot_3_type_description,
  i.augslot3visible     AS item_is_augment_slot_3_visible,

  i.augslot4type        AS item_augment_slot_4_type_id,
  as4t.description      AS item_augment_slot_4_type_description,
  i.augslot4visible     AS item_is_augment_slot_4_visible,

  i.augslot5type        AS item_augment_slot_5_type_id,
  as5t.description      AS item_augment_slot_5_type_description,
  i.augslot5visible     AS item_is_augment_slot_5_visible,

  i.augslot6type        AS item_augment_slot_6_type_id,
  as6t.description      AS item_augment_slot_6_type_description,
  i.augslot6visible     AS item_is_augment_slot_6_visible,

  -- Effects (Click / Worn / Focus / Scroll / Proc / Bard)
  i.maxcharges      AS item_max_charges,
  i.potionbelt      AS item_is_potion_belt_enabled,

  i.worneffect      AS item_worn_effect_id,
  i.wornname        AS item_worn_effect_name,
  w.name            AS item_worn_effect_spell_name,
  CASE WHEN i.worneffect > 0 THEN i.worntype ELSE NULL END AS item_worn_effect_type_id,
  CASE WHEN i.worneffect > 0 THEN wet.name ELSE NULL END AS item_worn_effect_type_name,
  i.wornlevel       AS item_worn_effect_level,
  i.wornlevel2      AS item_worn_effect_level2,

  i.clickeffect                       AS item_click_effect_id,
  i.clickname                         AS item_click_effect_name,
  c.name                              AS item_click_effect_spell_name,
  CASE WHEN i.clickeffect > 0 THEN i.clicktype ELSE NULL END AS item_click_effect_type_id,
  CASE WHEN i.clickeffect > 0 THEN cet.name ELSE NULL END AS item_click_effect_type_name,
  i.casttime                          AS item_click_effect_cast_time,
  pok_parse_time(i.casttime,'ms')     AS item_click_effect_cast_time_formatted,
  i.recastdelay                       AS item_click_effect_recast_delay,
  pok_parse_time(i.recastdelay,'s')   AS item_click_effect_recast_delay_formatted,
  i.recasttype                        AS item_click_effect_recast_delay_group_id, -- This group has no associated name and none is exposed in the GUI, simple integer check
  i.clicklevel                        AS item_click_effect_level,
  i.clicklevel2                       AS item_click_effect_level2,

  i.focuseffect     AS item_focus_effect_id,
  i.focusname       AS item_focus_effect_name,
  f.name            AS item_focus_effect_spell_name,
  CASE WHEN i.focuseffect > 0 THEN i.focustype ELSE NULL END AS item_focus_effect_type_id,
  CASE WHEN i.focuseffect > 0 THEN fet.name ELSE NULL END AS item_focus_effect_type_name,
  i.focuslevel      AS item_focus_effect_level,
  i.focuslevel2     AS item_focus_effect_level2,

  i.scrolleffect    AS item_scroll_effect_id,
  i.scrollname      AS item_scroll_effect_name,
  s.name            AS item_scroll_effect_spell_name,
  CASE WHEN i.scrolleffect > 0 THEN i.scrolltype ELSE NULL END AS item_scroll_effect_type_id,
  CASE WHEN i.scrolleffect > 0 THEN scet.name ELSE NULL END AS item_scroll_effect_type_name,
  i.scrolllevel     AS item_scroll_effect_level,
  i.scrolllevel2    AS item_scroll_effect_level2,

  i.bardeffect      AS item_bard_effect_id,
  i.bardname        AS item_bard_effect_name,
  b.name            AS item_bard_effect_spell_name,
  CASE WHEN i.bardeffect > 0 THEN i.bardeffecttype ELSE NULL END AS item_bard_effect_type_id,
  CASE WHEN i.bardeffect > 0 THEN bet.name ELSE NULL END AS item_bard_effect_type_name,
  i.bardlevel       AS item_bard_effect_level,
  i.bardlevel2      AS item_bard_effect_level2,
  i.bardtype        AS item_instrument_type_id,
  btn.name          AS item_instrument_type_name,
  i.bardvalue       AS item_instrument_value,

  i.proceffect                                         AS item_proc_effect_id,
  i.procname                                           AS item_proc_effect_name,
  p.name                                               AS item_proc_effect_spell_name,
  CASE WHEN i.proceffect > 0 THEN i.proctype ELSE NULL END AS item_proc_effect_type_id,
  CASE WHEN i.proceffect > 0 THEN pet.name ELSE NULL END AS item_proc_effect_type_name,
  ROUND(1+(i.procrate/100),2)                          AS item_proc_effect_rate_multiplier,
  CONCAT(IF(i.procrate>0,'+',''),i.procrate,'%')       AS item_proc_rate_bonus,
  i.proclevel                                          AS item_proc_effect_level,
  i.proclevel2                                         AS item_proc_effect_level2,

  -- Containers
  CASE WHEN i.bagslots > 0 THEN i.bagsize ELSE NULL END AS container_max_size_id,
  CASE WHEN i.bagslots > 0 THEN csz.name ELSE NULL END AS container_max_size_name,
  i.bagslots                                           AS container_slots,
  i.potionbeltslots                                    AS container_potion_belt_slots,
  i.bagtype                                            AS container_type_id,
  ct.name                                              AS container_type_name,
  CASE
    WHEN i.bagslots > 0 THEN ROUND(1 - (GREATEST(0, LEAST(100, COALESCE(i.bagwr,0))) / 100), 2)
    ELSE NULL
  END AS container_item_weight_multiplier, -- 75 WR -> 0.25
  CASE
    WHEN i.bagslots > 0 THEN CONCAT(GREATEST(0, LEAST(100, COALESCE(i.bagwr,0))), '%')
    ELSE NULL
  END AS container_item_weight_reduction_percentage, -- 75 WR -> 75%

  -- Light Sources
  i.light                              AS item_light_source_type_id,
  lst.name                             AS item_light_source_type_name,
  lst.color                            AS item_light_source_type_color,
  lst.brightness_value                 AS item_light_source_type_brightness_value,
  lst.brightness_name                  AS item_light_source_type_brightness_name,
  lst.priority                         AS item_light_source_type_priority,
  lst.works_underwater                 AS item_light_source_type_works_underwater,
  lst.must_equip                       AS item_light_source_type_must_equip,

  -- Food and Drink use an overloaded casttime_ value as part of their implementation
  -- Food
  pok_parse_food_value(i.itemtype,i.casttime_)        AS item_food_value,
  pok_parse_food_description(i.itemtype,i.casttime_)  AS item_food_description,

  -- Drink
  pok_parse_alcohol_value(i.itemtype,i.casttime_)     AS item_alcohol_value,
  
  pok_parse_drink_value(i.itemtype,i.casttime_)       AS item_drink_value,
  pok_parse_drink_description(i.itemtype,i.casttime_) AS item_drink_description,

  -- Economy / Currency
  i.price                                   AS item_copper_price,
  i.sellrate                                AS item_copper_sell_rate,
  i.pointtype                               AS item_point_type_id,
  pt.name                                   AS item_point_type_name,
  i.ldonprice                               AS item_point_price,
  i.ldonsold                                AS item_is_ldon_sold,
  i.ldonsellbackrate                        AS item_ldon_sell_rate,
  i.ldontheme                               AS item_ldon_theme_id,
  pok_parse_ldon_theme_bitmask(i.ldontheme) AS item_ldon_theme_name,
  i.favor                                   AS item_personal_favor,
  i.guildfavor                              AS item_guild_favor,

  -- Flags
  i.magic                                   AS item_is_magic,
  i.epicitem                                AS item_is_epic,
  i.heirloom                                AS item_is_heirloom,
  i.artifactflag                            AS item_is_artifact,
  i.attuneable                              AS item_is_attuneable,
  -- nodrop=0 means "No Drop" (non-tradable)
  NOT i.nodrop                              AS item_is_no_drop,
  -- norent=0 means "No Rent" (temporary, not persisted)
  NOT i.norent                              AS item_is_temporary,
  i.fvnodrop                                AS item_is_fv_no_drop,
  i.notransfer                              AS item_is_no_transfer,
  i.nopet                                   AS item_is_no_pet,
  i.questitemflag                           AS item_is_quest,
  i.summonedflag                            AS item_is_summoned,
  i.tradeskills                             AS item_is_tradeskill_component,
  i.expendablearrow                         AS item_is_expendable_arrow,

  -- Evolving Items
  i.evoitem                                 AS item_is_evolving,
  i.evoid                                   AS item_evolution_group_id,
  evo.group_size                            AS item_evolution_group_size,
  evo.name                                  AS item_evolution_group_name,
  i.evolvinglevel                           AS item_evolution_current_level,
  i.evomax                                  AS item_evolution_max_level,

  -- Faction Modifiers
  i.factionmod1                             AS item_faction_1_id,
  f1.name                                   AS item_faction_1_name,
  i.factionamt1                             AS item_faction_1_modifier,

  i.factionmod2                             AS item_faction_2_id,
  f2.name                                   AS item_faction_2_name,
  i.factionamt2                             AS item_faction_2_modifier,

  i.factionmod3                             AS item_faction_3_id,
  f3.name                                   AS item_faction_3_name,
  i.factionamt3                             AS item_faction_3_modifier,

  i.factionmod4                             AS item_faction_4_id,
  f4.name                                   AS item_faction_4_name,
  i.factionamt4                             AS item_faction_4_modifier,

  -- Visual
  i.icon                                    AS item_icon_id,
  CONCAT("dragitem",pok_get_icon_url(i.icon,6,6,500,1)) AS item_icon_url,
  i.color                                   AS item_color_32bit,
  pok_parse_color_argb(i.color)             AS item_color_argb,
  pok_parse_color_hex(i.color)              AS item_color_hex,
  i.placeable                               AS item_is_placeable,
  i.idfile                                  AS item_material_file_id,
  i.material                                AS item_material_id,
  im.name                                   AS item_material_name,
  i.elitematerial                           AS item_elite_material_id,
  em.name                                   AS item_elite_material_name,
  i.herosforgemodel                         AS item_heros_forge_model_id,
  hfm.name                                  AS item_heros_forge_model_name,
  hfm.filename                              AS item_heros_forge_model_file_name,

  -- Lore
  CASE WHEN i.loregroup <> 0 THEN 1 ELSE 0 END           AS item_is_lore,
  CASE WHEN i.loregroup > 0 THEN i.loregroup ELSE NULL END AS item_lore_group_id,
  lg.name                                                AS item_lore_group_name,
  lg.group_size                                          AS item_lore_group_size,
  i.pendingloreflag                                      AS item_is_lore_pending,
  i.lore                                                 AS item_lore_text,
  CASE WHEN i.book > 0 THEN 1 ELSE 0 END                 AS item_is_readable,
  i.book                                                 AS item_book_type_id,
  bkt.name                                               AS item_book_type_name,
  i.filename                                             AS item_book_file_name,
  bks.id                                                 AS item_book_id,
  bks.name                                               AS item_book_name,
  bks.txtfile                                            AS item_book_text,
  bks.language                                           AS item_book_language_id,
  bkl.name                                               AS item_book_language_name,
  i.lorefile                                             AS item_deprecated_lore_file_id,
  CASE WHEN i.book > 0 THEN i.booktype ELSE NULL END     AS item_book_legacy_language_id, -- Not used in code
  lbl.name                                               AS item_book_legacy_language_name, -- Not used in code

  -- Metadata
  i.charmfile                               AS item_charm_file,
  i.charmfileid                             AS item_charm_file_id,
  i.scriptfileid                            AS item_script_file_id,
  i.serialized                              AS item_serialized_datetime,
  i.serialization                           AS item_serialized_value,
  i.comment                                 AS item_comment,
  i.created                                 AS item_created_datetime,
  i.updated                                 AS item_updated_datetime,
  i.verified                                AS item_verified_datetime,
  i.source                                  AS item_data_source

FROM items i

LEFT JOIN spells_new c                      ON i.clickeffect    = c.id
LEFT JOIN spells_new w                      ON i.worneffect     = w.id
LEFT JOIN spells_new f                      ON i.focuseffect    = f.id
LEFT JOIN spells_new s                      ON i.scrolleffect   = s.id
LEFT JOIN spells_new p                      ON i.proceffect     = p.id
LEFT JOIN spells_new b                      ON i.bardeffect     = b.id

LEFT JOIN pok_eqemu_item_effect_types cet   ON i.clicktype      = cet.id
LEFT JOIN pok_eqemu_item_effect_types wet   ON i.worntype       = wet.id
LEFT JOIN pok_eqemu_item_effect_types fet   ON i.focustype      = fet.id
LEFT JOIN pok_eqemu_item_effect_types scet  ON i.scrolltype     = scet.id
LEFT JOIN pok_eqemu_item_effect_types pet   ON i.proctype       = pet.id
LEFT JOIN pok_eqemu_item_effect_types bet   ON i.bardeffecttype = bet.id

LEFT JOIN pok_eqemu_augment_types as1t      ON i.augslot1type   = as1t.id
LEFT JOIN pok_eqemu_augment_types as2t      ON i.augslot2type   = as2t.id
LEFT JOIN pok_eqemu_augment_types as3t      ON i.augslot3type   = as3t.id
LEFT JOIN pok_eqemu_augment_types as4t      ON i.augslot4type   = as4t.id
LEFT JOIN pok_eqemu_augment_types as5t      ON i.augslot5type   = as5t.id
LEFT JOIN pok_eqemu_augment_types as6t      ON i.augslot6type   = as6t.id

LEFT JOIN faction_list f1                   ON i.factionmod1    = f1.id
                                               AND i.factionmod1 > 0
LEFT JOIN faction_list f2                   ON i.factionmod2    = f2.id
                                               AND i.factionmod2 > 0
LEFT JOIN faction_list f3                   ON i.factionmod3    = f3.id
                                               AND i.factionmod3 > 0
LEFT JOIN faction_list f4                   ON i.factionmod4    = f4.id
                                               AND i.factionmod4 > 0

LEFT JOIN items ad                          ON i.augdistiller   = ad.id

LEFT JOIN pok_eqemu_languages lbl           ON i.booktype        = lbl.id
                                               AND i.book > 0

LEFT JOIN books bks                         ON i.filename       = bks.name
                                               AND TRIM(i.filename) <> ''
LEFT JOIN pok_eqemu_languages bkl           ON bks.language     = bkl.id

LEFT JOIN pok_eqemu_npc_body_types bt       ON i.banedmgbody     = bt.id
LEFT JOIN pok_eqemu_races br                ON i.banedmgrace     = br.id
LEFT JOIN pok_eqemu_container_types ct      ON i.bagtype         = ct.id
LEFT JOIN pok_eqemu_item_classes ic         ON i.itemclass       = ic.id
LEFT JOIN pok_eqemu_item_types itn          ON i.itemtype        = itn.id
LEFT JOIN pok_eqemu_item_subtypes isn       ON i.subtype         = isn.id
LEFT JOIN pok_eqemu_lore_groups lg          ON i.loregroup       = lg.id
LEFT JOIN pok_eqemu_skills eds              ON i.extradmgskill   = eds.id
LEFT JOIN pok_eqemu_skills ms               ON i.skillmodtype    = ms.id
LEFT JOIN pok_eqemu_materials im            ON i.material        = im.id
LEFT JOIN pok_eqemu_elite_materials em      ON i.elitematerial   = em.id
LEFT JOIN pok_eqemu_light_source_types lst  ON i.light           = lst.id
LEFT JOIN pok_eqemu_heros_forge_models hfm  ON i.herosforgemodel = hfm.id
LEFT JOIN pok_eqemu_book_types bkt          ON i.book            = bkt.id
LEFT JOIN pok_eqemu_point_types pt          ON i.pointtype       = pt.id
LEFT JOIN pok_eqemu_augment_restrictions ar ON i.augrestrict     = ar.id
LEFT JOIN pok_eqemu_benefit_categories bc   ON i.benefitflag     = bc.id
LEFT JOIN pok_eqemu_elemental_types et      ON i.elemdmgtype     = et.id
LEFT JOIN pok_eqemu_evolution_lines evo     ON i.evoid           = evo.id

LEFT JOIN pok_eqemu_item_sizes isz          ON i.size            = isz.id
LEFT JOIN pok_eqemu_item_sizes csz          ON i.bagsize         = csz.id


LEFT JOIN pok_eqemu_account_ranks accr      ON accr.status = (
                                                 SELECT MIN(accr2.status)
                                                 FROM pok_eqemu_account_ranks accr2
                                                 WHERE accr2.status >= COALESCE(i.minstatus, 0)
                                               )

LEFT JOIN pok_eqemu_item_types btn          ON i.bardtype       = btn.id
                                               AND btn.is_instrument = 1;
