DELIMITER $$

-- =========================================================
-- 1) Mercenaries (mercs, merc_buffs)
-- =========================================================
CREATE PROCEDURE pok_delete_character_mercs (
  IN pCharacterId INT UNSIGNED,
  IN pDryRun      TINYINT(1),
  IN pBackup      TINYINT(1)
)
BEGIN
  IF pDryRun = 1 THEN
    SELECT 'mercs' AS table_name,
           COUNT(*) AS rows_to_delete
    FROM mercs
    WHERE OwnerCharacterID = pCharacterId;

    SELECT 'merc_buffs' AS table_name,
           COUNT(*) AS rows_to_delete
    FROM merc_buffs
    WHERE MercId IN (
      SELECT MercID
      FROM mercs
      WHERE OwnerCharacterID = pCharacterId
    );
  ELSE
    IF pBackup = 1 THEN
      SELECT 'pok_delete_character_mercs' AS procedure_name,
             'Backup requested (not yet implemented)' AS note,
             pCharacterId AS character_id;
    END IF;

    DELETE FROM merc_buffs
    WHERE MercId IN (
      SELECT MercID
      FROM mercs
      WHERE OwnerCharacterID = pCharacterId
    );

    DELETE FROM mercs
    WHERE OwnerCharacterID = pCharacterId;
  END IF;
END$$


-- =========================================================
-- 2) Items & Inventory, Corpses, Parcels, Bandoliers, Potionbelt
-- =========================================================
CREATE PROCEDURE pok_delete_character_itemsAndInventory (
  IN pCharacterId INT UNSIGNED,
  IN pDryRun      TINYINT(1),
  IN pBackup      TINYINT(1)
)
BEGIN
  IF pDryRun = 1 THEN
    -- Corpses and corpse items
    SELECT 'character_corpse_items' AS table_name,
           COUNT(*) AS rows_to_delete
    FROM character_corpse_items
    WHERE corpse_id IN (
      SELECT id
      FROM character_corpses
      WHERE charid = pCharacterId
    );

    SELECT 'character_corpses' AS table_name,
           COUNT(*) AS rows_to_delete
    FROM character_corpses
    WHERE charid = pCharacterId;

    -- Parcels and parcel containers
    SELECT 'character_parcels_containers' AS table_name,
           COUNT(*) AS rows_to_delete
    FROM character_parcels_containers
    WHERE parcels_id IN (
      SELECT id
      FROM character_parcels
      WHERE char_id = pCharacterId
    );

    SELECT 'character_parcels' AS table_name,
           COUNT(*) AS rows_to_delete
    FROM character_parcels
    WHERE char_id = pCharacterId;

    -- Evolving items, bandolier, potionbelt, item recast
    SELECT 'character_evolving_items' AS table_name,
           COUNT(*) AS rows_to_delete
    FROM character_evolving_items
    WHERE character_id = pCharacterId;

    SELECT 'character_item_recast' AS table_name,
           COUNT(*) AS rows_to_delete
    FROM character_item_recast
    WHERE id = pCharacterId;

    SELECT 'character_potionbelt' AS table_name,
           COUNT(*) AS rows_to_delete
    FROM character_potionbelt
    WHERE id = pCharacterId;

    SELECT 'character_bandolier' AS table_name,
           COUNT(*) AS rows_to_delete
    FROM character_bandolier
    WHERE id = pCharacterId;

    -- Inventory and snapshots
    SELECT 'inventory_snapshots' AS table_name,
           COUNT(*) AS rows_to_delete
    FROM inventory_snapshots
    WHERE charid = pCharacterId;

    SELECT 'inventory' AS table_name,
           COUNT(*) AS rows_to_delete
    FROM inventory
    WHERE character_id = pCharacterId;

    -- Keyring and recipe list
    SELECT 'keyring' AS table_name,
           COUNT(*) AS rows_to_delete
    FROM keyring
    WHERE char_id = pCharacterId;

    SELECT 'char_recipe_list' AS table_name,
           COUNT(*) AS rows_to_delete
    FROM char_recipe_list
    WHERE char_id = pCharacterId;

  ELSE
    IF pBackup = 1 THEN
      SELECT 'pok_delete_character_itemsAndInventory' AS procedure_name,
             'Backup requested (not yet implemented)' AS note,
             pCharacterId AS character_id;
    END IF;

    -- Child tables first
    DELETE FROM character_corpse_items
    WHERE corpse_id IN (
      SELECT id
      FROM character_corpses
      WHERE charid = pCharacterId
    );

    DELETE FROM character_corpses
    WHERE charid = pCharacterId;

    DELETE FROM character_parcels_containers
    WHERE parcels_id IN (
      SELECT id
      FROM character_parcels
      WHERE char_id = pCharacterId
    );

    DELETE FROM character_parcels
    WHERE char_id = pCharacterId;

    DELETE FROM character_evolving_items
    WHERE character_id = pCharacterId;

    DELETE FROM character_item_recast
    WHERE id = pCharacterId;

    DELETE FROM character_potionbelt
    WHERE id = pCharacterId;

    DELETE FROM character_bandolier
    WHERE id = pCharacterId;

    DELETE FROM inventory_snapshots
    WHERE charid = pCharacterId;

    DELETE FROM inventory
    WHERE character_id = pCharacterId;

    DELETE FROM keyring
    WHERE char_id = pCharacterId;

    DELETE FROM char_recipe_list
    WHERE char_id = pCharacterId;
  END IF;
