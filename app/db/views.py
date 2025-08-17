import re
import difflib
from db import DB_PREFIX
from applogging import get_logger
logger = get_logger(__name__)
VIEW_PREFIX = f'{DB_PREFIX}'
PRESERVE_DEFINER = False

def _viewDefs():
    defs = []
    defs.append(('items_purchased_coin', "\n    SELECT\n      CAST(NULL AS SIGNED) AS item_id,\n      'purchased_coin'     AS source_type,\n      CAST(NULL AS SIGNED) AS source_id,\n      CAST(NULL AS SIGNED) AS source_ref,\n      NULL                 AS zone_short,\n      NULL                 AS zone_long,\n      NULL                 AS extra\n    WHERE 0\n  "))
    defs.append(('items_ground_spawns', "\n    SELECT\n      CAST(NULL AS SIGNED) AS item_id,\n      'ground_spawn'       AS source_type,\n      CAST(NULL AS SIGNED) AS source_id,\n      CAST(NULL AS SIGNED) AS source_ref,\n      NULL                 AS zone_short,\n      NULL                 AS zone_long,\n      NULL                 AS extra\n    WHERE 0\n  "))
    defs.append(('items_foraged', "\n    SELECT\n      CAST(NULL AS SIGNED) AS item_id,\n      'foraged'            AS source_type,\n      CAST(NULL AS SIGNED) AS source_id,\n      CAST(NULL AS SIGNED) AS source_ref,\n      NULL                 AS zone_short,\n      NULL                 AS zone_long,\n      NULL                 AS extra\n    WHERE 0\n  "))
    defs.append(('items_fished', "\n    SELECT\n      CAST(NULL AS SIGNED) AS item_id,\n      'fished'             AS source_type,\n      CAST(NULL AS SIGNED) AS source_id,\n      CAST(NULL AS SIGNED) AS source_ref,\n      NULL                 AS zone_short,\n      NULL                 AS zone_long,\n      NULL                 AS extra\n    WHERE 0\n  "))
    defs.append(('items_starting_items', "\n    SELECT\n      CAST(NULL AS SIGNED) AS item_id,\n      'starting_item'      AS source_type,\n      CAST(NULL AS SIGNED) AS source_id,\n      CAST(NULL AS SIGNED) AS source_ref,\n      NULL                 AS zone_short,\n      NULL                 AS zone_long,\n      NULL                 AS extra\n    WHERE 0\n  "))
    defs.append(('items_crafted', "\n    SELECT\n      CAST(NULL AS SIGNED) AS item_id,\n      'crafted'            AS source_type,\n      CAST(NULL AS SIGNED) AS source_id,\n      CAST(NULL AS SIGNED) AS source_ref,\n      NULL                 AS zone_short,\n      NULL                 AS zone_long,\n      NULL                 AS extra\n    WHERE 0\n  "))
    defs.append(('items_npc_loot', "\n    SELECT\n      CAST(NULL AS SIGNED) AS item_id,\n      'npc_loot'           AS source_type,\n      CAST(NULL AS SIGNED) AS source_id,\n      CAST(NULL AS SIGNED) AS source_ref,\n      NULL                 AS zone_short,\n      NULL                 AS zone_long,\n      NULL                 AS extra\n    WHERE 0\n  "))
    defs.append(('items_global_loot', "\n    SELECT\n      CAST(NULL AS SIGNED) AS item_id,\n      'global_loot'        AS source_type,\n      CAST(NULL AS SIGNED) AS source_id,\n      CAST(NULL AS SIGNED) AS source_ref,\n      NULL                 AS zone_short,\n      NULL                 AS zone_long,\n      NULL                 AS extra\n    WHERE 0\n  "))
    defs.append(('items_object_chest_loot', "\n    SELECT\n      CAST(NULL AS SIGNED) AS item_id,\n      'object_chest_loot'  AS source_type,\n      CAST(NULL AS SIGNED) AS source_id,\n      CAST(NULL AS SIGNED) AS source_ref,\n      NULL                 AS zone_short,\n      NULL                 AS zone_long,\n      NULL                 AS extra\n    WHERE 0\n  "))
    defs.append(('items_purchased_alt_currency', "\n    SELECT\n      CAST(NULL AS SIGNED) AS item_id,\n      'purchased_alt_currency' AS source_type,\n      CAST(NULL AS SIGNED) AS source_id,\n      CAST(NULL AS SIGNED) AS source_ref,\n      NULL                 AS zone_short,\n      NULL                 AS zone_long,\n      NULL                 AS extra\n    WHERE 0\n  "))
    defs.append(('items_task_rewards', "\n    SELECT\n      CAST(NULL AS SIGNED) AS item_id,\n      'task_reward'        AS source_type,\n      CAST(NULL AS SIGNED) AS source_id,\n      CAST(NULL AS SIGNED) AS source_ref,\n      NULL                 AS zone_short,\n      NULL                 AS zone_long,\n      NULL                 AS extra\n    WHERE 0\n  "))
    defs.append(('items_summoned_by_spells', "\n    SELECT\n      CAST(NULL AS SIGNED) AS item_id,\n      'summoned_by_spells' AS source_type,\n      CAST(NULL AS SIGNED) AS source_id,\n      CAST(NULL AS SIGNED) AS source_ref,\n      NULL                 AS zone_short,\n      NULL                 AS zone_long,\n      NULL                 AS extra\n    WHERE 0\n  "))
    defs.append(('items_quest_granted', "\n    SELECT\n      CAST(NULL AS SIGNED) AS item_id,\n      'quest_granted'      AS source_type,\n      CAST(NULL AS SIGNED) AS source_id,\n      CAST(NULL AS SIGNED) AS source_ref,\n      NULL                 AS zone_short,\n      NULL                 AS zone_long,\n      NULL                 AS extra\n    WHERE 0\n  "))
    defs.append(('items_scripted_ground_objects', "\n    SELECT\n      CAST(NULL AS SIGNED) AS item_id,\n      'scripted_ground_object' AS source_type,\n      CAST(NULL AS SIGNED) AS source_id,\n      CAST(NULL AS SIGNED) AS source_ref,\n      NULL                 AS zone_short,\n      NULL                 AS zone_long,\n      NULL                 AS extra\n    WHERE 0\n  "))
    defs.append(('items_instance_chest_rewards', "\n    SELECT\n      CAST(NULL AS SIGNED) AS item_id,\n      'instance_chest_reward' AS source_type,\n      CAST(NULL AS SIGNED) AS source_id,\n      CAST(NULL AS SIGNED) AS source_ref,\n      NULL                 AS zone_short,\n      NULL                 AS zone_long,\n      NULL                 AS extra\n    WHERE 0\n  "))
    defs.append(('items_pickpocket', "\n    SELECT\n      CAST(NULL AS SIGNED) AS item_id,\n      'pickpocket'         AS source_type,\n      CAST(NULL AS SIGNED) AS source_id,\n      CAST(NULL AS SIGNED) AS source_ref,\n      NULL                 AS zone_short,\n      NULL                 AS zone_long,\n      NULL                 AS extra\n    WHERE 0\n  "))
    defs.append(('items_begging', "\n    SELECT\n      CAST(NULL AS SIGNED) AS item_id,\n      'begging'            AS source_type,\n      CAST(NULL AS SIGNED) AS source_id,\n      CAST(NULL AS SIGNED) AS source_ref,\n      NULL                 AS zone_short,\n      NULL                 AS zone_long,\n      NULL                 AS extra\n    WHERE 0\n  "))
    defs.append(('items_account_claims', "\n    SELECT\n      CAST(NULL AS SIGNED) AS item_id,\n      'account_claim'      AS source_type,\n      CAST(NULL AS SIGNED) AS source_id,\n      CAST(NULL AS SIGNED) AS source_ref,\n      NULL                 AS zone_short,\n      NULL                 AS zone_long,\n      NULL                 AS extra\n    WHERE 0\n  "))
    return defs
