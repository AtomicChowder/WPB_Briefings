"""Merge today's covered URLs and talking-point headlines into context/history.json.

Maintains a per-user 7-day rolling window. The file structure has both:
- a per-day log (`daily`) so old entries can be aged out cleanly, and
- flat unions (`covered_urls`, `covered_topics`) for quick lookup by the routine.

Usage:
    python src/update_history.py /tmp/briefing_input.json
"""
from __future__ import annotations

import json
import sys
from datetime import date, timedelta
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
HIST_PATH = REPO / "context" / "history.json"
WINDOW_DAYS = 7
USERS = ("adam", "surali")


def _empty_user_block() -> dict:
    return {
        "last_updated":   None,
        "covered_urls":   [],
        "covered_topics": [],
        "daily":          [],
    }


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print("usage: update_history.py <briefing_input.json>", file=sys.stderr)
        return 1

    raw = json.loads(Path(argv[1]).read_text(encoding="utf-8"))
    today = raw["date_str"]
    today_dt = date.fromisoformat(today)
    cutoff = (today_dt - timedelta(days=WINDOW_DAYS)).isoformat()

    hist = json.loads(HIST_PATH.read_text(encoding="utf-8")) if HIST_PATH.exists() else {}

    new_urls = sorted({a["url"] for a in raw["articles"]})

    for uid in USERS:
        ub = hist.setdefault(uid, _empty_user_block())
        # Backfill missing keys for older history files
        for k, v in _empty_user_block().items():
            ub.setdefault(k, v)

        # Drop any prior entry for today (re-run idempotency) and prune > cutoff
        daily = [d for d in ub.get("daily", [])
                 if d.get("date", "") > cutoff and d.get("date") != today]

        topics = [tp["headline"]
                  for tp in (raw.get("users", {}).get(uid, {}) or {}).get("talking_points", [])]

        daily.append({"date": today, "urls": new_urls, "topics": topics})
        daily.sort(key=lambda d: d["date"])

        ub["daily"] = daily
        ub["covered_urls"] = sorted({u for d in daily for u in d.get("urls", [])})
        ub["covered_topics"] = sorted({t for d in daily for t in d.get("topics", [])})
        ub["last_updated"] = today

    # Drop any unknown user keys to keep history clean
    for k in list(hist):
        if k not in USERS:
            print(f"[history] dropping unknown user block: {k}")
            del hist[k]

    HIST_PATH.parent.mkdir(parents=True, exist_ok=True)
    HIST_PATH.write_text(json.dumps(hist, indent=2), encoding="utf-8")

    for uid in USERS:
        ub = hist[uid]
        print(f"[history] {uid}: {len(ub['covered_urls'])} URLs, "
              f"{len(ub['covered_topics'])} topics across {len(ub['daily'])} days "
              f"(window: {cutoff} → {today})")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
