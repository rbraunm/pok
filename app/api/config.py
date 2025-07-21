import os
import json

POK_DEBUG = os.getenv("POK_DEBUG", "false").lower() == "true"
EQEMU_CONFIG_PATH = "/app/server/eqemu_config.json"

def getEQEMUConfig():
  with open(EQEMU_CONFIG_PATH) as f:
    return json.load(f)