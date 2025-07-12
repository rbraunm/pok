NAME = "Recipe Finder"

from pathlib import Path
URL_PREFIX = "/" + Path(__file__).stem.lower()

from flask import request, jsonify
from app import renderPage
import re
from api.models.recipes import get_recipe_name, search_recipes, get_recipe_details

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
      recipeName = get_recipe_name(recipeId)
      recipeDetails = get_recipe_details(recipeId)
    else:
      recipeDetails = None

    header = f"""
<div class="headerRow">
  <h1>{NAME}</h1>
</div>"""

    body = ""
    if recipeDetails:
      body += f"<h2>{recipeName} (ID {recipeId})</h2>"
      body += f"<p>Tradeskill: {recipeDetails.get('tradeskill')} | Skill Needed: {recipeDetails.get('skillneeded')} | Trivial: {recipeDetails.get('trivial')}</p>"
      body += "<h3>Components</h3><ul>"
      for e in recipeDetails['entries']:
        if e['success'] == 0:
          body += f"<li>{e['componentcount']} × {e['name']} (ID {e['item_id']})</li>"
      body += "</ul>"
    elif recipeId:
      body += "<p>No recipe found.</p>"

    return renderPage(header, body)

  @app.route(f"{URL_PREFIX}/search")
  def recipe_search():
    q = request.args.get("q", "").strip()
    if not q:
      return jsonify(results=[])
    results = search_recipes(q)
    return jsonify(results=[{'id': r['id'], 'name': r['name']} for r in results])
