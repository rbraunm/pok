NAME = "PEQ Schema Export"
URL_PREFIX = "/peqschemaexport"

from flask import Response, request, url_for
from db import getDb
from app import renderPage

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

    header = f'''
      <div class="headerRow">
        <h1>PEQ Schema Export</h1>
        <a class="download-btn" href="{url_for("exportSchema")}?download=1">Download .sql</a>
      </div>
    '''
    body = f'<pre>{txt}</pre>'

    return renderPage(header, body)
