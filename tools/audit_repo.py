import json
import re
from pathlib import Path

ROOTS = ["app"]
PATTERNS = {
    "pydantic_v1_fields": re.compile(r"\b(schema_extra|orm_mode)\b"),
    "pydantic_v1_import": re.compile(r"from\s+pydantic\s+import\s+BaseModel"),
    "deprecated_fastapi": re.compile(
        r"from\s+fastapi\.encoders\s+import\s+jsonable_encoder"
    ),
    "lxml_imports": re.compile(r"\bfrom\s+lxml\s+import\s+etree\b|\bimport\s+lxml\b"),
}
hits = []
for root in ROOTS:
    for p in Path(root).rglob("*.py"):
        text = p.read_text(encoding="utf-8", errors="ignore")
        for key, rx in PATTERNS.items():
            for m in rx.finditer(text):
                hits.append(
                    {
                        "file": str(p),
                        "issue": key,
                        "line": text.count("\n", 0, m.start()) + 1,
                    }
                )
print(json.dumps({"findings": hits}, indent=2))
