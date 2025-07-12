import json
import pymysql.cursors

def getConfig():
    with open("/app/server/eqemu_config.json") as f:
        return json.load(f)

def getDb():
    cfg = getConfig()["server"]["database"]
    return pymysql.connect(
        host=cfg["host"],
        port=int(cfg["port"]),
        user=cfg["username"],
        password=cfg["password"],
        database=cfg["db"],
        cursorclass=pymysql.cursors.DictCursor,
        charset="utf8mb4"
    )
