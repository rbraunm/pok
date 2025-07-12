NAME = "Recipe Finder"
URL_PREFIX = "/recipefinder"

from flask import request, jsonify
from db import getDb
from app import renderPage
import re

def register(app):
  @app.route(URL_PREFIX, methods=["GET"])
  def recipefinder():
    recipeRaw = request.args.get("recipe_id", "").strip()
    recipeId = None
    recipeName = None

    match = re.search(r"\((\d+)\)$", recipeRaw)
    if match:
      recipeId = int(match.group(1))
    elif recipeRaw.isdigit():
      recipeId = int(recipeRaw)

    if recipeId is not None:
      db = getDb()
      with db.cursor() as cur:
        cur.execute("SELECT name FROM recipes WHERE id = %s", (recipeId,))
        row = cur.fetchone()
        if row:
          recipeName = row["name"]

    header = f"""
<h1>Recipe Finder</h1>
<form action="{URL_PREFIX}" method="get" autocomplete="off">
  <input type="text" id="recipeInput" name="recipe_id" placeholder="Enter recipe ID or name" value="{recipeName + f' ({recipeId})' if recipeId and recipeName else recipeId or ''}">
  <button type="submit">Search</button>
  <div id="autocomplete" class="autocomplete-suggestions" style="display:none;"></div>
</form>
<script>
const input = document.getElementById('recipeInput');
const box = document.getElementById('autocomplete');

input.addEventListener('focus', () => {{
  input.value = "";
  box.style.display = "none";
}});

input.addEventListener('input', () => {{
  const q = input.value;
  if (q.length < 2) return box.style.display = 'none';

  fetch('{URL_PREFIX}/search?q=' + encodeURIComponent(q))
    .then(res => res.json())
    .then(data => {{
      if (!data.results.length) return box.style.display = 'none';
      box.innerHTML = data.results.map(r =>
        `<div data-id="${{r.id}}" data-name="${{r.name}}">${{r.name}} (${{r.id}})</div>`
      ).join('');
      box.style.display = 'block';
    }});
}});

box.addEventListener('click', (e) => {{
  const div = e.target.closest('div');
  if (!div) return;
  const displayValue = `${{div.dataset.name}} (${{div.dataset.id}})`;
  input.value = displayValue;

  const form = input.closest("form");
  const hiddenInput = document.createElement("input");
  hiddenInput.type = "hidden";
  hiddenInput.name = "recipe_id";
  hiddenInput.value = div.dataset.id;
  form.appendChild(hiddenInput);
  form.submit();
}});

document.addEventListener('click', e => {{
  if (!box.contains(e.target) && e.target !== input) {{
    box.style.display = 'none';
  }}
}});
</script>
"""

    body = ""
    if recipeId and recipeName:
      body = f"<p>You selected <strong>{recipeName}</strong> (ID {recipeId}).</p>"
    elif recipeId:
      body = f"<p>You selected recipe ID <strong>{recipeId}</strong>, but it wasn't found in the database.</p>"

    return renderPage(header, body)

  @app.route(f"{URL_PREFIX}/search")
  def recipefinder_search():
    q = request.args.get("q", "").strip()
    if not q:
      return jsonify(results=[])

    db = getDb()
    query = """
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
      LIMIT 15
    """
    like = f"%{q}%"
    prefix = f"{q}%"

    with db.cursor() as cur:
      cur.execute(query, {"like": like, "prefix": prefix})
      results = [{"id": r["id"], "name": r["name"]} for r in cur.fetchall()]

    return jsonify(results=results)
