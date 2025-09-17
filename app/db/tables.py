import sys
import re
from applogging import get_logger
from db import DB_PREFIX

logger = get_logger(__name__)

TABLE_SQL = [
  f"""
CREATE TABLE IF NOT EXISTS {DB_PREFIX}_item_sources (
  item_id                 INT PRIMARY KEY,
  lootdropEntries         TEXT,
  merchantListEntries     TEXT,
  tradeskillRecipeEntries TEXT,
  questEntries            TEXT
)""",
  f"""
CREATE TABLE IF NOT EXISTS {DB_PREFIX}_eqemu_classes (
  id            SMALLINT PRIMARY KEY,
  name          VARCHAR(64)                                                      NOT NULL,
  category      ENUM('player_class','guildmaster','merchant','banker','service') NOT NULL,
  short_name    CHAR(3)                                                          NULL
)""",
  f"""
CREATE TABLE IF NOT EXISTS {DB_PREFIX}_eqemu_special_abilities (
  id            SMALLINT PRIMARY KEY,
  name          VARCHAR(64)                                       NOT NULL,
  category      ENUM('offense','defense','behavior','immunity')   NOT NULL,
  display_name  VARCHAR(64)                                       NOT NULL,
  details       TEXT                                              NOT NULL
)""",
]

SEED_DATA = {
  "eqemu_classes": [
    (1,   'Warrior',                       'player_class',   'WAR'),
    (2,   'Cleric',                        'player_class',   'CLR'),
    (3,   'Paladin',                       'player_class',   'PAL'),
    (4,   'Ranger',                        'player_class',   'RNG'),
    (5,   'Shadow Knight',                 'player_class',   'SHD'),
    (6,   'Druid',                         'player_class',   'DRU'),
    (7,   'Monk',                          'player_class',   'MON'),
    (8,   'Bard',                          'player_class',   'BRD'),
    (9,   'Rogue',                         'player_class',   'ROG'),
    (10,  'Shaman',                        'player_class',   'SHM'),
    (11,  'Necromancer',                   'player_class',   'NEC'),
    (12,  'Wizard',                        'player_class',   'WIZ'),
    (13,  'Magician',                      'player_class',   'MAG'),
    (14,  'Enchanter',                     'player_class',   'ENC'),
    (15,  'Beastlord',                     'player_class',   'BST'),
    (16,  'Berserker',                     'player_class',   'BER'),

    (20,  'Warrior Guildmaster',           'guildmaster',    None),
    (21,  'Cleric Guildmaster',            'guildmaster',    None),
    (22,  'Paladin Guildmaster',           'guildmaster',    None),
    (23,  'Ranger Guildmaster',            'guildmaster',    None),
    (24,  'Shadow Knight Guildmaster',     'guildmaster',    None),
    (25,  'Druid Guildmaster',             'guildmaster',    None),
    (26,  'Monk Guildmaster',              'guildmaster',    None),
    (27,  'Bard Guildmaster',              'guildmaster',    None),
    (28,  'Rogue Guildmaster',             'guildmaster',    None),
    (29,  'Shaman Guildmaster',            'guildmaster',    None),
    (30,  'Necromancer Guildmaster',       'guildmaster',    None),
    (31,  'Wizard Guildmaster',            'guildmaster',    None),
    (32,  'Magician Guildmaster',          'guildmaster',    None),
    (33,  'Enchanter Guildmaster',         'guildmaster',    None),
    (34,  'Beastlord Guildmaster',         'guildmaster',    None),
    (35,  'Berserker Guildmaster',         'guildmaster',    None),

    (40,  'Banker',                        'banker',         None),
    (41,  'Merchant',                      'merchant',       None),
    (59,  'Discord Merchant (PVP Points)', 'merchant',       None),
    (60,  'Adventure Recruiter',           'service',        None),
    (61,  'Adventure Merchant',            'merchant',       None),
    (63,  'Tribute Master',                'service',        None),
    (64,  'Guild Tribute Master',          'service',        None),
    (66,  'Guild Banker',                  'banker',         None),
    (67,  "Norrath's Keeper Merchant",     'merchant',       None),
    (68,  'Dark Reign Merchant',           'merchant',       None),
    (69,  'Fellowship Master',             'service',        None),
    (70,  'Alternate Currency Merchant',   'merchant',       None),
    (71,  'Mercenary Liaison',             'service',        None),
  ],
  "eqemu_special_abilities": [
    (1,  'Summon',                        'behavior',   'Summon',                 'Summon target→NPC or NPC→target; supports cooldown (ms) and HP% threshold.'),
    (2,  'Enrage',                        'defense',    'Enrage',                 'Begins at HP% threshold; ripostes incoming melee; duration and cooldown in ms.'),
    (3,  'Rampage',                       'offense',    'Rampage',                'Extra attacks on additional targets; params for proc%, target count, dmg%, flat dmg, AC ignore, crit mods.'),
    (4,  'Area Rampage',                  'offense',    'AE Rampage',             'Rampage that hits all in range (or N targets); same tunables as Rampage.'),
    (5,  'Flurry',                        'offense',    'Flurry',                 'Chance to add extra swings; params for proc%, added hits, dmg%, flat dmg, AC ignore, crit mods.'),
    (6,  'Triple Attack',                 'offense',    'Triple Attack',          'Enables three melee swings per round.'),
    (7,  'Quad Attack',                   'offense',    'Quad Attack',            'Enables four melee swings per round.'),
    (8,  'Dual Wield',                    'offense',    'Dual Wield',             'Allows off-hand weapon attack.'),
    (9,  'Bane Attack',                   'offense',    'Bane Attack',            'Can damage targets requiring bane-type weapons.'),
    (10, 'Magical Attack',                'offense',    'Magical Attack',         'Can damage targets requiring magical weapons.'),
    (11, 'Ranged Attack',                 'offense',    'Ranged Attack',          'Uses ranged attacks out of melee; params: min/max range, hit% mod, dmg% mod.'),
    (12, 'Unslowable',                    'immunity',   'Slow',                   'Immune to slow effects.'),
    (13, 'Unmezable',                     'immunity',   'Mez',                    'Immune to mesmerize.'),
    (14, 'Uncharmable',                   'immunity',   'Charm',                  'Immune to charm.'),
    (15, 'Unstunable',                    'immunity',   'Stun',                   'Immune to stun.'),
    (16, 'Unsnareable',                   'immunity',   'Snare',                  'Immune to snare.'),
    (17, 'Unfearable',                    'immunity',   'Fear',                   'Immune to fear.'),
    (18, 'Immune to Dispell',             'immunity',   'Dispel',                 'Immune to dispel effects.'),
    (19, 'Immune to Melee',               'immunity',   'Melee',                  'Immune to all melee damage.'),
    (20, 'Immune to Magic',               'immunity',   'Magic',                  'Immune to all magic spells.'),
    (21, 'Immune to Fleeing',             'behavior',   "Doesn't Flee",           'Will never flee at low HP.'),
    (22, 'Immune to Non-Bane Damage',     'immunity',   'Non-Bane',               'Only damaged by correct bane-type weapons.'),
    (23, 'Immune to Non-Magical Damage',  'immunity',   'Non-Magical',            'Only damaged by magical weapons.'),
    (24, 'Will Not Aggro',                'behavior',   "Doesn't Aggro",          'Players cannot enter its hate list.'),
    (25, 'Immune to Aggro',               'immunity',   'Immune to Aggro',        'Cannot be added to any hate list.'),
    (26, 'Resist Ranged Spells',          'defense',    'Belly Caster',           'Blocks spells cast outside melee range (“belly cast” required).'),
    (27, 'See through Feign Death',       'immunity',   'Feign Death',            'Detects FD; FD players can still be aggro’d/kept on hate.'),
    (28, 'Immune to Taunt',               'immunity',   'Taunt',                  'Taunt has no effect.'),
    (29, 'Tunnel Vision',                 'behavior',   'Tunnel Vision',          'Hate from non-top targets is scaled by an aggro modifier param.'),
    (30, 'Does NOT buff/heal friends',    'behavior',   'No Ally Buff/Heal',      'Won’t cast beneficial spells on same-faction allies.'),
    (31, 'Unpacifiable',                  'immunity',   'Pacify',                 'Immune to pacify/lull.'),
    (32, 'Leashed',                       'behavior',   'Leashed',                'If pulled past leash distance, returns home, fully heals, wipes hate; param sets distance.'),
    (33, 'Tethered',                      'behavior',   'Tethered',               'Hard tether near aggro range; param sets leash distance before snap-back.'),
    (34, 'Destructible Object',           'behavior',   'Destructible',           'For destructible NPC objects (deprecated); simple on/off.'),
    (35, 'No Harm from Players',          'immunity',   'All Player Damage',      'Players cannot harm it by any means.'),
    (36, 'Always Flee',                   'behavior',   'Always Flee',            'Will flee at low HP regardless of ally proximity.'),
    (37, 'Flee Percentage',               'behavior',   'Flee at %',              'Flees at specified HP%; ignores ally checks; param = HP%.'),
    (38, 'Allow Beneficial',              'behavior',   'Allow Beneficial',       'Players may cast beneficial spells on this NPC.'),
    (39, 'Disable Melee',                 'behavior',   'Disable Melee',          'Cannot perform melee attacks; can still aggro.'),
    (40, 'Chase Distance',                'behavior',   'Chase Distance',         'Sets max/min chase distances; optional ignore-LOS flag.'),
    (41, 'Allow Tank',                    'behavior',   'Allow Tank',             'Allows other NPCs to take aggro from players.'),
    (42, 'Ignore Root Aggro',             'behavior',   'Ignore Root Aggro',      'While rooted, attacks hate-top, not nearest target.'),
    (43, 'Casting Resist Diff',           'offense',    'Casting Resist Mod',     'Applies a flat resist-difficulty modifier to spells cast by this NPC; negative = easier to land, positive = harder to land.'),
    (44, 'Counter Avoid Damage',          'offense',    'Lower Opponent Avoid',   'Reduces a client’s avoidance (dodge/parry/block/riposte) via flat % params; increases NPC hit rate.'),
    (45, 'Proximity Aggro',               'behavior',   'Proximity Aggro',        'Can add new nearby clients to hate while already in combat.'),
    (46, 'Immune Ranged Attacks',         'immunity',   'Ranged Attacks',         'Immune to ranged weapon damage.'),
    (47, 'Immune Client Damage',          'immunity',   'Players',                'Immune to damage from players.'),
    (48, 'Immune NPC Damage',             'immunity',   'NPCs',                   'Immune to damage from NPCs.'),
    (49, 'Immune Client Aggro',           'immunity',   'Player Aggro',           'Players cannot generate aggro on it.'),
    (50, 'Immune NPC Aggro',              'immunity',   'NPC Aggro',              'NPCs cannot generate aggro on it.'),
    (51, 'Modify Avoid Damage',           'defense',    'Raise Avoidance',        'Increases this NPC’s avoidance (all or specific skills) via flat % params.'),
    (52, 'Immune Fading Memories',        'immunity',   'Fading Memories',        'Immune to memory-fade/aggro-wipe effects.'),
    (53, 'Immune to Open',                'immunity',   'Open',                   'Immune to /open.'),
    (54, 'Immune to Assassinate',         'immunity',   'Assassinate',            'Immune to Rogue Assassinate.'),
    (55, 'Immune to Headshot',            'immunity',   'Headshot',               'Immune to Ranger Headshot.'),
    (56, 'Immune to Bot Aggro',           'immunity',   'Bot Aggro',              'Bots cannot generate aggro on it.'),
    (57, 'Immune to Bot Damage',          'immunity',   'Bots',                   'Immune to damage from bots.')
  ]
}

