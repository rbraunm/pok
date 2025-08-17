import json
from applogging import get_logger
logger = get_logger(__name__)

EQEMU_CONFIG_PATH = "/app/server/eqemu_config.json"

def getEQEMUConfig():
  with open(EQEMU_CONFIG_PATH) as f:
    return json.load(f)