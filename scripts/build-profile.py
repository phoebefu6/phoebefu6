#!/usr/bin/env python3
"""Rebuild the generated section of the profile README.

Every number on the profile is derived from the hub's stats.json, never typed.
Running this daily is what keeps the front page of the account honest while
Phoebe ships.

The section is delimited by marker comments so the hand-written copy around it
is never touched.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parent.parent
README = ROOT / "README.md"
OWNER = "phoebefu6"
STATS_URL = f"https://{OWNER}.github.io/learn-with-phoebe/stats.json"


def fetch_stats() -> dict:
    with urlopen(STATS_URL, timeout=30) as r:
        return json.loads(r.read())


def render_stats(s: dict) -> str:
    return (
        f"**{s['courses_live']} free courses** live right now, "
        f"**{s['sessions_live']} sessions** across **{s['buckets_live']} domains**, "
        f"on **{s['repos_live']} live sites**. Everything below is free and runs in a browser."
    )


def replace(text: str, name: str, body: str) -> str:
    start, end = f"<!-- {name}:START -->", f"<!-- {name}:END -->"
    pattern = re.compile(re.escape(start) + r".*?" + re.escape(end), re.DOTALL)
    if not pattern.search(text):
        raise SystemExit(f"marker {name} not found in README.md")
    return pattern.sub(f"{start}\n{body}\n{end}", text)


def main() -> int:
    original = README.read_text()
    updated = replace(original, "STATS", render_stats(fetch_stats()))

    if "--check" in sys.argv:
        if original != updated:
            print("profile README is stale", file=sys.stderr)
            return 1
        print("profile README current")
        return 0

    README.write_text(updated)
    print("profile README rebuilt")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