def _fetch_table_columns(cur, full_table_name):
  cur.execute(
    """
    SELECT COLUMN_NAME, LOWER(COALESCE(EXTRA,'')) AS extra
    FROM INFORMATION_SCHEMA.COLUMNS
    WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = %s
    ORDER BY ORDINAL_POSITION
    """,
    (full_table_name,)
  )
  cols = []
  for row in cur.fetchall() or []:
    name = row["COLUMN_NAME"] if isinstance(row, dict) else row[0]
    extra = row["extra"] if isinstance(row, dict) else row[1]
    if "generated" in (extra or ""):
      continue
    cols.append(name)
  return cols

def _gen_upsert_sql(full_table_name, columns):
  cols_sql = ", ".join(f"`{c}`" for c in columns)
  placeholders = ", ".join(["%s"] * len(columns))
  updates = ", ".join(f"`{c}`=VALUES(`{c}`)" for c in columns)
  return f"""INSERT INTO `{full_table_name}` ({cols_sql})
VALUES ({placeholders})
ON DUPLICATE KEY UPDATE {updates}"""

def _drop_prefixed_tables(cur):
  cur.execute("SET FOREIGN_KEY_CHECKS=0")
  cur.execute(
    """
    SELECT TABLE_NAME
    FROM INFORMATION_SCHEMA.TABLES
    WHERE TABLE_SCHEMA = DATABASE()
      AND TABLE_TYPE = 'BASE TABLE' AND LEFT(TABLE_NAME, CHAR_LENGTH(CONCAT(%s, '_'))) = CONCAT(%s, '_')
    """,
    (DB_PREFIX, DB_PREFIX)
  )
  for row in cur.fetchall() or []:
    t = row["TABLE_NAME"] if isinstance(row, dict) else row[0]
    cur.execute(f"DROP TABLE IF EXISTS `{t}`")
    logger.info(f"Dropped table `{t}`")
  cur.execute("SET FOREIGN_KEY_CHECKS=1")