END$$


-- =========================================================
-- 3) Spells, AAs, Discs, Buffs, Pets, Tribute, Auras
-- =========================================================
CREATE PROCEDURE pok_delete_character_spellsAAsAndPets (
  IN pCharacterId INT UNSIGNED,
  IN pDryRun      TINYINT(1),
  IN pBackup      TINYINT(1)
)
BEGIN
  IF pDryRun = 1 THEN
    SELECT 'character_spells' AS table_name,
           COUNT(*) AS rows_to_delete
    FROM character_spells
    WHERE id = pCharacterId;

    SELECT 'character_memmed_spells' AS table_name,
           COUNT(*) AS rows_to_delete
    FROM character_memmed_spells
    WHERE id = pCharacterId;

    SELECT 'character_alternate_abilities' AS table_name,
           COUNT(*) AS rows_to_delete
    FROM character_alternate_abilities
    WHERE id = pCharacterId;

    SELECT 'character_disciplines' AS table_name,
           COUNT(*) AS rows_to_delete
    FROM character_disciplines
    WHERE id = pCharacterId;

    SELECT 'character_auras' AS table_name,
           COUNT(*) AS rows_to_delete
    FROM character_auras
    WHERE id = pCharacterId;

    SELECT 'character_buffs' AS table_name,
           COUNT(*) AS rows_to_delete
    FROM character_buffs
    WHERE character_id = pCharacterId;

    SELECT 'character_pet_buffs' AS table_name,
           COUNT(*) AS rows_to_delete
    FROM character_pet_buffs
    WHERE char_id = pCharacterId;

    SELECT 'character_pet_inventory' AS table_name,
           COUNT(*) AS rows_to_delete
    FROM character_pet_inventory
    WHERE char_id = pCharacterId;

    SELECT 'character_pet_info' AS table_name,
           COUNT(*) AS rows_to_delete
    FROM character_pet_info
    WHERE char_id = pCharacterId;

    SELECT 'character_pet_name' AS table_name,
           COUNT(*) AS rows_to_delete
    FROM character_pet_name
    WHERE character_id = pCharacterId;

    SELECT 'character_tribute' AS table_name,
           COUNT(*) AS rows_to_delete
    FROM character_tribute
    WHERE character_id = pCharacterId;

  ELSE
    IF pBackup = 1 THEN
      SELECT 'pok_delete_character_spellsAAsAndPets' AS procedure_name,
             'Backup requested (not yet implemented)' AS note,
             pCharacterId AS character_id;
    END IF;

    DELETE FROM character_spells
    WHERE id = pCharacterId;

    DELETE FROM character_memmed_spells
    WHERE id = pCharacterId;

    DELETE FROM character_alternate_abilities
    WHERE id = pCharacterId;

    DELETE FROM character_disciplines
    WHERE id = pCharacterId;

    DELETE FROM character_auras
    WHERE id = pCharacterId;

    DELETE FROM character_buffs
    WHERE character_id = pCharacterId;

    DELETE FROM character_pet_buffs
    WHERE char_id = pCharacterId;

    DELETE FROM character_pet_inventory
    WHERE char_id = pCharacterId;

    DELETE FROM character_pet_info
    WHERE char_id = pCharacterId;

    DELETE FROM character_pet_name
    WHERE character_id = pCharacterId;

    DELETE FROM character_tribute
    WHERE character_id = pCharacterId;
  END IF;
