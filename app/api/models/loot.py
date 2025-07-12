from api import getDb

def get_drop_locations(item_id:int):
  sql = """
    SELECT
      lt.id                        AS loottable_id,
      lde.chance                   AS base_chance,
      le.multiplier                AS multiplier,
      lde.chance * le.multiplier   AS effective_chance,
      z.short_name                 AS zone_shortname,
      z.long_name                  AS zone_longname,
      nt.name                      AS npc_name,
      nt.lastname                  AS npc_lastname,
      nt.level,
      nt.maxlevel,
      GROUP_CONCAT(
        CONCAT(
          ROUND(s2.y,1), ', ',
          ROUND(s2.x,1), ', ',
          ROUND(s2.z,1)
        ) SEPARATOR '<br>'
      ) AS spawn_points
    FROM lootdrop_entries lde
      JOIN loottable_entries le  ON lde.lootdrop_id = le.lootdrop_id
      JOIN loottable         lt  ON le.loottable_id = lt.id
      JOIN npc_types         nt  ON lt.id = nt.loottable_id
      JOIN spawnentry        se  ON nt.id = se.npcID
      JOIN spawn2            s2  ON se.spawngroupID = s2.spawngroupID
      JOIN zone              z   ON s2.zone = z.short_name
    WHERE lde.item_id = %s
      AND z.peqzone = 1
    GROUP BY lt.id, nt.id, s2.zone
    ORDER BY z.long_name, effective_chance DESC
  """
  with getDb().cursor() as cur:
    cur.execute(sql, (item_id,))
    return cur.fetchall()
