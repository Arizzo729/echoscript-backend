import json
import pathlib

out = ["# EchoScript Backend Audit\n"]


def add(title: str, path: str):
    out.append(f"\n## {title}\n")
    p = pathlib.Path(path)
    if not p.exists():
        out.append("_missing_\n")
        return
    txt = p.read_text(encoding="utf-8", errors="ignore").strip()
    if not txt:
        out.append("_empty file_\n")
        return
    # Try JSON; if it fails, include as plain text
    try:
        obj = json.loads(txt)
        out.append("```json\n" + json.dumps(obj, indent=2)[:20000] + "\n```\n")
    except Exception:
        out.append("```\n" + txt[:20000] + "\n```\n")


def add_all():
    add("Versions & Import Boot", ".audit/import-boot.json")
    add("Dependency Tree", ".audit/pipdeptree.txt")
    add("Security (pip-audit)", ".audit/pip-audit.txt")
    add("Dead/Unused Code (vulture)", ".audit/vulture.txt")
    add("Mypy (types)", ".audit/mypy.txt")
    add("Pytest (smoke)", ".audit/pytest.txt")
    add("Pydantic/FastAPI patterns", ".audit/patterns.json")


if __name__ == "__main__":
    add_all()
    pathlib.Path(".audit/report.md").write_text("\n".join(out), encoding="utf-8")
    print("Wrote .audit/report.md")
