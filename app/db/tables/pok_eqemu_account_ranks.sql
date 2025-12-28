CREATE TABLE `pok_eqemu_account_ranks` (
  id      SMALLINT     PRIMARY KEY,
  `status` SMALLINT    NOT NULL,
  `name`  VARCHAR(32)  NOT NULL,
  UNIQUE KEY `uq_status` (`status`)
) COMMENT='Player account ranks';

INSERT INTO `pok_eqemu_account_ranks` (id, `status`, `name`) VALUES
  (1,   0,   'Normal'),
  (2,   10,  'Steward'),
  (3,   20,  'Apprentice Guide'),
  (4,   50,  'Guide'),
  (5,   80,  'QuestTroupe'),
  (6,   81,  'Senior Guide'),
  (7,   85,  'GM-Tester'),
  (8,   90,  'EQ Support'),
  (9,   95,  'GM-Staff'),
  (10,  100, 'GM-Admin'),
  (11,  150, 'GM-Lead Admin'),
  (12,  160, 'QuestMaster'),
  (13,  170, 'GM-Areas'),
  (14,  180, 'GM-Coder'),
  (15,  200, 'GM-Mgmt'),
  (16,  250, 'GM-Impossible');
