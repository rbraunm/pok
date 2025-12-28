SELECT
  a.id                      AS account_,
  a.name                    AS account_,
  a.charname                AS account_,
  a.auto_login_charname     AS account_,
  a.sharedplat              AS account_,
  a.password                AS account_,
  a.status                  AS account_,
  a.ls_id                   AS account_,
  a.lsaccount_id            AS account_,
  a.gmspeed                 AS account_,
  a.invulnerable            AS account_,
  a.flymode                 AS account_,
  a.ignore_tells            AS account_,
  a.revoked                 AS account_,
  a.karma                   AS account_,
  a.minilogin_ip            AS account_,
  a.hideme                  AS account_,
  a.rulesflag               AS account_,
  a.suspendeduntil          AS account_,
  a.time_creation           AS account_,
  a.ban_reason              AS account_,
  a.suspend_reason          AS account_,
  a.crc_eqgame              AS account_,
  a.crc_skillcaps           AS account_,
  a.crc_basedata            AS account_
FROM account a

/* Test restrictions, remove when done testing*/
LIMIT 1;
