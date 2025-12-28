CREATE TABLE `pok_eqemu_light_source_types` (
  id INT UNSIGNED PRIMARY KEY,
  `name` VARCHAR(255) NOT NULL,
  color VARCHAR(32) DEFAULT NULL,
  brightness_value TINYINT UNSIGNED DEFAULT NULL,
  brightness_name VARCHAR(32) DEFAULT NULL,
  priority TINYINT UNSIGNED DEFAULT NULL,
  works_underwater TINYINT(1) NULL,
  must_equip      TINYINT(1) NULL
) COMMENT='Light source types; brightness split; binary flags 1=true,0=false';

-- Derived from https://wiki.project1999.com/Light_source
INSERT INTO `pok_eqemu_light_source_types`
  (id, `name`, color, brightness_value, brightness_name, priority, works_underwater, must_equip) VALUES
  (1 , 'Candle'            , 'Orange', 9, 'Dim'         , 9, 0, 1),
  (2 , 'Torch'             , 'Orange', 5, 'Bright'      , 8, 0, 1),
  (3 , 'Tiny Glowing Skull', 'Blue'  , 6, 'Less Bright' , 7, 1, 1),
  (4 , 'Small Lantern'     , 'Orange', 3, 'Very Bright' , 4, 0, 1),
  (5 , 'Stein of Moggok'   , 'Blue'  , 4, 'Bright'      , 3, 1, 1),
  (6 , 'Large Lantern'     , 'Orange', 1, 'Very Bright' , 2, 0, 1),
  (7 , 'Flameless Lantern' , 'Blue'  , 2, 'Very Bright' , 1, 1, 1),
  (8 , 'Globe of Stars'    , 'Blue'  , 1, 'Very Bright' , 1, 1, 1), -- This is actually in use in RoF2, best guess stats
  (9 , 'Light Globe'       , 'Blue'  , 6, 'Less Bright' , 7, 1, 0),
  (10, 'Lightstone'        , 'Blue'  , 4, 'Bright'      , 3, 1, 0),
  (11, 'Greater Lightstone', 'Blue'  , 2, 'Very Bright' , 1, 1, 0),
  (12, 'Fire Beetle Eye'   , 'Red'   , 7, 'Less Bright' , 6, 1, 0),
  (13, 'Coldlight'         , 'Purple', 8, 'Dim'         , 5, 1, 0),
  (14, 'Paw of Opolla'     , 'Red'   , 7, 'Less Bright' , 6, 1, 0),
  (15, 'Stein of Tears'    , 'Purple', 8, 'Dim'         , 5, 1, 0);
