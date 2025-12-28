CREATE TABLE `pok_eqemu_emote_types` (
  id SMALLINT PRIMARY KEY,
  `name` VARCHAR(64) NOT NULL
) COMMENT='Emote delivery types used by npc_emotes.type';

INSERT INTO `pok_eqemu_emote_types` (id, `name`) VALUES
  (0, 'Say'),
  (1, 'Emote'),
  (2, 'Shout'),
  (3, 'Proximity');
