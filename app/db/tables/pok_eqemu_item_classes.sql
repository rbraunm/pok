CREATE TABLE `pok_eqemu_item_classes` (
  id SMALLINT PRIMARY KEY,
  `name` VARCHAR(64) NOT NULL
) COMMENT='Item classes';

INSERT INTO `pok_eqemu_item_classes` (id, `name`) VALUES
  (0, 'Normal'),
  (1, 'Container'),
  (2, 'Book');
