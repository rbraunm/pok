CREATE TABLE `pok_eqemu_book_types` (
  id SMALLINT PRIMARY KEY,
  `name` VARCHAR(64) NOT NULL
) COMMENT='Book types';

INSERT INTO `pok_eqemu_book_types` (id, `name`) VALUES
  (1, 'Book'),
  (2, 'Message');
