# /opt/eqemu/pok/app/PEQSchemaExport.py
NAME = "PEQ Schema Export"
URL_PREFIX = "/schema"

from flask import Response
from db import getDb

def register(app):
    @app.route(URL_PREFIX)
    def exportSchema():
        db = getDb()
        ddls = []
        with db.cursor() as cur:
            # get all tables in the current database
            cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = DATABASE();")
            tables = [r["table_name"] for r in cur.fetchall()]
            # for each table, fetch its CREATE statement
            for tbl in tables:
                cur.execute(f"SHOW CREATE TABLE `{tbl}`;")
                row = cur.fetchone()
                # The column name is driver-dependent; PyMySQL uses 'Create Table'
                ddl = row.get("Create Table") or row.get("Create View") or ""
                ddls.append(ddl + ";")
        # join with blank lines and return as plaintext
        txt = "\n\n".join(ddls)
        return Response(txt, mimetype="text/plain")