END$$


-- =========================================================
-- 4) Tasks, Lockouts, Instances, DZ, Adventures, Groups, Raids, Timers, Zone Flags
-- =========================================================
CREATE PROCEDURE pok_delete_character_tasksAndLockouts (
  IN pCharacterId INT UNSIGNED,
  IN pDryRun      TINYINT(1),
  IN pBackup      TINYINT(1)
)
BEGIN
  IF pDryRun = 1 THEN
    SELECT 'completed_shared_task_members' AS table_name,
           COUNT(*) AS rows_to_delete
    FROM completed_shared_task_members
    WHERE character_id = pCharacterId;

    SELECT 'shared_task_members' AS table_name,
           COUNT(*) AS rows_to_delete
    FROM shared_task_members
    WHERE character_id = pCharacterId;

    SELECT 'completed_tasks' AS table_name,
           COUNT(*) AS rows_to_delete
    FROM completed_tasks
    WHERE charid = pCharacterId;

    SELECT 'character_activities' AS table_name,
           COUNT(*) AS rows_to_delete
    FROM character_activities
    WHERE charid = pCharacterId;

    SELECT 'character_enabledtasks' AS table_name,
           COUNT(*) AS rows_to_delete
    FROM character_enabledtasks
    WHERE charid = pCharacterId;

    SELECT 'character_tasks' AS table_name,
           COUNT(*) AS rows_to_delete
    FROM character_tasks
    WHERE charid = pCharacterId;

    SELECT 'character_task_timers' AS table_name,
           COUNT(*) AS rows_to_delete
    FROM character_task_timers
    WHERE character_id = pCharacterId;

    SELECT 'character_expedition_lockouts' AS table_name,
           COUNT(*) AS rows_to_delete
    FROM character_expedition_lockouts
    WHERE character_id = pCharacterId;

    SELECT 'character_instance_safereturns' AS table_name,
           COUNT(*) AS rows_to_delete
    FROM character_instance_safereturns
    WHERE character_id = pCharacterId;

    SELECT 'dynamic_zone_members' AS table_name,
           COUNT(*) AS rows_to_delete
    FROM dynamic_zone_members
    WHERE character_id = pCharacterId;

    SELECT 'instance_list_player' AS table_name,
           COUNT(*) AS rows_to_delete
    FROM instance_list_player
    WHERE charid = pCharacterId;

    SELECT 'adventure_members' AS table_name,
           COUNT(*) AS rows_to_delete
    FROM adventure_members
    WHERE charid = pCharacterId;

    SELECT 'adventure_stats' AS table_name,
           COUNT(*) AS rows_to_delete
    FROM adventure_stats
    WHERE player_id = pCharacterId;

    SELECT 'group_id' AS table_name,
           COUNT(*) AS rows_to_delete
    FROM group_id
    WHERE character_id = pCharacterId;

    SELECT 'raid_members' AS table_name,
           COUNT(*) AS rows_to_delete
    FROM raid_members
    WHERE charid = pCharacterId;

    SELECT 'timers' AS table_name,
           COUNT(*) AS rows_to_delete
    FROM timers
    WHERE char_id = pCharacterId;

    SELECT 'zone_flags' AS table_name,
           COUNT(*) AS rows_to_delete
    FROM zone_flags
    WHERE charID = pCharacterId;

  ELSE
    IF pBackup = 1 THEN
      SELECT 'pok_delete_character_tasksAndLockouts' AS procedure_name,
             'Backup requested (not yet implemented)' AS note,
             pCharacterId AS character_id;
    END IF;

    DELETE FROM completed_shared_task_members
    WHERE character_id = pCharacterId;

    DELETE FROM shared_task_members
    WHERE character_id = pCharacterId;

    DELETE FROM completed_tasks
    WHERE charid = pCharacterId;

    DELETE FROM character_activities
    WHERE charid = pCharacterId;

    DELETE FROM character_enabledtasks
    WHERE charid = pCharacterId;

    DELETE FROM character_tasks
    WHERE charid = pCharacterId;

    DELETE FROM character_task_timers
    WHERE character_id = pCharacterId;

    DELETE FROM character_expedition_lockouts
    WHERE character_id = pCharacterId;

    DELETE FROM character_instance_safereturns
    WHERE character_id = pCharacterId;

    DELETE FROM dynamic_zone_members
    WHERE character_id = pCharacterId;

    DELETE FROM instance_list_player
    WHERE charid = pCharacterId;

    DELETE FROM adventure_members
    WHERE charid = pCharacterId;

    DELETE FROM adventure_stats
    WHERE player_id = pCharacterId;

    DELETE FROM group_id
    WHERE character_id = pCharacterId;

    DELETE FROM raid_members
    WHERE charid = pCharacterId;

    DELETE FROM timers
    WHERE char_id = pCharacterId;

    DELETE FROM zone_flags
    WHERE charID = pCharacterId;
  END IF;
