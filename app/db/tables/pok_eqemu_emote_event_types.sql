CREATE TABLE `pok_eqemu_emote_event_types` (
  id SMALLINT PRIMARY KEY,
  `name` VARCHAR(64) NOT NULL
) COMMENT='Emote event triggers used by npc_emotes.event_';

INSERT INTO `pok_eqemu_emote_event_types` (id, `name`) VALUES
  (0, 'LeaveCombat'),
  (1, 'EnterCombat'),
  (2, 'OnDeath'),
  (3, 'AfterDeath'),
  (4, 'Hailed'),
  (5, 'KilledPC'),
  (6, 'KilledNPC'),
  (7, 'OnSpawn'),
  (8, 'OnDespawn');
