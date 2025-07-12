from api import getDb

def search_items(query:str, limit:int=15):
  like = f"%{query}%"
  prefix = f"{query}%"
  sql = """
    SELECT id, name
    FROM items
    WHERE CAST(id AS CHAR) LIKE %(like)s OR name LIKE %(like)s
    ORDER BY
      CASE
        WHEN name LIKE %(prefix)s THEN 0
        WHEN CAST(id AS CHAR) LIKE %(prefix)s THEN 1
        ELSE 2
      END,
      name
    LIMIT %(limit)s
  """
  with getDb().cursor() as cur:
    cur.execute(sql, {'like': like, 'prefix': prefix, 'limit': limit})
    return cur.fetchall()

def get_item(item_id:int):
  sql = "SELECT * FROM items WHERE id = %s"
  with getDb().cursor() as cur:
    cur.execute(sql, (item_id,))
    return cur.fetchone()
