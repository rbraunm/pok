# /opt/eqemu/pok/app/app.py
import os, importlib.util
from flask import Flask, render_template, jsonify
from db import getDb

app = Flask(
    __name__,
    static_folder="static",
    template_folder="templates"
)

# Discover & register plugins
plugin_endpoints = []
for fname in os.listdir(os.path.dirname(__file__)):
    if not fname.endswith(".py") or fname in ("app.py", "db.py"):
        continue
    mod_name = fname[:-3]
    path = os.path.join(os.path.dirname(__file__), fname)
    spec = importlib.util.spec_from_file_location(mod_name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    if hasattr(module, "register"):
        module.register(app)
        plugin_endpoints.append({
            "name": getattr(module, "NAME", mod_name.title()),
            "url": getattr(module, "URL_PREFIX", f"/{mod_name}")
        })

@app.route("/")
def index():
    return render_template("index.html", plugins=plugin_endpoints)

@app.route("/api/status")
def apiStatus():
    db = getDb()
    with db.cursor() as cursor:
        cursor.execute("SELECT 1 AS status")
        result = cursor.fetchone()
    return jsonify(status=result["status"])

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)

