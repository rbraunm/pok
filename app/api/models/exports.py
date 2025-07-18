from api import getDb
import pymysql.cursors
import re

_PLACEHOLDER   = "~private~"
_SENSITIVE_RGX = re.compile(r"(password|e-?mail)", re.IGNORECASE)

def _sanitize_row(row: dict) -> dict:
  return {
    col: (_PLACEHOLDER if _SENSITIVE_RGX.search(col) else val)
    for col, val in row.items()
  }

def get_sample(table: str, limit: int = 100):
  db = getDb()
  with db.cursor(pymysql.cursors.DictCursor) as cur:
    cur.execute(f"SELECT * FROM `{table}` LIMIT %s", (limit,))
    return [_sanitize_row(r) for r in cur.fetchall()]

def sample_tables(table_list, limit: int = 100):
  return {t: get_sample(t, limit) for t in table_list}
