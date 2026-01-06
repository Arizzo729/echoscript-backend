import importlib
import json
import pkgutil
import sys
from pathlib import Path

out = {"fastapi_version": "unknown", "pydantic_version": "unknown", "import_errors": []}
try:
    import fastapi
    import pydantic

    out["fastapi_version"] = getattr(fastapi, "__version__", "unknown")
    out["pydantic_version"] = getattr(pydantic, "__version__", "unknown")
except Exception:
    pass
ROOT = Path("app")
if ROOT.exists():
    for mod in pkgutil.walk_packages([str(ROOT)]):
        name = f"app.{mod.name}" if not mod.ispkg else None
        try:
            if name:
                importlib.import_module(name)
        except Exception as e:
            out["import_errors"].append({"module": name, "error": repr(e)})
print(json.dumps(out, indent=2))