_whitespace_re = re.compile('\\s+')
_hdr_re = re.compile('^create\\s+(?:or\\s+replace\\s+)?(?:(?:algorithm=\\w+|definer=`?[^`]+`?@`?[^`]+`?|sql\\s+security\\s+\\w+)\\s+)*view\\s+(?:`?[^`]+`?\\.)?`?[^`]+`?\\s*(?:\\([^)]+\\)\\s*)?as\\s+', re.I | re.S)

def _normalize_sql(sql: str) -> str:
    s = (sql or '').strip().rstrip(';')
    new_s = _hdr_re.sub('', s)
    if new_s == s and s[:6].lower() == 'create':
        logger.debug('views.py: header regex did not match SHOW CREATE VIEW output head')
    s = new_s
    s = re.sub('/\\*.*?\\*/', ' ', s, flags=re.S)
    s = re.sub('--[^\\n]*', ' ', s)
    s = s.replace('`', '')
    s = re.sub("_(?:utf8mb4|utf8|latin1)\\s*'", "'", s, flags=re.I)
    s = re.sub('\\s+collate\\s+[a-z0-9_]+', ' ', s, flags=re.I)
    s = re.sub('\\s+character\\s+set\\s+[a-z0-9_]+', ' ', s, flags=re.I)
    s = re.sub('cast\\s*\\(\\s*null\\s+as\\s+signed\\s*(?:int|integer)?\\s*\\)', 'cast(null as signed)', s, flags=re.I)
    s = re.sub('cast\\s*\\(\\s*null\\s+as\\s+unsigned\\s*(?:int|integer)?\\s*\\)', 'cast(null as unsigned)', s, flags=re.I)
    s = re.sub('\\s+from\\s+dual\\s+(?:as\\s+\\w+\\s+)?', ' ', s, flags=re.I)
    s = re.sub('\\s*,\\s*', ',', s)
    s = re.sub('\\s*\\(\\s*', '(', s)
    s = re.sub('\\s*\\)\\s*', ')', s)
    s = re.sub('\\s*=\\s*', '=', s)
    s = _whitespace_re.sub(' ', s).strip().lower()
    return s

