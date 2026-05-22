#!/usr/bin/env python3
"""
Updates context/history.json with today's covered URLs and talking point headlines.
Maintains a 7-day rolling window per user (caps at 200 URLs and 50 topics).
"""

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
HISTORY_PATH = REPO_ROOT / "context" / "history.json"


def load_history() -> dict:
    if HISTORY_PATH.exists():
        return json.loads(HISTORY_PATH.read_text())
    return {
        "adam": {"last_updated": "", "covered_urls": [], "covered_topics": []},
        "surali": {"last_updated": "", "covered_urls": [], "covered_topics": []},
    }


def main():
    input_path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("/tmp/briefing_input.json")
    data = json.loads(input_path.read_text())
    date_str = data["date_str"]
    all_urls = [a["url"] for a in data.get("articles", [])]

    history = load_history()
    for user_id, user_data in data["users"].items():
        if user_id not in history:
            history[user_id] = {"last_updated": "", "covered_urls": [], "covered_topics": []}
        new_topics = [tp["headline"] for tp in user_data.get("talking_points", [])]
        existing_urls = history[user_id].get("covered_urls", [])
        existing_topics = history[user_id].get("covered_topics", [])
        history[user_id]["last_updated"] = date_str
        history[user_id]["covered_urls"] = list(dict.fromkeys(existing_urls + all_urls))[-200:]
        history[user_id]["covered_topics"] = list(dict.fromkeys(existing_topics + new_topics))[-50:]

    HISTORY_PATH.parent.mkdir(parents=True, exist_ok=True)
    HISTORY_PATH.write_text(json.dumps(history, indent=2, ensure_ascii=False))
    print(f"✓  context/history.json updated ({date_str})")


if __name__ == "__main__":
    main()
