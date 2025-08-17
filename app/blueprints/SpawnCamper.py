NAME = "Spawn Camper"

from pathlib import Path
from web.utils import renderPage
from applogging import get_logger
logger = get_logger(__name__)

URL_PREFIX = "/" + Path(__file__).stem

def register(app):
  @app.route(URL_PREFIX, methods=["GET"])
  def spawn_camper():
    body = """
<div class="sc-root">
  <div class="sc-wrap">
    <div class="sc-input">
      <div style="align-self:beginning;">
        <button class="sc-icon" id="sc-add" type="button" title="Add spawn" aria-label="Add spawn">➕</button>
      </div>
      <div id="sc-name-container">
        <label for="sc-name" id="sc-name-label">Spawn name</label>
        <input class="sc-narrow" id="sc-name" type="text" placeholder="e.g., Quillmane, Arch Magus, etc">
      </div>
      <div id="sc-duration-container">
        <label for="sc-duration" id="sc-duration-label">Respawn time</label>
        <input class="sc-narrow-sm" id="sc-duration" type="text" placeholder="e.g., 22m, 1h30m, 200s, 00:22:00">
      </div>
      <div class="sc-row sc-muted">
        <label><input id="sc-sound" type="checkbox" checked> Beep</label>
        <label><input id="sc-notify" type="checkbox" checked> Browser notify</label>
      </div>
      <div class="sc-muted">Alerts at T-1:00 and T=0.</div>
    </div>

    <hr class="sc-hr">

    <div class="sc-card-grid" id="sc-cards"></div>
  </div>
</div>

<script type="module" src="/static/js/spawncamper.js"></script>
"""
    return renderPage(header=NAME, body=body)