def _desiredMap():
    wanted = {}
    for base, sel in _viewDefs():
        name = f'{VIEW_PREFIX}_{base}'
        wanted[name] = {'select_sql': sel, 'norm': _normalize_sql(sel)}
    return wanted

def _fetchExistingOurPrefix(cur):
    """
  Returns {view_name: {"norm": normalized_select, "definer": ..., "security": ...}}
  Prefer SHOW CREATE VIEW for stable server-side canonicalization; fall back to INFORMATION_SCHEMA.VIEWS.
  """
    cur.execute('\n    SELECT TABLE_NAME\n    FROM INFORMATION_SCHEMA.VIEWS\n    WHERE TABLE_NAME LIKE %s\n    ORDER BY TABLE_NAME\n  ', (f'{VIEW_PREFIX}_%',))
    names = [r['TABLE_NAME'] if isinstance(r, dict) else r[0] for r in cur.fetchall() or []]
    existing = {}
    for name in names:
        body = ''
        definer = None
        security = None
        try:
            cur.execute(f'SHOW CREATE VIEW `{name}`')
            row = cur.fetchone()
            if row:
                if isinstance(row, dict):
                    body = row.get('Create View') or ''
                else:
                    body = row[1] if len(row) > 1 else ''
        except Exception:
            body = ''
        if not body:
            try:
                cur.execute('\n          SELECT VIEW_DEFINITION, DEFINER, SECURITY_TYPE\n          FROM INFORMATION_SCHEMA.VIEWS\n          WHERE TABLE_NAME = %s\n        ', (name,))
                r = cur.fetchone()
                if r:
                    if isinstance(r, dict):
                        body = r.get('VIEW_DEFINITION') or ''
                        definer = r.get('DEFINER')
                        security = r.get('SECURITY_TYPE')
                    else:
                        body = r[0] or ''
                        definer = r[1] if len(r) > 1 else None
                        security = r[2] if len(r) > 2 else None
            except Exception:
                pass
        if PRESERVE_DEFINER and (definer is None or security is None):
            try:
                cur.execute('\n          SELECT DEFINER, SECURITY_TYPE\n          FROM INFORMATION_SCHEMA.VIEWS\n          WHERE TABLE_NAME = %s\n        ', (name,))
                r = cur.fetchone()
                if r:
                    if isinstance(r, dict):
                        definer = r.get('DEFINER')
                        security = r.get('SECURITY_TYPE')
                    else:
                        definer = r[0]
                        security = r[1] if len(r) > 1 else None
            except Exception:
                pass
        existing[name] = {'norm': _normalize_sql(body), 'definer': definer, 'security': security}
    return existing

