NAME = "Skill Book"

from pathlib import Path
import html
from flask import request
from web.utils import renderPage, getNameFromBitmask
from api.models.characters import search_characters, get_character, CLASS_BITMASK, RACE_BITMASK
from api.models.tradeskill import TRADESKILL, get_skills_by_character, get_skill_up_recipes

URL_PREFIX = "/" + Path(__file__).stem

def render_character_summary(character):
  className = getNameFromBitmask(character['class_id'], CLASS_BITMASK).lower()
  raceName = getNameFromBitmask(character['race_id'], RACE_BITMASK)

  return f"""
    <div class="character-summary">
      <img src="/static/img/class_portraits/{className}.gif" alt="{className} portrait" class="class-portrait" />
      <div class="character-details">
        <h2>{html.escape(character['name'])}</h2>
        <p>Class: {className.title()}<br>
        Level: {character['level']}<br>
        Race: {raceName}</p>
      </div>
    </div>
  """

def get_trivial_color_class(skill: int, trivial: int) -> str:
  if trivial <= int(skill * 0.95):
    return "eq-color-grey"
  elif trivial <= skill:
    return "eq-color-green"
  elif trivial <= skill + 15:
    return "eq-color-lightblue"
  elif trivial <= skill + 35:
    return "eq-color-blue"
  elif trivial <= skill + 50:
    return "eq-color-yellow"
  else:
    return "eq-color-red"

def render_tradeskill_list(characterId, tradeskillValues):
  html_parts = ['<div class="tradeskill-list"><h3>Tradeskills</h3><ul>']

  # Sort by tradeskill name
  for skillId, value in sorted(tradeskillValues.items(), key=lambda item: TRADESKILL.get(item[0], "").lower()):
    skillName = TRADESKILL.get(skillId)
    if not skillName:
      continue
    html_parts.append(
      f"<li><a href='?charId={characterId}&skillId={skillId}'>{html.escape(skillName)}: {value}</a></li>"
    )

  html_parts.append("</ul></div>")
  return "\n".join(html_parts)

def list_section(label, items, countField="componentCount"):
  if not items:
    return ""
  return (
    f"<div class='recipe-subsection'>"
    f"<b>{label}:</b>"
    "<ul class='recipe-list'>" +
    "".join(
      f"<li>{item[countField]} x <span class='eqtooltip' data-type='item' data-id='{item['id']}'>"
      f"{html.escape(item['name'])}</span></li>"
      for item in items if item.get("name")
    ) +
    "</ul></div>"
  )

def render_skill_up_recipes(skillId, characterSkill):
  recipes = get_skill_up_recipes(skillId, characterSkill)
  if not recipes:
    return "<p>No available skill-up recipes at your current skill level.</p>"

  html_parts = [f"<h3>Skill-Up Recipes for {TRADESKILL.get(skillId, 'Unknown')}</h3>"]

  grouped = {}
  for recipe in recipes:
    grouped.setdefault(recipe["name"], []).append(recipe)

  for recipeName, variants in grouped.items():
    html_parts.append(
      f"<div class='recipe-block'><h4 class='recipe-title'>{html.escape(recipeName)}</h4><div class='recipe-section'>"
    )

    for variant in variants:
      failItems = [i for i in variant.get("ingredients", []) if i.get("failCount")]
      successItems = [i for i in variant.get("ingredients", []) if i.get("successCount") and i.get("componentCount")]
      makes = [i for i in variant.get("outputs", []) if i.get("successCount") and not i.get("componentCount")]
      variantColor = get_trivial_color_class(characterSkill, variant["trivial"])

      html_parts.append("<div class='recipe-variant'>")
      html_parts.append(
        f"<div class='trivial {variantColor}'>Trivial: {variant['trivial']}</div>"
      )
      html_parts.append("<div class='recipe-columns'>")
      html_parts.append("<div class='recipe-left-column'>")
      html_parts.append(list_section('Ingredients', variant.get("ingredients", [])))
      html_parts.append(list_section('Makes', makes, 'successCount'))
      html_parts.append("</div>")  # end left
      html_parts.append("<div class='recipe-right-column'>")
      html_parts.append(list_section('Returned on Failure', failItems, 'failCount'))
      html_parts.append(list_section('Returned on Success', successItems, 'successCount'))
      html_parts.append("</div>")  # end right
      html_parts.append("</div>")  # end recipe-columns
      html_parts.append("</div>")  # end recipe-variant

    html_parts.append("</div></div>")

  return "\n".join(html_parts)

def render_search_results(results):
  if not results:
    return "<p>No matching characters found.</p>"
  parts = ["<h2>Character Search Results</h2><ul>"]
  for c in results:
    className = getNameFromBitmask(c['class_id'], CLASS_BITMASK)
    parts.append(
      f"<li><a href='?charId={c['id']}'>{html.escape(c['name'])} "
      f"(Level {c['level']} {className})</a></li>"
    )
  parts.append("</ul>")
  return "\n".join(parts)

def register(app):
  @app.route(URL_PREFIX, methods=["GET"])
  def skillbook():
    char_query = request.args.get("character", "").strip()
    char_id = request.args.get("charId")
    skill_id = request.args.get("skillId", type=int)

    htmlContent = f"""
      <form method="get" action="">
        <label for="character">Search Character:</label>
        <input type="text" id="character" name="character" value="{html.escape(char_query)}" />
        <input type="submit" value="Search" />
      </form>
      <hr>
    """

    if char_query:
      search_results = search_characters(char_query)
      if len(search_results) == 1:
        char_id = search_results[0]["id"]
      else:
        htmlContent += render_search_results(search_results)

    if char_id:
      character = get_character(int(char_id))
      if character:
        if character:
          tradeskills = get_skills_by_character(character['id'])
          skillUpHtml = ""

          if skill_id in tradeskills:
            skill_value = tradeskills.get(skill_id, 0)
            skillUpHtml = render_skill_up_recipes(skill_id, skill_value)

          leftPanel = render_character_summary(character) + render_tradeskill_list(character['id'], tradeskills)

          htmlContent += f"""
            <div style="display: flex; gap: 40px; align-items: flex-start;">
              <div style="min-width: 220px;">{leftPanel}</div>
              <div style="flex-grow: 1;">{skillUpHtml}</div>
            </div>
          """
      else:
        htmlContent += "<p>Character not found.</p>"

    return renderPage(htmlContent)