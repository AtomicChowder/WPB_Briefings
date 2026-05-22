#!/usr/bin/env python3
"""
Reads /tmp/briefing_input.json and writes docs/{user}/briefing_data.json for each user.
Applies: combined-score filter (>= 6), category cap (5 per category), descending sort.
"""

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
DOCS_DIR = REPO_ROOT / "docs"

CATEGORY_COLORS = {
    "AI & Technology": "#6366f1",
    "HSBC News": "#dc2626",
    "Competitor Intelligence": "#0891b2",
    "Private Banking & Wealth": "#059669",
    "Regulatory & Markets": "#d97706",
    "Operations & Change": "#7c3aed",
}

CATEGORY_ORDER = list(CATEGORY_COLORS.keys())

USER_CONFIG = {
    "adam": {
        "user_name": "Adam Chow",
        "user_display_name": "Adam",
        "user_title": "Head of Change Execution, WPB Private Banking & Wealth Solutions, Asia Pacific",
        "rel_field": "adam_rel",
    },
    "surali": {
        "user_name": "Sirali Siriwardene",
        "user_display_name": "Sirali",
        "user_title": "COO & Global Head of Change Execution, WPS",
        "rel_field": "surali_rel",
    },
}

CATEGORY_CAP = 5
MIN_COMBINED_SCORE = 6


def build_for_user(user_id: str, data: dict) -> dict:
    cfg = USER_CONFIG[user_id]
    rel_field = cfg["rel_field"]

    scored = []
    for art in data["articles"]:
        user_rel = art.get(rel_field, 0)
        hsbc_rel = art.get("hsbc_relevancy", 0)
        if hsbc_rel + user_rel >= MIN_COMBINED_SCORE:
            scored.append({**art, "user_relevance": user_rel, "_combined": hsbc_rel + user_rel})

    by_cat: dict[str, list] = {}
    for art in scored:
        by_cat.setdefault(art["category"], []).append(art)

    for cat in by_cat:
        by_cat[cat].sort(key=lambda a: a["_combined"], reverse=True)
        by_cat[cat] = by_cat[cat][:CATEGORY_CAP]

    counter = 1
    articles_by_category: dict[str, list] = {}
    all_flat: list[dict] = []

    for cat in CATEGORY_ORDER:
        if cat not in by_cat:
            continue
        articles_by_category[cat] = []
        for art in by_cat[cat]:
            art_id = f"art{counter:02d}"
            counter += 1
            entry = {
                "id": art_id,
                "title": art["title"],
                "url": art["url"],
                "source": art["source"],
                "published_at": art.get("published_at", ""),
                "summary": art["summary"],
                "hsbc_relevancy": art["hsbc_relevancy"],
                "user_relevance": art["user_relevance"],
                "noise_level": art.get("noise_level", 3),
                "category": cat,
            }
            articles_by_category[cat].append(entry)
            all_flat.append({
                "id": art_id,
                "title": art["title"][:90],
                "url": art["url"],
                "source": art["source"],
                "hsbc_relevancy": art["hsbc_relevancy"],
                "user_relevance": art["user_relevance"],
                "noise_level": art.get("noise_level", 3),
                "category": cat,
                "summary": art["summary"],
            })

    talking_points = [
        {
            "headline": tp["headline"],
            "context_html": tp.get("context_html", ""),
            "source_links": tp.get("source_links", []),
            "is_update": tp.get("is_update", False),
        }
        for tp in data["users"][user_id].get("talking_points", [])
    ]

    included_categories = {
        cat: CATEGORY_COLORS[cat] for cat in CATEGORY_ORDER if cat in articles_by_category
    }
    total = sum(len(v) for v in articles_by_category.values())
    generated_at = datetime.now(timezone.utc).strftime("%-d %b %Y, %H:%M UTC")

    return {
        "user_id": user_id,
        "user_name": cfg["user_name"],
        "user_display_name": cfg["user_display_name"],
        "user_title": cfg["user_title"],
        "briefing_date": data["briefing_date"],
        "date_str": data["date_str"],
        "generated_at": generated_at,
        "total_articles": total,
        "talking_points": talking_points,
        "articles_by_category": articles_by_category,
        "chart_data": {"articles": all_flat, "categories": included_categories},
    }


def main():
    input_path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("/tmp/briefing_input.json")
    data = json.loads(input_path.read_text())
    for user_id in data["users"]:
        result = build_for_user(user_id, data)
        out_dir = DOCS_DIR / user_id
        out_dir.mkdir(parents=True, exist_ok=True)
        out_path = out_dir / "briefing_data.json"
        out_path.write_text(json.dumps(result, indent=2, ensure_ascii=False))
        print(f"✓  {out_path.relative_to(REPO_ROOT)}")


if __name__ == "__main__":
    main()
