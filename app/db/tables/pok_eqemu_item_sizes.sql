CREATE TABLE `pok_eqemu_item_sizes` (
  id SMALLINT PRIMARY KEY,
  `name` VARCHAR(16) NOT NULL
) COMMENT='Item size names (join to items.size)';

INSERT INTO `pok_eqemu_item_sizes` (id, `name`) VALUES
  (0, 'Tiny'),
  (1, 'Small'),
  (2, 'Medium'),
  (3, 'Large'),
  (4, 'Giant'),
  (5, 'Massive'),
  (6, 'Colossal');
