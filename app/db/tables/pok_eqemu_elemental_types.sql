CREATE TABLE `pok_eqemu_elemental_types` (
  id SMALLINT PRIMARY KEY,
  `name` VARCHAR(32) NOT NULL
) COMMENT='Elemental damage types';

INSERT INTO `pok_eqemu_elemental_types` (id, `name`) VALUES
  (1, 'Magic'),
  (2, 'Fire'),
  (3, 'Cold'),
  (4, 'Poison'),
  (5, 'Disease');
