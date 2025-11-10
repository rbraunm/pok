CREATE TABLE `spawn_variants`(
  -- Identity and zone context
  npc_spawn_id           INT UNSIGNED NOT NULL,
  npc_spawngroup_id      INT UNSIGNED NOT NULL,
  zone_id                INT UNSIGNED NOT NULL,
  zone_short_name        VARCHAR(64)  NOT NULL,
  zone_long_name         VARCHAR(256) NOT NULL,

  -- Location (EQ ordering Y, X, Z)
  npc_spawn_y            DECIMAL(11,3) NOT NULL,
  npc_spawn_x            DECIMAL(11,3) NOT NULL,
  npc_spawn_z            DECIMAL(11,3) NOT NULL,
  npc_spawn_heading      DECIMAL(8,3)  NOT NULL,
  npc_spawn_time         INT SIGNED    NOT NULL,
  npc_spawn_variance     INT SIGNED    NOT NULL,
  npc_path_id            INT UNSIGNED  NOT NULL,

  -- Spawnpoint gating snapshot
  spawn_cond_id             INT UNSIGNED  NOT NULL,
  spawn_cond_value_required INT           NOT NULL,

  -- Candidate NPC
  npc_id                 INT UNSIGNED  NOT NULL,
  npc_name               VARCHAR(128)  NOT NULL,
  npc_label              VARCHAR(128)  NULL,
  npc_level_min          TINYINT UNSIGNED NOT NULL,
  npc_level_max          TINYINT UNSIGNED NOT NULL,
  npc_rare               TINYINT(1)    NOT NULL,
  npc_raid               TINYINT(1)    NOT NULL,
  npc_spawn_chance       DECIMAL(9,6)  NOT NULL,

  PRIMARY KEY (npc_spawn_id, npc_id),
  KEY ix_zone_id (zone_id),
  KEY ix_zone_name (zone_short_name),
  KEY ix_group (npc_spawngroup_id),
  KEY ix_npc (npc_id)
);

SELECT
  s2.id                                   AS npc_spawn_id,
  s2.spawngroupID                         AS npc_spawngroup_id,
  z.zoneidnumber                          AS zone_id,
  z.short_name                            AS zone_short_name,
  z.long_name                             AS zone_long_name,

  ROUND(s2.y, 3)                          AS npc_spawn_y,
  ROUND(s2.x, 3)                          AS npc_spawn_x,
  ROUND(s2.z, 3)                          AS npc_spawn_z,
  ROUND(s2.heading, 3)                    AS npc_spawn_heading,
  s2.respawntime                          AS npc_spawn_time,
  s2.variance                             AS npc_spawn_variance,
  s2.pathgrid                             AS npc_path_id,

  s2._condition                           AS spawn_cond_id,
  s2.cond_value                           AS spawn_cond_value_required,

  nt.id                                   AS npc_id,
  nt.name                                 AS npc_name,
  nt.lastname                             AS npc_label,
  nt.level                                AS npc_level_min,
  CASE WHEN nt.maxlevel IS NULL OR nt.maxlevel = 0
       THEN nt.level ELSE GREATEST(nt.level, nt.maxlevel)
  END                                     AS npc_level_max,
  nt.rare_spawn                           AS npc_rare,
  nt.raid_target                          AS npc_raid,
  CAST(se.chance AS DECIMAL(9,6))         AS npc_spawn_chance

FROM spawnentry se
JOIN spawn2 s2        ON s2.spawngroupID = se.spawngroupID
JOIN npc_types nt     ON nt.id           = se.npcID
JOIN (
  SELECT z1.*
  FROM zone z1
  WHERE z1.min_status = 0
    AND z1.cancombat  = 1
    AND (z1.min_expansion <= pok_get_eqemu_expansion())
    AND (z1.max_expansion = -1 OR z1.max_expansion >= pok_get_eqemu_expansion())
    AND NOT EXISTS (
      SELECT 1 FROM zone z2
      WHERE z2.short_name = z1.short_name
        AND z2.min_status = 0
        AND z2.cancombat  = 1
        AND (z2.min_expansion <= pok_get_eqemu_expansion())
        AND (z2.max_expansion = -1 OR z2.max_expansion >= pok_get_eqemu_expansion())
        AND z2.version > z1.version
    )
) z ON z.short_name = s2.zone
WHERE se.chance > 0
  AND (s2.min_expansion <= pok_get_eqemu_expansion())
  AND (s2.max_expansion = -1 OR s2.max_expansion >= pok_get_eqemu_expansion())
  AND (se.min_expansion <= pok_get_eqemu_expansion())
  AND (se.max_expansion = -1 OR se.max_expansion >= pok_get_eqemu_expansion());