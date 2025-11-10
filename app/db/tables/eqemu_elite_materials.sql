CREATE TABLE `eqemu_elite_materials` (
  id SMALLINT PRIMARY KEY,
  `name` VARCHAR(255) NOT NULL
) COMMENT='Elite materials (Velious textures)';

INSERT INTO `eqemu_elite_materials` (id, `name`) VALUES
  (17 , 'Velious Leather'),
  (18 , 'Velious Chain'),
  (19 , 'Velious Plate'),
  (20 , 'Velious Cloth'),
  (21 , 'Velious Ringmail'),
  (22 , 'Velious Scale'),
  (23 , 'Velious Monk');
