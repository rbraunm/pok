CREATE TABLE `eqemu_item_subtypes` (
  id SMALLINT PRIMARY KEY,
  `name` VARCHAR(255) NOT NULL
) COMMENT='Item subtypes';

INSERT INTO `eqemu_item_subtypes` (id, `name`) VALUES
  (1  , 'Consumables: Absinthe/Procs'),
  (2  , 'Consumables: Antidote/Immunization'),
  (3  , 'Consumables: Skinspikes'),
  (4  , 'Consumables: Tonics (Resonant/Affinity)'),
  (5  , 'Consumables: Divine/Celestial Healing'),
  (6  , 'Consumables: Essences (Race)'),
  (7  , 'Consumables: Weapon Proc Poisons'),
  (8  , 'Consumables: Clarity/Health/Regen'),
  (9  , 'Consumables: Translocation'),
  (10 , 'Jewelry: Feymetal Trio'),
  (11 , 'Consumables: Utility (Wolf/Faerune)'),
  (12 , 'Consumables: Philter Lines'),
  (13 , 'Mounts: Rope/Small Drums'),
  (14 , 'Mounts: Leather/Drums'),
  (15 , 'Mounts: Silken/Worg'),
  (16 , 'Mounts: Chain/Worg/Drums'),
  (17 , 'Mounts: Ornate Chain/Drums'),
  (99 , 'Consumables: Legacy Multi-dose'),
  (120, 'Cultural: Simple/Blessed'),
  (140, 'Cultural: Ornate/Revered'),
  (160, 'Cultural: Intricate/Sacred'),
  (170, 'Cultural: Elaborate/Eminent'),
  (175, 'Cultural: Exalted'),
  (180, 'Cultural: Elegant/Sublime/Venerable'),
  (185, 'Cultural: Stalwart'),
  (190, 'Cultural: Extravagant/Illustrious'),
  (195, 'Cultural: Glorious/Numinous');
