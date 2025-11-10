CREATE TABLE `eqemu_augment_restrictions` (
  id   SMALLINT PRIMARY KEY,
  `name` VARCHAR(255) NOT NULL
) COMMENT='Augment restrictions';

INSERT INTO `eqemu_augment_restrictions` (id, `name`) VALUES
  (1,  'Armor Only'),
  (2,  'Weapons Only'),
  (3,  '1H Weapons Only'),
  (4,  '2H Weapons Only'),
  (5,  '1H Slash Only'),
  (6,  '1H Blunt Only'),
  (7,  'Piercing Only'),
  (8,  'Hand-to-Hand Only'),
  (9,  '2H Slash Only'),
  (10, '2H Blunt Only'),
  (11, '2H Pierce Only'),
  (12, 'Bows Only'),
  (13, 'Shields Only');
