NAME = "PEQ Schema Export"
URL_PREFIX = "/schema"

from flask import Response, render_template_string, request
from db import getDb

TEMPLATE = """
<!doctype html>
<html>
  <head>
    <meta charset="utf-8">
    <title>PEQ Schema Export</title>
    <style>
      body { font-family: monospace; background: #2c3e50; color: #ecf0f1; margin: 2rem; }
      h1 { margin-bottom: 1rem; }
      .container { position: relative; }
      pre {
        background: #1e272e;
        color: #dff9fb;
        padding: 1rem;
        border-radius: 0.5rem;
        overflow-x: auto;
        white-space: pre-wrap;
        word-wrap: break-word;
        max-height: 80vh;
      }
      a.download-btn {
        position: absolute;
        top: 0;
        right: 0;
        margin: 1rem;
        background: #1abc9c;
        color: white;
        padding: 0.5rem 1rem;
        border-radius: 0.25rem;
        text-decoration: none;
        font-weight: bold;
      }
      a.download-btn:hover {
        background: #16a085;
      }
    </style>
  </head>
  <body>
    <h1>PEQ Schema Export</h1>
    <div class="container">
      <a class="download-btn" href="{{ url_for('exportSchema') }}?download=1">Download .sql</a>
      <pre>{{ data }}</pre>
    </div>
  </body>
</html>
"""

def register(app):
  @app.route(URL_PREFIX, methods=["GET"])
  def exportSchema():
    db = getDb()
    ddls = []
    with db.cursor() as cur:
      cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = DATABASE();")
      tables = [r["table_name"] for r in cur.fetchall()]
      for tbl in tables:
        cur.execute(f"SHOW CREATE TABLE `{tbl}`;")
        row = cur.fetchone()
        ddl = row.get("Create Table") or row.get("Create View") or ""
        ddls.append(ddl + ";")
    txt = "\n\n".join(ddls)

    if request.args.get("download") == "1":
      return Response(
        txt,
        mimetype="text/sql",
        headers={"Content-Disposition": "attachment; filename=PEQSchemaExport.sql"}
      )

    return render_template_string(TEMPLATE, data=txt)
