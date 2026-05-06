"""
Update context/history.json with today's URLs and headlines.
Applies a rolling 7-day window per user.

Usage:
    python src/update_history.py /tmp/briefing_input.json
"""

import json
import sys
from datetime import date, timedelta
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
HISTORY_PATH = REPO_ROOT / "context" / "history.json"
WINDOW_DAYS = 7

USER_REL_FIELDS = {
    "adam": "adam_rel",
    "sirali": "surali_rel",
}


def main():
    if len(sys.argv) < 2:
        print("Usage: python src/update_history.py <briefing_input.json>", file=sys.stderr)
        sys.exit(1)

    inp = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    history = json.loads(HISTORY_PATH.read_text(encoding="utf-8")) if HISTORY_PATH.exists() else {}
    today = date.today().isoformat()
    cutoff = (date.today() - timedelta(days=WINDOW_DAYS)).isoformat()

    articles = inp.get("articles", [])

    for user_key in ("adam", "sirali"):
        rel_field = USER_REL_FIELDS[user_key]
        user_hist = history.setdefault(user_key, {
            "last_updated": "",
            "covered_urls": [],
            "covered_topics": [],
        })

        # Prune stale entries (keep only last 7 days by resetting if last_updated is old)
        last = user_hist.get("last_updated", "")
        if last and last < cutoff:
            user_hist["covered_urls"] = []
            user_hist["covered_topics"] = []

        # Add today's URLs
        new_urls = [a["url"] for a in articles if a.get("url")]
        existing_urls = set(user_hist.get("covered_urls", []))
        for url in new_urls:
            if url not in existing_urls:
                user_hist.setdefault("covered_urls", []).append(url)
                existing_urls.add(url)

        # Add today's talking point headlines
        tps = inp.get("users", {}).get(user_key, {}).get("talking_points", [])
        existing_topics = set(user_hist.get("covered_topics", []))
        for tp in tps:
            headline = tp.get("headline", "")
            if headline and headline not in existing_topics:
                user_hist.setdefault("covered_topics", []).append(headline)
                existing_topics.add(headline)

        user_hist["last_updated"] = today

    HISTORY_PATH.parent.mkdir(parents=True, exist_ok=True)
    HISTORY_PATH.write_text(json.dumps(history, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"✓  context/history.json updated ({today})")


if __name__ == "__main__":
    main()
