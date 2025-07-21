import traceback
import html
import json
from flask import Flask
from web.utils import PoKJSONEncoder, renderPage
from web.loaders import loadBlueprints, loadModels
from api.config import POK_DEBUG

APP_VERSION = "0.6.87"

app = Flask(
  __name__,
  static_folder="static",
  template_folder="templates"
)

app.json_encoder = PoKJSONEncoder

print("Loading models...")
loadModels()

print("Loading blueprints...")
loadBlueprints(app)

@app.errorhandler(Exception)
def handleError(e):
  if POK_DEBUG:
    traceback.print_exc()
  return renderPage("Error" + f"<pre>{html.escape(str(e))}</pre>"), 500


@app.route("/")
def index():
  return renderPage("Welcome" + f"<p>PoK API Version: {APP_VERSION}</p>")

@app.route("/version")
def version():
  return app.response_class(
    response=json.dumps({"appVersion": APP_VERSION}),
    mimetype="application/json"
  )

@app.route("/health")
def health():
  return app.response_class(
    response=json.dumps({"status": "ok"}),
    mimetype="application/json"
  )

if __name__ == "__main__":
  app.run(host="0.0.0.0", port=8202, debug=POK_DEBUG)