END$$


-- =========================================================
-- 5) Social, Logs, Quest Globals, Data Buckets, Inspect Messages
-- =========================================================
CREATE PROCEDURE pok_delete_character_socialAndLogs (
  IN pCharacterId INT UNSIGNED,
  IN pDryRun      TINYINT(1),
  IN pBackup      TINYINT(1)
)
BEGIN
  IF pDryRun = 1 THEN
    SELECT 'friends' AS table_name,
           COUNT(*) AS rows_to_delete
    FROM friends
    WHERE charid = pCharacterId;

    SELECT 'mail' AS table_name,
           COUNT(*) AS rows_to_delete
    FROM mail
    WHERE charid = pCharacterId;

    SELECT 'quest_globals' AS table_name,
           COUNT(*) AS rows_to_delete
    FROM quest_globals
    WHERE charid = pCharacterId;

    SELECT 'data_buckets' AS table_name,
           COUNT(*) AS rows_to_delete
    FROM data_buckets
    WHERE character_id = pCharacterId;

    SELECT 'player_event_logs' AS table_name,
           COUNT(*) AS rows_to_delete
    FROM player_event_logs
    WHERE character_id = pCharacterId;

    SELECT 'player_event_trade_entries' AS table_name,
           COUNT(*) AS rows_to_delete
    FROM player_event_trade_entries
    WHERE char_id = pCharacterId;

    SELECT 'bug_reports' AS table_name,
           COUNT(*) AS rows_to_delete
    FROM bug_reports
    WHERE character_id = pCharacterId;

    SELECT 'character_inspect_messages' AS table_name,
           COUNT(*) AS rows_to_delete
    FROM character_inspect_messages
    WHERE id = pCharacterId;

    SELECT 'character_peqzone_flags' AS table_name,
           COUNT(*) AS rows_to_delete
    FROM character_peqzone_flags
    WHERE id = pCharacterId;

  ELSE
    IF pBackup = 1 THEN
      SELECT 'pok_delete_character_socialAndLogs' AS procedure_name,
             'Backup requested (not yet implemented)' AS note,
             pCharacterId AS character_id;
    END IF;

    DELETE FROM friends
    WHERE charid = pCharacterId;

    DELETE FROM mail
    WHERE charid = pCharacterId;

    DELETE FROM quest_globals
    WHERE charid = pCharacterId;

    DELETE FROM data_buckets
    WHERE character_id = pCharacterId;

    DELETE FROM player_event_logs
    WHERE character_id = pCharacterId;

    DELETE FROM player_event_trade_entries
    WHERE char_id = pCharacterId;

    DELETE FROM bug_reports
    WHERE character_id = pCharacterId;

    DELETE FROM character_inspect_messages
    WHERE id = pCharacterId;

    DELETE FROM character_peqzone_flags
    WHERE id = pCharacterId;
  END IF;
