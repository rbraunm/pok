SELECT
  -- Identity / Classification
  s.id          AS spell_id,
  s.Name        AS spell_name,

  -- Equip / Usage Constraints

  -- Icons
  s.icon        AS spell_legacy_icon_id, -- Not used in RoF2
  NULL          AS spell_legacy_icon_url, -- Not used in RoF2, intentionally null
  s.memicon     AS spell_legacy_gem_icon_id, -- Not used in RoF2
  NULL          AS spell_legacy_gem_icon_url, -- Not used in RoF2, intentionally null
  s.new_icon    AS spell_icon_id,
  CONCAT("gemicons",pok_get_icon_url(s.new_icon,10,10,0,0)) AS spell_gem_icon_url,
  CONCAT("spells",pok_get_icon_url(s.new_icon,6,6,0,0)) AS spell_book_icon_url

FROM spells_new s
LIMIT 5;
