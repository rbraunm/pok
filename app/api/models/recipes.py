from api.db import getDb

def get_recipe_name(recipe_id:int):
  sql = "SELECT name FROM recipes WHERE id = %s"
  with getDb().cursor() as cur:
    cur.execute(sql, (recipe_id,))
    row = cur.fetchone()
  return row['name'] if row else None

def search_recipes(query:str, limit:int=15):
  like = f"%{query}%"
  prefix = f"{query}%"
  sql = """
    SELECT id, name
    FROM recipes
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

def get_recipe_details(recipe_id:int):
  sql_meta = "SELECT * FROM recipes WHERE id = %s"
  sql_entries = """
    SELECT e.item_id, i.name, e.componentcount, e.success
    FROM tradeskill_recipe_entries e
    JOIN items i ON i.id = e.item_id
    WHERE e.recipe_id=%s
  """
  db = getDb()
  with db.cursor() as cur:
    cur.execute(sql_meta, (recipe_id,))
    meta = cur.fetchone()
  if not meta:
    return None
  with db.cursor() as cur:
    cur.execute(sql_entries, (recipe_id,))
    meta['entries'] = cur.fetchall()
  return meta
