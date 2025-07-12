from api import getDb

def get_sample(table, limit=100):
  with getDb().cursor() as cur:
    cur.execute(f"SELECT * FROM {table} LIMIT %s", (limit,))
    return cur.fetchall()

def sample_tables(table_list, limit=100):
  return {t: get_sample(t, limit) for t in table_list}
