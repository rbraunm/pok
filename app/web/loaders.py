import os
import importlib
import traceback
from flask import Flask
from web.utils import registerNavLink

def loadBlueprints(app: Flask):
  for root, _, files in os.walk("blueprints"):
    for file in files:
      if file.endswith(".py") and file != "__init__.py":
        path = os.path.join(root, file)
        relPath = os.path.relpath(path, ".").replace(os.sep, ".")[:-3]
        try:
          module = importlib.import_module(relPath)
          if hasattr(module, "register"):
            module.register(app)

          name = getattr(module, "NAME", None)
          url = getattr(module, "URL_PREFIX", None)
          if name and url:
            registerNavLink(name, url)

          print(f"Loaded blueprint: {relPath}")
        except Exception as e:
          print(f"Failed to load blueprint {relPath}: {e}")
          traceback.print_exc()

def loadModels():
  for root, _, files in os.walk("api/models"):
    for file in files:
      if file.endswith(".py") and file != "__init__.py":
        path = os.path.join(root, file)
        relPath = os.path.relpath(path, "api").replace(os.sep, ".")[:-3]
        try:
          importlib.import_module(f"api.{relPath}")
          print(f"Loaded model: api.{relPath}")
        except Exception as e:
          print(f"Failed to load model {relPath}: {e}")
          traceback.print_exc()