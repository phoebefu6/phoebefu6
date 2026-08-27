#!/usr/bin/env python3
"""Rebuild the generated sections of the profile README.

Nothing on the profile is typed by hand. The counts come from the hub's
stats.json, and the highlights are derived from the same file plus the course
manifest. Running this daily is what keeps the front page of the account honest
while Phoebe ships.

Two generated sections, each delimited by marker comments so the hand-written
copy around them is never touched:

  STATS       one line of live counts
  HIGHLIGHTS  a course rotated daily, plus any genuinely new arrivals

The rotation exists because the shelf is far deeper than anyone browsing will
ever scroll. Picking one course per day by date means every course in the
catalogue gets front-page time over a full cycle, and a returning visitor sees
something different each day.
"""

from __future__ import annotations

import json
import re
import sys
from datetime import date, timedelta
from pathlib import Path
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parent.parent
README = ROOT / "README.md"
OWNER = "phoebefu6"
HUB = f"https://{OWNER}.github.io/learn-with-phoebe"
STATS_URL = f"{HUB}/stats.json"
COURSES_URL = f"{HUB}/courses.json"

# How recently a course must have appeared to count as a new arrival.
NEW_WINDOW = timedelta(days=21)
MAX_NEW = 3


def fetch(url: str) -> dict:
    with urlopen(url, timeout=30) as r:
        return json.loads(r.read())


def render_stats(s: dict) -> str:
    return (
        f"**{s['courses_live']} free courses** live right now, "
        f"**{s['sessions_live']} sessions** across **{s['buckets_live']} domains**, "
        f"on **{s['repos_live']} live sites**. All free, all in the browser."
    )


def one_line(text: str, limit: int = 76) -> str:
    """First clause of a blurb, cut on a word boundary."""
    text = re.sub(r"\s+", " ", text or "").strip()
    for sep in (" - ", ": "):
        head = text.split(sep)[0]
        if 40 <= len(head) <= limit:
            return head.rstrip(" ,.")
    if len(text) <= limit:
        return text.rstrip(" ,.")
    cut = text[: limit + 1]
    if " " in cut:
        cut = cut[: cut.rindex(" ")]
    return cut.rstrip(" ,.;:") + "..."


def pick_of_the_day(live: list[str], today: date) -> str:
    """Deterministic daily rotation through the whole shelf.

    Keyed on the ordinal date so it advances once a day and cycles the entire
    catalogue before repeating. Stable for any given day, which keeps the daily
    commit to a single changed line.
    """
    return live[today.toordinal() % len(live)]


def new_arrivals(stats: dict, today: date) -> list[str]:
    """Courses first seen live inside the recent window, newest first.

    first_seen is written by the hub's build-stats.py and never rewritten, so
    this reflects when a course actually went live rather than when its repo was
    last pushed.
    """
    seen = stats.get("first_seen") or {}
    cutoff = (today - NEW_WINDOW).isoformat()
    recent = [(d, slug) for slug, d in seen.items() if d > cutoff]
    # A first run backdates the whole shelf to one day; that is a backfill, not
    # 78 launches, so suppress it rather than announce everything at once.
    if len(recent) > MAX_NEW * 3:
        return []
    return [slug for _, slug in sorted(recent, reverse=True)][:MAX_NEW]


def render_highlights(stats: dict, courses: dict[str, dict], today: date) -> str:
    live = stats["live_course_slugs"]
    lines = []

    slug = pick_of_the_day(live, today)
    course = courses.get(slug, {})
    title = course.get("title") or slug
    lines.append(f"**📘 Today from the shelf** · [{title}]({HUB.rsplit('/', 1)[0]}/{slug}/)")
    blurb = one_line(course.get("blurb", ""))
    if blurb:
        lines.append(f"{blurb}")

    fresh = new_arrivals(stats, today)
    if fresh:
        links = " · ".join(
            f"[{courses.get(s, {}).get('title') or s}](https://{OWNER}.github.io/{s}/)"
            for s in fresh
        )
        lines.append(f"\n**✨ Just landed** · {links}")

    return "\n".join(lines)


def replace(text: str, name: str, body: str) -> str:
    start, end = f"<!-- {name}:START -->", f"<!-- {name}:END -->"
    pattern = re.compile(re.escape(start) + r".*?" + re.escape(end), re.DOTALL)
    if not pattern.search(text):
        raise SystemExit(f"marker {name} not found in README.md")
    return pattern.sub(f"{start}\n{body}\n{end}", text)


def main() -> int:
    today = date.today()
    stats = fetch(STATS_URL)
    courses = {c["slug"]: c for c in fetch(COURSES_URL)["courses"]}

    original = README.read_text()
    updated = replace(original, "STATS", render_stats(stats))
    updated = replace(updated, "HIGHLIGHTS", render_highlights(stats, courses, today))

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
