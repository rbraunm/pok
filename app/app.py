APP_VERSION = "0.6.4071"

import html
import json
from flask import Flask, request
from web.utils import PoKJSONEncoder, renderPage
from web.loaders import loadBlueprints, loadModels
from applogging import get_logger
from werkzeug.exceptions import HTTPException
from flask import request

logger = get_logger(__name__)
app = Flask(__name__, static_folder='static', template_folder='templates')
app.json_encoder = PoKJSONEncoder

logger.info('Loading models...')
loadModels()
logger.info('Loading blueprints...')
loadBlueprints(app)

@app.errorhandler(Exception)
def handleError(e):
    if isinstance(e, HTTPException):
        if e.code >= 500:
            logger.exception(f'HTTP {e.code} on {request.method} {request.path}')
        else:
            logger.warning(f"HTTP {e.code} on {request.method} {request.path}: {getattr(e, 'description', '')}")
        return e
    logger.exception(f'Unhandled exception on {request.method} {request.path}')
    return (renderPage('Error' + '<pre>Internal Server Error</pre>'), 500)

@app.route('/')
def index():
    content = f"""\n  <div class="pok-container">\n    <div class="pok-hero">\n      <h1 class="pok-title"><span class="eq-gold">Pane of Knowledge</span></h1>\n      <span class="pok-badge">v{html.escape(APP_VERSION)}</span>\n      <span id="healthBadge" class="pok-badge-dot pok-muted" role="status" aria-live="polite">\n        <span class="pok-dot"></span><span>checking…</span>\n      </span>\n    </div>\n\n    <p class="pok-sub">Welcome! Explore items, dig into drop data, and keep an eye on system status. Use the quick tools below to jump in.</p>\n\n    <div class="pok-grid">\n      <section class="pok-card pok-card--muted pok-border">\n        <div class="pok-section-title">\n          <h2>API explorer · Item drops</h2>\n        </div>\n        <p class="pok-muted">Jump straight to an item's drop table from its ID.</p>\n\n        <form id="itemForm" class="pok-row" action="/api/item" method="GET" onsubmit="return false">\n          <label for="itemId" class="pok-muted" style="position:absolute;left:-9999px;">Item ID</label>\n          <input id="itemId" class="pok-input" type="number" inputmode="numeric" placeholder="e.g. 11745" />\n          <button id="goBtn" class="pok-btn" type="button" title="Go">Go</button>\n        </form>\n\n        <ul class="pok-list--clean pok-muted">\n          <li>Example: <a href="/api/item/11745/drops"><code>/api/item/11745/drops</code></a></li>\n        </ul>\n      </section>\n\n      <section class="pok-card pok-card--muted pok-border">\n        <div class="pok-section-title">\n          <h2>Quick links</h2>\n        </div>\n        <ul class="pok-list">\n          <li><a href="/version">Version (JSON)</a></li>\n          <li><a href="/health">Health (JSON)</a></li>\n          <li><a href="/api">API root</a></li>\n        </ul>\n        <p class="pok-muted">Links avoid exposing internals; details live in logs.</p>\n      </section>\n\n      <section class="pok-card pok-card--muted pok-border">\n        <div class="pok-section-title">\n          <h2>About</h2>\n        </div>\n        <p class="pok-muted">Pane of Knowledge is a lightweight EverQuest data explorer and API front end. Designed for speed, clarity, and zero leakage of sensitive internals.</p>\n      </section>\n    </div>\n  </div>\n\n  <script>\n    (function(){{  // doubled braces for f-string\n      const form = document.getElementById('itemForm');\n      const input = document.getElementById('itemId');\n      const goBtn = document.getElementById('goBtn');\n\n      const go = () => {{\n        const id = (input.value || '').trim();\n        if (!id) return input.focus();\n        window.location.href = '/api/item/' + encodeURIComponent(id) + '/drops';\n      }};\n\n      goBtn.addEventListener('click', go);\n      input.addEventListener('keydown', (e) => {{ if (e.key === 'Enter') go(); }});\n      form.addEventListener('submit', go);\n\n      // Health badge\n      const badge = document.getElementById('healthBadge');\n      fetch('/health', {{ cache: 'no-store' }})\n        .then(r => r.ok ? r.json() : Promise.reject())\n        .then(d => {{\n          badge.classList.remove('pok-muted');\n          badge.classList.add((d && d.status) === 'ok' ? 'pok-ok' : 'pok-bad');\n          badge.querySelector('span:nth-child(2)').textContent =\n            (d && d.status) === 'ok' ? 'healthy' : 'degraded';\n        }})\n        .catch(() => {{\n          badge.classList.remove('pok-muted');\n          badge.classList.add('pok-bad');\n          badge.querySelector('span:nth-child(2)').textContent = 'unreachable';\n        }});\n    }}());\n  </script>\n  """
    return renderPage(content)

@app.route('/version')
def version():
    return app.response_class(response=json.dumps({'appVersion': APP_VERSION}), mimetype='application/json')

@app.route('/health')
def health():
    return app.response_class(response=json.dumps({'status': 'ok'}), mimetype='application/json')
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8202)
