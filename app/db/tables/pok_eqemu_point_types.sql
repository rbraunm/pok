CREATE TABLE `pok_eqemu_point_types` (
  id SMALLINT PRIMARY KEY,
  `name` VARCHAR(255) NOT NULL
) COMMENT='Point types';

INSERT INTO `pok_eqemu_point_types` (id, `name`) VALUES
  (1, 'LDoN Points'),
  (2, 'LDoN Points'),
  (4, 'Radiant Crystals'),
  (5, 'Ebon Crystals');
