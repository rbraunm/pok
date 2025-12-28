/* Strict currency resolution via a single join to pok_eqemu_currency_types */
SELECT
  ml.item                                           AS item_id,
  nt.id                                             AS npc_id,

  ml.faction_required                               AS merchant_item_faction_amount_required,
  pok_parse_faction_level_name(ml.faction_required) AS merchant_item_faction_name_required,
  ml.level_required                                 AS merchant_item_level_required,
  pok_parse_classes_bitmask(ml.classes_required)    AS merchant_item_classes_required,
  ml.probability                                    AS merchant_item_list_chance,
  ml.min_status                                     AS merchant_item_min_player_status_value,
  accr.id                                           AS merchant_item_min_player_status_id,
  accr.name                                         AS merchant_item_min_player_status_name,

  ct.short_name                                     AS merchant_currency_id,
  ct.name                                           AS merchant_currency_name,
  ct.id                                             AS merchant_currency_type_id,
  ct.icon_id                                        AS merchant_currency_icon_id,

  CASE
    WHEN nt.class = 70 AND nt.alt_currency_id > 0 THEN ml.alt_currency_cost
    WHEN nt.class = 61 AND COALESCE(i.ldonprice,0) > 0 THEN i.ldonprice
    WHEN nt.class IN (67, 68) THEN ml.alt_currency_cost
    ELSE i.price
  END                                               AS merchant_currency_price,


  -- Expansion / Content Gating
  ml.min_expansion                                  AS merchant_list_min_expansion,
  ml.max_expansion                                  AS merchant_list_max_expansion,
  ml.content_flags                                  AS merchant_list_content_flags_required,
  ml.content_flags_disabled                         AS merchant_list_content_flags_disabled

FROM merchantlist ml
JOIN items i                 ON i.id           = ml.item
JOIN npc_types nt            ON nt.merchant_id = ml.merchantid
LEFT JOIN alternate_currency ac ON ac.id       = nt.alt_currency_id
LEFT JOIN npc_faction nf        ON nf.id       = nt.npc_faction_id
LEFT JOIN faction_list fl       ON fl.id       = nf.primaryfaction
LEFT JOIN pok_eqemu_account_ranks accr ON accr.status = (
                                            SELECT MIN(accr2.status)
                                            FROM pok_eqemu_account_ranks accr2
                                            WHERE accr2.status >= COALESCE(i.minstatus, 0)
                                          )

/* One deterministic currency row per merchant item */
JOIN pok_eqemu_currency_types ct
  ON (
       /* Alt currency (class 70): match by the backing item_id from alternate_currency */
       (nt.class = 70 AND nt.alt_currency_id > 0 AND ct.item_id = ac.item_id)

    OR /* LDoN (class 61): match by item theme */
       (nt.class = 61 AND COALESCE(i.ldonprice,0) > 0 AND ct.ldon_theme_id = i.ldontheme)

    OR /* Legacy DoN classes: 68 = Ebon, 69 = Radiant */
       (nt.class IN (67, 68) AND ct.don_variant_id = CASE WHEN nt.class = 67 THEN 1 ELSE 2 END)

    OR /* Coin branch: bind explicitly to your 'copper' row (id = 1) */
       (nt.class NOT IN (61, 67, 68, 70) AND ct.id = 1)
     );
