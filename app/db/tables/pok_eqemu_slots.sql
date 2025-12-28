CREATE TABLE `pok_eqemu_slots`(
  id         SMALLINT     PRIMARY KEY,
  name       VARCHAR(32)  NOT NULL,
  short_name VARCHAR(16)  NULL
);

INSERT INTO `pok_eqemu_slots` (id, name, short_name) VALUES
  (0,  'Charm',        'CHARM'),
  (1,  'Ear',          'EAR'),
  (2,  'Head',         'HEAD'),
  (3,  'Face',         'FACE'),
  -- (4, 'Ear 2') omitted (unused)
  (5,  'Neck',         'NECK'),
  (6,  'Shoulders',    'SHOULDERs'),
  (7,  'Arms',         'ARMS'),
  (8,  'Back',         'BACK'),
  (9,  'Bracer',       'BRACER'),
  -- (10, 'Bracer 2') omitted (unused)
  (11, 'Range',        'RANGE'),
  (12, 'Hands',        'HANDS'),
  (13, 'Primary',      'PRIMARY'),
  (14, 'Secondary',    'SECONDARY'),
  (15, 'Ring',         'RING'),
  -- (16, 'Ring 2') omitted (unused)
  (17, 'Chest',        'CHEST'),
  (18, 'Legs',         'LEGS'),
  (19, 'Feet',         'FEET'),
  (20, 'Waist',        'WAIST'),
  (21, 'Powersource',  'POWERSRC'),
  (22, 'Ammo',         'AMMO');