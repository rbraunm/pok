CREATE TABLE `pok_eqemu_benefit_categories` (
  id   SMALLINT     PRIMARY KEY,
  `name` VARCHAR(64) NOT NULL
) COMMENT='Item benefit categories';

INSERT INTO `pok_eqemu_benefit_categories` (id, `name`) VALUES
  (1,  'tribute_benefit_token'),
  (3,  'mount_bridle'),
  (10, 'dye_material');
