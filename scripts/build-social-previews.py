#!/usr/bin/env python3
"""Generate GitHub social preview cards for the pinned repos.

GitHub renders these at 1280x640 on every link share - LinkedIn, X, Slack,
Hacker News. Without one, a shared repo shows a grey box.

Uploading is a manual step in repo Settings; there is no API for it. Because
these images are therefore hand-uploaded and not regenerated nightly, they
deliberately carry **no exact counts** - only floors like "70+", which stay
true as the shelf grows. A precise number here would rot exactly the way the
old hardcoded "20 courses" did.

    python3 scripts/build-social-previews.py

Writes PNGs to assets/social/.
"""

from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "assets" / "social"
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

PLUM, PURPLE, PEACH, MUTED = "#2a1b3d", "#9333ea", "#fdba74", "#6b6480"

# headline is split so exactly one phrase carries the purple + peach treatment,
# mirroring the personal site's hero construction.
CARDS = [
    {
        "repo": "learn-with-phoebe",
        "head": "70+ free courses on",
        "accent": "data and AI.",
        "sub": "Two tracks: one to decide, one to build.\nEvery one runs in your browser. No install, no login.",
    },
    {
        "repo": "phoebe-the-builder",
        "head": "I see problems as",
        "accent": "opportunities.",
        "sub": "The build log. I design data and AI strategy end to end,\nthen open the editor and ship it.",
    },
    {
        "repo": "agent-skills-phoebe-picks",
        "head": "Which agent Skills",
        "accent": "survive a real build.",
        "sub": "Each one field-tested by shipping a product with it,\nrated on a public rubric. Every demo open.",
    },
    {
        "repo": "phoebe-data-skills",
        "head": "Data skills you can",
        "accent": "install, not just read.",
        "sub": "Real runs on real rows, with flaws planted on purpose\nand a review pass that rewrites the code.",
    },
    {
        "repo": "sketch-ideas-with-phoebe",
        "head": "Data and AI,",
        "accent": "explained in pictures.",
        "sub": "Decoded concepts, teaching comics, style lab.\nEvery prompt published.",
    },
]

TEMPLATE = """<!doctype html><html><head><meta charset="utf-8"><style>
  * {{ margin:0; padding:0; box-sizing:border-box; }}
  html,body {{ width:1280px; height:640px; }}
  body {{
    background:#fff; padding:86px 96px; position:relative; overflow:hidden;
    font-family: system-ui, -apple-system, "Segoe UI", Helvetica, Arial, sans-serif;
    display:flex; flex-direction:column; justify-content:space-between;
  }}
  .mark {{ display:flex; align-items:center; gap:14px; }}
  .pf {{ width:44px; height:44px; border-radius:11px; background:{purple};
        color:#fff; font-size:19px; font-weight:800;
        display:flex; align-items:center; justify-content:center; }}
  .repo {{ font-size:23px; font-weight:700; color:{plum}; letter-spacing:-.3px; }}
  h1 {{ font-size:74px; line-height:1.05; font-weight:800; color:{plum};
       letter-spacing:-2.4px; max-width:1020px; }}
  .accent {{ color:{purple}; position:relative; display:inline-block; }}
  .accent::after {{ content:""; position:absolute; left:-4px; right:-8px; bottom:11px;
                   height:18px; background:{peach}; z-index:-1; }}
  .sub {{ font-size:26px; line-height:1.5; color:{muted}; font-weight:500;
         white-space:pre-line; max-width:900px; margin-top:38px; }}
  .block {{ padding-bottom:8px; }}
  .bars {{ position:absolute; right:96px; top:150px; display:flex;
          align-items:flex-end; gap:15px; height:190px; }}
  .bars i {{ width:13px; border-radius:2px; display:block; }}
</style></head><body>
  <div class="mark"><div class="pf">PF</div><div class="repo">{repo}</div></div>
  <div class="bars">
    <i style="height:78px;background:{purple}"></i>
    <i style="height:142px;background:{peach}"></i>
    <i style="height:106px;background:{peach}"></i>
    <i style="height:58px;background:{purple}"></i>
  </div>
  <div class="block">
    <h1>{head} <span class="accent">{accent}</span></h1>
    <div class="sub">{sub}</div>
  </div>
</body></html>"""


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        for card in CARDS:
            html = TEMPLATE.format(
                purple=PURPLE, plum=PLUM, peach=PEACH, muted=MUTED, **card
            )
            src = Path(tmp) / f"{card['repo']}.html"
            src.write_text(html)
            dest = OUT / f"{card['repo']}.png"
            subprocess.run(
                [
                    CHROME, "--headless", "--disable-gpu", "--hide-scrollbars",
                    f"--screenshot={dest}", "--window-size=1280,640",
                    "--default-background-color=FFFFFFFF",
                    "--virtual-time-budget=1500", str(src),
                ],
                capture_output=True,
            )
            kb = dest.stat().st_size // 1024 if dest.exists() else 0
            print(f"  {dest.name:34} {kb} KB")
    print(f"\n{len(CARDS)} cards written to {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
