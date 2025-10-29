import importlib
import json
import pkgutil
from pathlib import Path

try:
    import fastapi
    import pydantic

    fv = getattr(fastapi, "__version__", "unknown")
    pv = getattr(pydantic, "__version__", "unknown")
except Exception:
    fv = pv = "unknown"

ROOT = Path("app")
errors = []
for mod in pkgutil.walk_packages([str(ROOT)]):
    name = f"app.{mod.name}" if not mod.ispkg else None
    try:
        if name:
            importlib.import_module(name)
    except Exception as e:
        errors.append({"module": name, "error": repr(e)})

print(
    json.dumps(
        {"fastapi_version": fv, "pydantic_version": pv, "import_errors": errors[:200]},
        indent=2,
    )
)