def _fmt_definer(definer: str | None) -> str | None:
    if not definer or '@' not in definer:
        return None
    user, host = definer.split('@', 1)
    user = user.strip('`\'"')
    host = host.strip('`\'"')
    return f'DEFINER=`{user}`@`{host}`'

def _fmt_sql_security(security: str | None) -> str | None:
    if not security:
        return None
    sec = security.strip().upper()
    if sec in ('DEFINER', 'INVOKER'):
        return f'SQL SECURITY {sec}'
    return None

def _log_view_diff(name: str, have_norm: str | None, want_norm: str) -> None:
    have_norm = have_norm or '<none>'
    diff = '\n'.join(difflib.unified_diff(have_norm.split(), want_norm.split(), fromfile=f'{name}:have', tofile=f'{name}:want', lineterm=''))
    if diff:
        logger.debug(f'[views diff]\n{diff}')
    else:
        logger.debug(f'[views diff] have: {have_norm}')
        logger.debug(f'[views diff] want: {want_norm}')

def syncViews(db):
    """
  Upsert all defined views via CREATE OR REPLACE, and drop stray views with our prefix.
  """
    desired = _desiredMap()
    changed = False
    with db.cursor() as cur:
        existing = _fetchExistingOurPrefix(cur)
        for name in sorted(existing.keys()):
            if name not in desired:
                try:
                    cur.execute(f'DROP VIEW IF EXISTS `{name}`')
                    logger.info(f'Dropped stray view `{name}` (not in definitions)')
                    changed = True
                except Exception:
                    logger.exception(f'Failed to drop stray view `{name}`')
        for name, want in desired.items():
            have = existing.get(name)
            have_norm = have['norm'] if have else None
            want_norm = want['norm']
            if have_norm == want_norm:
                logger.info(f'View `{name}` is up-to-date; skipping')
                continue
            prefix_bits = []
            if PRESERVE_DEFINER and have:
                defFrag = _fmt_definer(have.get('definer'))
                secFrag = _fmt_sql_security(have.get('security'))
                if defFrag:
                    prefix_bits.append(defFrag)
                if secFrag:
                    prefix_bits.append(secFrag)
            prefix_sql = ' '.join(prefix_bits) + ' ' if prefix_bits else ''
            stmt = f"CREATE OR REPLACE {prefix_sql}VIEW `{name}` AS\n{want['select_sql']}"
            if have is not None:
                _log_view_diff(name, have_norm, want_norm)
            try:
                cur.execute(stmt)
                if have is None:
                    logger.info(f'Created view `{name}`')
                else:
                    logger.info(f'Replaced view `{name}` (definition changed)')
                changed = True
            except Exception:
                logger.exception(f'Upsert failed for view `{name}`')
    if changed:
        db.commit()

def initializeViews(db):
    logger.info('Checking views...')
    syncViews(db)