def initializeTables(db):
  logger.info("Initializing tables...")
  ENGINE_CLAUSE = " ENGINE=InnoDB DEFAULT CHARSET=utf8mb4"

  created = 0
  seeded_tables = 0
  seeded_rows_total = 0

  with db.cursor() as cur:
    cur.execute(
      """
      SELECT COUNT(*) AS cnt
      FROM INFORMATION_SCHEMA.TABLES
      WHERE TABLE_SCHEMA = DATABASE()
        AND TABLE_TYPE = 'BASE TABLE' AND LEFT(TABLE_NAME, CHAR_LENGTH(CONCAT(%s, '_'))) = CONCAT(%s, '_')
      """,
      (DB_PREFIX, DB_PREFIX)
    )
    row = cur.fetchone() or {}
    to_drop = int((row["cnt"] if isinstance(row, dict) else row[0]) or 0)

    _drop_prefixed_tables(cur)

    for ddl in TABLE_SQL:
      m = re.search(r'CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?`?([A-Za-z0-9_]+)`?', ddl, re.IGNORECASE)
      name = m.group(1) if m else None
      cur.execute(f"{ddl} {ENGINE_CLAUSE}")
      created += 1
      logger.info(f"Created table `{name}`" if name else "Created table")

    # Seed pass
    cur.execute(
      """
      SELECT TABLE_NAME
      FROM INFORMATION_SCHEMA.TABLES
      WHERE TABLE_SCHEMA = DATABASE()
        AND TABLE_TYPE = 'BASE TABLE' AND LEFT(TABLE_NAME, CHAR_LENGTH(CONCAT(%s, '_'))) = CONCAT(%s, '_')
      """,
      (DB_PREFIX, DB_PREFIX)
    )
    prefixed_tables = [r["TABLE_NAME"] if isinstance(r, dict) else r[0] for r in (cur.fetchall() or [])]

    for full_name in prefixed_tables:
      base = full_name[len(DB_PREFIX) + 1:]
      rows = SEED_DATA.get(base)
      if not rows:
        continue

      cols = _fetch_table_columns(cur, full_name)
      if not cols:
        logger.exception(f"Fatal: could not fetch columns for `{full_name}`")
        raise RuntimeError("missing columns")

      if any(len(r) != len(cols) for r in rows):
        logger.exception(
          f"Fatal: seed row length mismatch for `{full_name}` "
          f"(expected {len(cols)} values per row)"
        )
        raise ValueError("seed row length mismatch")

      sql = _gen_upsert_sql(full_name, cols)
      for r in rows:
        cur.execute(sql, r)
      seeded_tables += 1
      seeded_rows_total += len(rows)
      logger.info(f"Seeded `{full_name}` ({len(rows)} rows)")

  db.commit()
  logger.info(
    "Tables init complete: dropped=%s, created=%s; seeded_tables=%s, seeded_rows=%s.",
    to_drop, created, seeded_tables, seeded_rows_total
  )