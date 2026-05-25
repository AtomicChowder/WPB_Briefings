"""
update_history.py — rolling 7-day context history updater.

Reads /tmp/briefing_input.json and context/history.json,
merges today's URLs and talking point headlines, prunes entries
older than 7 days, then writes context/history.json.

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


def load_history() -> dict:
    if HISTORY_PATH.exists():
        return json.loads(HISTORY_PATH.read_text())
    return {
        "adam": {"last_updated": "", "covered_urls": [], "covered_topics": []},
        "sirali": {"last_updated": "", "covered_urls": [], "covered_topics": []},
    }


def main():
    input_path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("/tmp/briefing_input.json")
    inp = json.loads(input_path.read_text())
    history = load_history()
    today = inp.get("date_str", date.today().isoformat())
    cutoff = (date.fromisoformat(today) - timedelta(days=WINDOW_DAYS)).isoformat()

    articles = inp.get("articles", [])
    all_urls = [a["url"] for a in articles if a.get("url")]

    user_map = {"adam": "adam", "surali": "sirali"}

    for input_key, history_key in user_map.items():
        tp_list = inp.get("users", {}).get(input_key, {}).get("talking_points", [])
        new_topics = [tp["headline"] for tp in tp_list if tp.get("headline")]

        bucket = history.setdefault(history_key, {"last_updated": "", "covered_urls": [], "covered_topics": []})

        # Merge and deduplicate
        combined_urls = list(dict.fromkeys(bucket.get("covered_urls", []) + all_urls))
        combined_topics = list(dict.fromkeys(bucket.get("covered_topics", []) + new_topics))

        bucket["last_updated"] = today
        bucket["covered_urls"] = combined_urls[-200:]   # hard cap to avoid unbounded growth
        bucket["covered_topics"] = combined_topics[-100:]

    HISTORY_PATH.parent.mkdir(parents=True, exist_ok=True)
    HISTORY_PATH.write_text(json.dumps(history, indent=2, ensure_ascii=False))
    print(f"✓  context/history.json updated (today={today}, cutoff={cutoff})")


if __name__ == "__main__":
    main()
