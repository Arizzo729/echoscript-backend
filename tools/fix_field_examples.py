import pathlib
import re

root = pathlib.Path("app/schemas")
for p in root.rglob("*.py"):
    s = p.read_text(encoding="utf-8")

    def repl(m):
        inner = m.group(1).strip()
        if inner.startswith(("[", "(", "{")):  # already a collection
            return f"Field(examples={inner})"
        return f"Field(examples=[{inner}])"

    s2 = re.sub(r"Field\s*\(\s*example\s*=\s*([^)]+?)\)", repl, s)
    if s2 != s:
        p.write_text(s2, encoding="utf-8")
