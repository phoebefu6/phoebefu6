#!/usr/bin/env python3
"""Rebuild the generated sections of the profile README.

Every number and every "recently shipped" row is derived, never typed. The
counts come from the hub's stats.json; the ship log comes from the GitHub API.
Running this daily is what keeps the profile honest while Phoebe ships.

Sections are delimited by marker comments so the hand-written copy around them
is never touched.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parent.parent
README = ROOT / "README.md"
OWNER = "phoebefu6"
STATS_URL = f"https://{OWNER}.github.io/learn-with-phoebe/stats.json"

# Repos that are infrastructure rather than something to show off in a ship log.
HIDE = {OWNER, "phoebe-skill-vault"}


def token() -> str:
    t = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if t:
        return t
    try:
        return subprocess.run(
            ["gh", "auth", "token"], capture_output=True, text=True, check=True
        ).stdout.strip()
    except (FileNotFoundError, subprocess.CalledProcessError):
        return ""


def api(path: str):
    req = Request(
        f"https://api.github.com{path}", headers={"Accept": "application/vnd.github+json"}
    )
    t = token()
    if t:
        req.add_header("Authorization", f"Bearer {t}")
    with urlopen(req, timeout=30) as r:
        return json.loads(r.read())


def fetch_stats() -> dict:
    with urlopen(STATS_URL, timeout=30) as r:
        return json.loads(r.read())


def summarise(description: str | None, limit: int = 88) -> str:
    """First clause of a repo description, cut on a word boundary."""
    text = re.sub(r"\s+", " ", (description or "")).strip()
    if not text:
        return ""
    # Drop the trailing byline, it repeats on every row.
    text = re.sub(r"\s*(by Phoebe Fu\.?)$", "", text, flags=re.I).strip()
    if len(text) <= limit:
        return text
    cut = text[: limit + 1]
    if " " in cut:
        cut = cut[: cut.rindex(" ")]
    return cut.rstrip(" ,-.;:") + "..."


def recent_ships(limit: int = 6) -> list[dict]:
    repos = api(f"/users/{OWNER}/repos?per_page=100&sort=pushed&type=owner")
    out = []
    for repo in repos:
        if repo["name"] in HIDE or repo["private"] or repo["archived"]:
            continue
        out.append(
            {
                "name": repo["name"],
                "url": repo["homepage"] or repo["html_url"],
                "desc": summarise(repo["description"]),
                "pushed": repo["pushed_at"],
            }
        )
        if len(out) == limit:
            break
    return out


def render_stats(s: dict) -> str:
    return (
        f"**{s['courses_live']} free courses** live right now, "
        f"**{s['sessions_live']} sessions** across **{s['buckets_live']} domains**, "
        f"on **{s['repos_live']} live sites**. Everything below is free and runs in a browser."
    )


def render_ships(ships: list[dict]) -> str:
    lines = ["| Shipped | What it is |", "| --- | --- |"]
    for s in ships:
        when = datetime.strptime(s["pushed"], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
        days = (datetime.now(timezone.utc) - when).days
        ago = "today" if days == 0 else "yesterday" if days == 1 else f"{days}d ago"
        lines.append(f"| [{s['name']}]({s['url']}) · {ago} | {s['desc']} |")
    return "\n".join(lines)


def replace(text: str, name: str, body: str) -> str:
    start, end = f"<!-- {name}:START -->", f"<!-- {name}:END -->"
    pattern = re.compile(re.escape(start) + r".*?" + re.escape(end), re.DOTALL)
    if not pattern.search(text):
        raise SystemExit(f"marker {name} not found in README.md")
    return pattern.sub(f"{start}\n{body}\n{end}", text)


def main() -> int:
    text = README.read_text()
    text = replace(text, "STATS", render_stats(fetch_stats()))
    text = replace(text, "SHIPS", render_ships(recent_ships()))
    if "--check" in sys.argv:
        current = README.read_text()
        if current != text:
            print("profile README is stale", file=sys.stderr)
            return 1
        print("profile README current")
        return 0
    README.write_text(text)
    print("profile README rebuilt")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
