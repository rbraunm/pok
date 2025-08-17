from db import getDb
from applogging import get_logger
logger = get_logger(__name__)

def get_current_expansion() -> int:
  sql = """
    SELECT rule_value
    FROM rule_values
    WHERE rule_name = 'Expansion:CurrentExpansion'
    LIMIT 1
  """
  with getDb().cursor() as cur:
    cur.execute(sql)
    row = cur.fetchone()
    if row and "rule_value" in row:
      return int(row["rule_value"])
    return -1