END$$


-- =========================================================
-- 6) Bots: bots + settings + owner options
--     UPDATED: safe if bot tables are missing
-- =========================================================
CREATE PROCEDURE pok_delete_character_bots (
  IN pCharacterId INT UNSIGNED,
  IN pDryRun      TINYINT(1),
  IN pBackup      TINYINT(1)
)
BEGIN
  DECLARE vHasBots INT DEFAULT 0;

  -- Treat presence of bot_data as "bots feature is installed"
  SELECT COUNT(*)
  INTO vHasBots
  FROM information_schema.tables
  WHERE table_schema = DATABASE()
    AND table_name = 'bot_data';

  IF vHasBots = 0 THEN
    -- Bot tables not present: no-op, but emit a small note
    SELECT 'pok_delete_character_bots: bot tables not present, skipping' AS note,
           pCharacterId AS character_id,
           pDryRun      AS dry_run,
           pBackup      AS backup_requested;
  ELSE
    IF pDryRun = 1 THEN
      -- Core bot records
      SELECT 'bot_data' AS table_name,
             COUNT(*) AS rows_to_delete
      FROM bot_data
      WHERE owner_id = pCharacterId;

      -- Bot pet children (via bot_pets)
      SELECT 'bot_pets' AS table_name,
             COUNT(*) AS rows_to_delete
      FROM bot_pets
      WHERE bot_id IN (
        SELECT bot_id FROM bot_data WHERE owner_id = pCharacterId
      );

      SELECT 'bot_pet_buffs' AS table_name,
             COUNT(*) AS rows_to_delete
      FROM bot_pet_buffs
      WHERE pets_index IN (
        SELECT pets_index
        FROM bot_pets
        WHERE bot_id IN (
          SELECT bot_id FROM bot_data WHERE owner_id = pCharacterId
        )
      );

      SELECT 'bot_pet_inventories' AS table_name,
             COUNT(*) AS rows_to_delete
      FROM bot_pet_inventories
      WHERE pets_index IN (
        SELECT pets_index
        FROM bot_pets
        WHERE bot_id IN (
          SELECT bot_id FROM bot_data WHERE owner_id = pCharacterId
        )
      );

      -- Bot heal rotations (and children)
      SELECT 'bot_heal_rotations' AS table_name,
             COUNT(*) AS rows_to_delete
      FROM bot_heal_rotations
      WHERE bot_id IN (
        SELECT bot_id FROM bot_data WHERE owner_id = pCharacterId
      );

      SELECT 'bot_heal_rotation_members' AS table_name,
             COUNT(*) AS rows_to_delete
      FROM bot_heal_rotation_members
      WHERE heal_rotation_index IN (
        SELECT heal_rotation_index
        FROM bot_heal_rotations
        WHERE bot_id IN (
          SELECT bot_id FROM bot_data WHERE owner_id = pCharacterId
        )
      );

      SELECT 'bot_heal_rotation_targets' AS table_name,
             COUNT(*) AS rows_to_delete
      FROM bot_heal_rotation_targets
      WHERE heal_rotation_index IN (
        SELECT heal_rotation_index
        FROM bot_heal_rotations
        WHERE bot_id IN (
          SELECT bot_id FROM bot_data WHERE owner_id = pCharacterId
        )
      );

      -- Bot group/guild members
      SELECT 'bot_group_members' AS table_name,
             COUNT(*) AS rows_to_delete
      FROM bot_group_members
      WHERE bot_id IN (
        SELECT bot_id FROM bot_data WHERE owner_id = pCharacterId
      );

      SELECT 'bot_guild_members' AS table_name,
             COUNT(*) AS rows_to_delete
      FROM bot_guild_members
      WHERE bot_id IN (
        SELECT bot_id FROM bot_data WHERE owner_id = pCharacterId
      );

      -- Misc bot children keyed by bot_id
      SELECT 'bot_blocked_buffs' AS table_name,
             COUNT(*) AS rows_to_delete
      FROM bot_blocked_buffs
      WHERE bot_id IN (
        SELECT bot_id FROM bot_data WHERE owner_id = pCharacterId
      );

      SELECT 'bot_buffs' AS table_name,
             COUNT(*) AS rows_to_delete
      FROM bot_buffs
      WHERE bot_id IN (
        SELECT bot_id FROM bot_data WHERE owner_id = pCharacterId
      );

      SELECT 'bot_inspect_messages' AS table_name,
             COUNT(*) AS rows_to_delete
      FROM bot_inspect_messages
      WHERE bot_id IN (
        SELECT bot_id FROM bot_data WHERE owner_id = pCharacterId
      );

      SELECT 'bot_inventories' AS table_name,
             COUNT(*) AS rows_to_delete
      FROM bot_inventories
      WHERE bot_id IN (
        SELECT bot_id FROM bot_data WHERE owner_id = pCharacterId
      );

      SELECT 'bot_spell_settings' AS table_name,
             COUNT(*) AS rows_to_delete
      FROM bot_spell_settings
      WHERE bot_id IN (
        SELECT bot_id FROM bot_data WHERE owner_id = pCharacterId
      );

      SELECT 'bot_stances' AS table_name,
             COUNT(*) AS rows_to_delete
      FROM bot_stances
      WHERE bot_id IN (
        SELECT bot_id FROM bot_data WHERE owner_id = pCharacterId
      );

      SELECT 'bot_timers' AS table_name,
             COUNT(*) AS rows_to_delete
      FROM bot_timers
      WHERE bot_id IN (
        SELECT bot_id FROM bot_data WHERE owner_id = pCharacterId
      );

      -- Owner-level settings
      SELECT 'bot_settings' AS table_name,
             COUNT(*) AS rows_to_delete
      FROM bot_settings
      WHERE character_id = pCharacterId;

      SELECT 'bot_owner_options' AS table_name,
             COUNT(*) AS rows_to_delete
      FROM bot_owner_options
      WHERE owner_id = pCharacterId;

    ELSE
      IF pBackup = 1 THEN
        SELECT 'pok_delete_character_bots' AS procedure_name,
               'Backup requested (not yet implemented)' AS note,
               pCharacterId AS character_id;
      END IF;

      -- Pet children first
      DELETE FROM bot_pet_buffs
      WHERE pets_index IN (
        SELECT pets_index
        FROM bot_pets
        WHERE bot_id IN (
          SELECT bot_id FROM bot_data WHERE owner_id = pCharacterId
        )
      );

      DELETE FROM bot_pet_inventories
      WHERE pets_index IN (
        SELECT pets_index
        FROM bot_pets
        WHERE bot_id IN (
          SELECT bot_id FROM bot_data WHERE owner_id = pCharacterId
        )
      );

      -- Heal rotation children
      DELETE FROM bot_heal_rotation_targets
      WHERE heal_rotation_index IN (
        SELECT heal_rotation_index
        FROM bot_heal_rotations
        WHERE bot_id IN (
          SELECT bot_id FROM bot_data WHERE owner_id = pCharacterId
        )
      );

      DELETE FROM bot_heal_rotation_members
      WHERE heal_rotation_index IN (
        SELECT heal_rotation_index
        FROM bot_heal_rotations
        WHERE bot_id IN (
          SELECT bot_id FROM bot_data WHERE owner_id = pCharacterId
        )
      );

      -- Other bot-id keyed children
      DELETE FROM bot_blocked_buffs
      WHERE bot_id IN (
        SELECT bot_id FROM bot_data WHERE owner_id = pCharacterId
      );

      DELETE FROM bot_buffs
      WHERE bot_id IN (
        SELECT bot_id FROM bot_data WHERE owner_id = pCharacterId
      );

      DELETE FROM bot_group_members
      WHERE bot_id IN (
        SELECT bot_id FROM bot_data WHERE owner_id = pCharacterId
      );

      DELETE FROM bot_guild_members
      WHERE bot_id IN (
        SELECT bot_id FROM bot_data WHERE owner_id = pCharacterId
      );

      DELETE FROM bot_inspect_messages
      WHERE bot_id IN (
        SELECT bot_id FROM bot_data WHERE owner_id = pCharacterId
      );

      DELETE FROM bot_inventories
      WHERE bot_id IN (
        SELECT bot_id FROM bot_data WHERE owner_id = pCharacterId
      );

      DELETE FROM bot_spell_settings
      WHERE bot_id IN (
        SELECT bot_id FROM bot_data WHERE owner_id = pCharacterId
      );

      DELETE FROM bot_stances
      WHERE bot_id IN (
        SELECT bot_id FROM bot_data WHERE owner_id = pCharacterId
      );

      DELETE FROM bot_timers
      WHERE bot_id IN (
        SELECT bot_id FROM bot_data WHERE owner_id = pCharacterId
      );

      -- Heal rotations and pets
      DELETE FROM bot_heal_rotations
      WHERE bot_id IN (
        SELECT bot_id FROM bot_data WHERE owner_id = pCharacterId
      );

      DELETE FROM bot_pets
      WHERE bot_id IN (
        SELECT bot_id FROM bot_data WHERE owner_id = pCharacterId
      );

      -- Core bot row
      DELETE FROM bot_data
      WHERE owner_id = pCharacterId;

      -- Owner-level settings
      DELETE FROM bot_settings
      WHERE character_id = pCharacterId;

      DELETE FROM bot_owner_options
      WHERE owner_id = pCharacterId;
    END IF;
  END IF;
