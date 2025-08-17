from db import getDb
from applogging import get_logger
logger = get_logger(__name__)

def list_tables():
  sql = "SHOW TABLES"
  with getDb().cursor() as cur:
    cur.execute(sql)
    return [row[0] if isinstance(row, (list, tuple)) else list(row.values())[0] for row in cur.fetchall()]

def describe_table(table:str):
  sql = f"DESCRIBE {table}"
  with getDb().cursor() as cur:
    cur.execute(sql)
    return cur.fetchall()
