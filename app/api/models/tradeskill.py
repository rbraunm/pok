from api import getDb

def get_recipes_for_item(item_id:int):
  sql = """
    SELECT id, tradeskill, skillneeded, trivial
    FROM tradeskill_recipe
    WHERE id IN (
      SELECT recipe_id
      FROM tradeskill_recipe_entries
      WHERE item_id=%s AND success=1
    )
  """
  with getDb().cursor() as cur:
    cur.execute(sql, (item_id,))
    return cur.fetchall()