END$$


-- =========================================================
-- 7) Guild, Faction, Titles, Trader/Buyer State
-- =========================================================
CREATE PROCEDURE pok_delete_character_guildAndTrade (
  IN pCharacterId INT UNSIGNED,
  IN pDryRun      TINYINT(1),
  IN pBackup      TINYINT(1)
)
BEGIN
  IF pDryRun = 1 THEN
    SELECT 'guild_members' AS table_name,
           COUNT(*) AS rows_to_delete
    FROM guild_members
    WHERE char_id = pCharacterId;

    SELECT 'faction_values' AS table_name,
           COUNT(*) AS rows_to_delete
    FROM faction_values
    WHERE char_id = pCharacterId;

    SELECT 'player_titlesets' AS table_name,
           COUNT(*) AS rows_to_delete
    FROM player_titlesets
    WHERE char_id = pCharacterId;

    SELECT 'titles' AS table_name,
           COUNT(*) AS rows_to_delete
    FROM titles
    WHERE char_id = pCharacterId;

    SELECT 'buyer_buy_lines' AS table_name,
           COUNT(*) AS rows_to_delete
    FROM buyer_buy_lines
    WHERE char_id = pCharacterId;

    SELECT 'buyer' AS table_name,
           COUNT(*) AS rows_to_delete
    FROM buyer
    WHERE char_id = pCharacterId;

    SELECT 'trader' AS table_name,
           COUNT(*) AS rows_to_delete
    FROM trader
    WHERE char_id = pCharacterId;

  ELSE
    IF pBackup = 1 THEN
      SELECT 'pok_delete_character_guildAndTrade' AS procedure_name,
             'Backup requested (not yet implemented)' AS note,
             pCharacterId AS character_id;
    END IF;

    DELETE FROM guild_members
    WHERE char_id = pCharacterId;

    DELETE FROM faction_values
    WHERE char_id = pCharacterId;

    DELETE FROM player_titlesets
    WHERE char_id = pCharacterId;

    DELETE FROM titles
    WHERE char_id = pCharacterId;

    DELETE FROM buyer_buy_lines
    WHERE char_id = pCharacterId;

    DELETE FROM buyer
    WHERE char_id = pCharacterId;

    DELETE FROM trader
    WHERE char_id = pCharacterId;
  END IF;
