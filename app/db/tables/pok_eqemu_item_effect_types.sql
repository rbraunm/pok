CREATE TABLE `pok_eqemu_item_effect_types` (
  `id` SMALLINT PRIMARY KEY,
  `name` VARCHAR(32) NOT NULL,
  `family` ENUM('click','worn','focus','scroll','bard','proc') NOT NULL
) COMMENT='Effect type labels for click/worn/focus/scroll/bard/proc enums';

INSERT INTO `pok_eqemu_item_effect_types` (`id`, `name`, `family`) VALUES
  (0, 'Combat',         'proc'),
  (1, 'Any Slot',       'click'),
  (2, 'Effect',         'worn'),
  (3, 'Expendable',     'click'),
  (4, 'Must Equip',     'click'),
  (5, 'Any Slot',       'click'),
  (6, 'Focus Effect',   'focus'),
  (7, 'Effect',         'scroll'),
  (8, 'Focus Effect',   'bard');
