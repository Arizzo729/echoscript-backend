#!/usr/bin/env python
"""
Detect common repo-shape issues:
- Nested duplicate dumps like echoscript_backend_*/echoscript_backend_*
- Web build artifacts left inside backend (web_dist, echoscript-web/build)
- MP3 data blobs in /data

This script only **reports** by default. Pass --fix to remove safely.
"""
from __future__ import annotations

import argparse
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def find_nested_duplicates(root: Path):
    hits = []
    for p in root.rglob("*"):
        if p.is_dir() and "echoscript_backend_" in p.name:
            inner = list(p.glob("**/echoscript_backend_*"))
            if inner:
                hits.append((p, inner))
    return hits


def find_web_builds(root: Path):
    patterns = ["web_dist", "echoscript-web/build", "echoscript-web/.react-router"]
    hits = []
    for pat in patterns:
        for p in root.glob(f"**/{pat}"):
            if p.exists():
                hits.append(p)
    return hits


def find_data_blobs(root: Path):
    hits = []
    for p in root.glob("**/data/*.mp3"):
        hits.append(p)
    return hits


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--fix", action="store_true", help="remove found items")
    args = ap.parse_args()

    nested = find_nested_duplicates(ROOT)
    builds = find_web_builds(ROOT)
    blobs = find_data_blobs(ROOT)

    print("== Nested duplicate dumps ==")
    for outer, inners in nested:
        print(" -", outer)
        for i in inners:
            print("    ->", i)

    print("\n== Web build artifacts ==")
    for p in builds:
        print(" -", p)

    print("\n== Data blobs ==")
    for p in blobs:
        print(" -", p)

    if args.fix:
        for _, inners in nested:
            for i in inners:
                shutil.rmtree(i, ignore_errors=True)
        for p in builds:
            shutil.rmtree(p, ignore_errors=True)
        for p in blobs:
            try:
                p.unlink()
            except Exception:
                pass
        print("\nFixed.")


if __name__ == "__main__":
    main()