END$$


-- =========================================================
-- 8) Core Profile (currencies, stats, skills, binds, etc)
-- =========================================================
CREATE PROCEDURE pok_delete_character_coreProfile (
  IN pCharacterId INT UNSIGNED,
  IN pDryRun      TINYINT(1),
  IN pBackup      TINYINT(1)
)
BEGIN
  IF pDryRun = 1 THEN
    SELECT 'character_alt_currency' AS table_name,
           COUNT(*) AS rows_to_delete
    FROM character_alt_currency
    WHERE char_id = pCharacterId;

    SELECT 'character_currency' AS table_name,
           COUNT(*) AS rows_to_delete
    FROM character_currency
    WHERE id = pCharacterId;

    SELECT 'character_exp_modifiers' AS table_name,
           COUNT(*) AS rows_to_delete
    FROM character_exp_modifiers
    WHERE character_id = pCharacterId;

    SELECT 'character_stats_record' AS table_name,
           COUNT(*) AS rows_to_delete
    FROM character_stats_record
    WHERE character_id = pCharacterId;

    SELECT 'character_bind' AS table_name,
           COUNT(*) AS rows_to_delete
    FROM character_bind
    WHERE id = pCharacterId;

    SELECT 'character_languages' AS table_name,
           COUNT(*) AS rows_to_delete
    FROM character_languages
    WHERE id = pCharacterId;

    SELECT 'character_leadership_abilities' AS table_name,
           COUNT(*) AS rows_to_delete
    FROM character_leadership_abilities
    WHERE id = pCharacterId;

    SELECT 'character_material' AS table_name,
           COUNT(*) AS rows_to_delete
    FROM character_material
    WHERE id = pCharacterId;

    SELECT 'character_skills' AS table_name,
           COUNT(*) AS rows_to_delete
    FROM character_skills
    WHERE id = pCharacterId;

    SELECT 'character_data' AS table_name,
           COUNT(*) AS rows_to_delete
    FROM character_data
    WHERE id = pCharacterId;

  ELSE
    IF pBackup = 1 THEN
      SELECT 'pok_delete_character_coreProfile' AS procedure_name,
             'Backup requested (not yet implemented)' AS note,
             pCharacterId AS character_id;
    END IF;

    DELETE FROM character_alt_currency
    WHERE char_id = pCharacterId;

    DELETE FROM character_currency
    WHERE id = pCharacterId;

    DELETE FROM character_exp_modifiers
    WHERE character_id = pCharacterId;

    DELETE FROM character_stats_record
    WHERE character_id = pCharacterId;

    DELETE FROM character_bind
    WHERE id = pCharacterId;

    DELETE FROM character_languages
    WHERE id = pCharacterId;

    DELETE FROM character_leadership_abilities
    WHERE id = pCharacterId;

    DELETE FROM character_material
    WHERE id = pCharacterId;

    DELETE FROM character_skills
    WHERE id = pCharacterId;

    -- Finally, the main character row
    DELETE FROM character_data
    WHERE id = pCharacterId;
  END IF;
