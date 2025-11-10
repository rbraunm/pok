CREATE TABLE `eqemu_deities`(
  id         SMALLINT    PRIMARY KEY,
  name       VARCHAR(64) NOT NULL,
  short_name VARCHAR(16) NULL
);

-- DATA
INSERT INTO `eqemu_deities` (id, name, short_name) VALUES
  (201, 'Bertoxxulous', 'Bert'),
  (202, 'Brell Serilis', 'Brell'),
  (203, 'Cazic-Thule', 'Cazic'),
  (204, 'Erollisi Marr', 'Erollisi'),
  (205, 'Bristlebane', 'Bristle'),
  (206, 'Innoruuk', 'Inny'),
  (207, 'Karana', 'Karana'),
  (208, 'Mithaniel Marr', 'Mithaniel'),
  (209, 'Prexus', 'Prexus'),
  (210, 'Quellious', 'Quellious'),
  (211, 'Rallos Zek', 'Rallos'),
  (212, 'Rodcet Nife', 'Rodcet'),
  (213, 'Solusek Ro', 'Solusek'),
  (214, 'The Tribunal', 'Tribunal'),
  (215, 'Tunare', 'Tunare'),
  (216, 'Veeshan', 'Veeshan'),
  (396, 'Agnostic', 'Agnostic');
