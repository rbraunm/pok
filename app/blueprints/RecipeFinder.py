NAME = "Recipe Finder"

from pathlib import Path
URL_PREFIX = "/" + Path(__file__).stem

import re
from flask import request, json
from web.utils import renderPage
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

    htmlContent = f"""
      <div class="headerRow">
        <h1>{NAME}</h1>
      </div>"""

    if recipeDetails:
      htmlContent += f"<h2>{recipeName} (ID {recipeId})</h2>"
      htmlContent += f"<p>Tradeskill: {recipeDetails.get('tradeskill')} | Skill Needed: {recipeDetails.get('skillneeded')} | Trivial: {recipeDetails.get('trivial')}</p>"
      htmlContent += "<h3>Components</h3><ul>"
      for e in recipeDetails['entries']:
        if e['success'] == 0:
          htmlContent += f"<li>{e['componentcount']} × {e['name']} (ID {e['item_id']})</li>"
      htmlContent += "</ul>"
    elif recipeId:
      htmlContent += "<p>No recipe found.</p>"

    return renderPage(htmlContent)

  @app.route(f"{URL_PREFIX}/search")
  def recipe_search():
    q = request.args.get("q", "").strip()
    results = search_recipes(q) if q else []
    return json.dumps({"results": [{'id': r['id'], 'name': r['name']} for r in results]})