END$$


-- =========================================================
-- 9) Orchestrator: full character delete
-- =========================================================
CREATE PROCEDURE pok_delete_character_full (
  IN pCharacterId INT UNSIGNED,
  IN pDryRun      TINYINT(1),
  IN pBackup      TINYINT(1)
)
BEGIN
  -- High-level note for dry runs
  SELECT 'pok_delete_character_full' AS procedure_name,
         pCharacterId AS character_id,
         pDryRun      AS dry_run,
         pBackup      AS backup_requested;

  CALL pok_delete_character_mercs(pCharacterId, pDryRun, pBackup);
  CALL pok_delete_character_itemsAndInventory(pCharacterId, pDryRun, pBackup);
  CALL pok_delete_character_spellsAAsAndPets(pCharacterId, pDryRun, pBackup);
  CALL pok_delete_character_tasksAndLockouts(pCharacterId, pDryRun, pBackup);
  CALL pok_delete_character_socialAndLogs(pCharacterId, pDryRun, pBackup);
  CALL pok_delete_character_bots(pCharacterId, pDryRun, pBackup);
  CALL pok_delete_character_guildAndTrade(pCharacterId, pDryRun, pBackup);
  CALL pok_delete_character_coreProfile(pCharacterId, pDryRun, pBackup);
END$$

DELIMITER ;
