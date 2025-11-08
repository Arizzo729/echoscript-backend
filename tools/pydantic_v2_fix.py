import pathlib
import re
import sys

ROOT = pathlib.Path("app/schemas")
if not ROOT.exists():
    sys.exit(0)

for p in ROOT.rglob("*.py"):
    txt = p.read_text(encoding="utf-8")

    # (a) Field(example="x") -> Field(examples=["x"])
    # handles strings and simple literals; leaves complex cases for manual review
    def repl_example(m):
        inner = m.group(1).strip()
        # if already list/tuple/dict, skip
        if inner.startswith(("[", "(", "{")):
            return f"Field(examples={inner})"
        # wrap string/numeric in a list
        return f"Field(examples=[{inner}])"

    txt = re.sub(r"Field\s*\(\s*example\s*=\s*([^)]+?)\)", repl_example, txt)

    # (b) class Config: orm_mode=True -> model_config={"from_attributes": True}
    txt = re.sub(
        r"class\s+Config\s*:\s*(?:\n\s+.+)*?orm_mode\s*=\s*True[^\n]*",
        'model_config = {"from_attributes": True}',
        txt,
        flags=re.DOTALL,
    )

    # (c) allow_population_by_field_name=True -> populate_by_name=True (in model_config)
    # If a Config block with allow_population_by_field_name exists, replace the whole block.
    txt = re.sub(
        r"class\s+Config\s*:\s*(?:\n\s+.+)*?allow_population_by_field_name\s*=\s*True[^\n]*",
        'model_config = {"populate_by_name": True}',
        txt,
        flags=re.DOTALL,
    )

    # (d) Both options in same old Config -> combine
    txt = txt.replace(
        'model_config = {"from_attributes": True}\nmodel_config = {"populate_by_name": True}',
        'model_config = {"from_attributes": True, "populate_by_name": True}',
    )

    p.write_text(txt, encoding="utf-8")
