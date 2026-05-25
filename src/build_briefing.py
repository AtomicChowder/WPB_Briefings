"""
build_briefing.py — deterministic post-processor for the WPB briefing.

Reads /tmp/briefing_input.json (written by Claude during the routine),
applies score filters, category caps, and sorting, then writes:
  docs/adam/briefing_data.json
  docs/sirali/briefing_data.json

Usage:
    python src/build_briefing.py /tmp/briefing_input.json
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

USER_META = {
    "adam": {
        "user_name": "Adam Chow",
        "user_display_name": "Adam",
        "user_title": "Head of Change Execution, WPB Private Banking & Wealth Solutions, Asia Pacific",
        "rel_field": "adam_rel",
    },
    "sirali": {
        "user_name": "Sirali Siriwardene",
        "user_display_name": "Sirali",
        "user_title": "COO & Global Head of Change Execution, WPS",
        "rel_field": "surali_rel",
    },
}

MIN_COMBINED_SCORE = 6
MAX_PER_CATEGORY = 3


def build_user_briefing(user_id: str, inp: dict) -> dict:
    meta = USER_META[user_id]
    rel_field = meta["rel_field"]

    # Input JSON uses "surali" as the key; internal user_id is "sirali"
    input_key = "surali" if user_id == "sirali" else user_id

    raw_articles = inp.get("articles", [])
    talking_points_raw = inp.get("users", {}).get(input_key, {}).get("talking_points", [])

    # Filter and score articles for this user
    scored = []
    for art in raw_articles:
        hsbc = int(art.get("hsbc_relevancy", 0))
        user_rel = int(art.get(rel_field, art.get("user_relevance", 0)))
        combined = hsbc + user_rel
        if combined < MIN_COMBINED_SCORE:
            continue
        scored.append({**art, "_combined": combined, "_user_rel": user_rel})

    # Group by category, sort within category, cap at MAX_PER_CATEGORY
    categories: dict[str, list] = {}
    for art in scored:
        cat = art.get("category", "AI & Technology")
        categories.setdefault(cat, []).append(art)

    articles_by_category: dict[str, list] = {}
    all_articles_flat: list = []
    art_id_counter = 1

    for cat in CATEGORY_COLORS:
        if cat not in categories:
            continue
        arts = sorted(categories[cat], key=lambda a: -a["_combined"])[:MAX_PER_CATEGORY]
        bucket = []
        for art in arts:
            art_id = f"art{art_id_counter:02d}"
            art_id_counter += 1
            entry = {
                "id": art_id,
                "title": art.get("title", ""),
                "url": art.get("url", ""),
                "source": art.get("source", ""),
                "published_at": art.get("published_at", ""),
                "summary": art.get("summary", ""),
                "hsbc_relevancy": art.get("hsbc_relevancy", 0),
                "user_relevance": art["_user_rel"],
                "noise_level": art.get("noise_level", 2),
                "category": cat,
            }
            bucket.append(entry)
            all_articles_flat.append({
                "id": art_id,
                "title": art.get("title", "")[:90],
                "url": art.get("url", ""),
                "source": art.get("source", ""),
                "hsbc_relevancy": art.get("hsbc_relevancy", 0),
                "user_relevance": art["_user_rel"],
                "noise_level": art.get("noise_level", 2),
                "category": cat,
                "summary": art.get("summary", ""),
            })
        articles_by_category[cat] = bucket

    # Build talking points
    talking_points = []
    for tp in talking_points_raw:
        talking_points.append({
            "headline": tp.get("headline", ""),
            "context_html": tp.get("why_it_matters", tp.get("context_html", "")),
            "source_links": tp.get("source_links", []),
            "is_update": tp.get("is_update", False),
        })

    # Build chart categories subset
    chart_categories = {cat: CATEGORY_COLORS[cat] for cat in articles_by_category}

    now_utc = datetime.now(timezone.utc)
    return {
        "user_id": user_id,
        "user_name": meta["user_name"],
        "user_display_name": meta["user_display_name"],
        "user_title": meta["user_title"],
        "briefing_date": inp.get("briefing_date", ""),
        "date_str": inp.get("date_str", ""),
        "generated_at": now_utc.strftime("%-d %b %Y, %H:%M UTC"),
        "total_articles": len(all_articles_flat),
        "talking_points": talking_points,
        "articles_by_category": articles_by_category,
        "chart_data": {
            "articles": all_articles_flat,
            "categories": chart_categories,
        },
    }


def main():
    input_path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("/tmp/briefing_input.json")
    if not input_path.exists():
        print(f"Error: {input_path} not found", file=sys.stderr)
        sys.exit(1)

    inp = json.loads(input_path.read_text())

    for user_id in ("adam", "sirali"):
        out_dir = DOCS_DIR / user_id
        out_dir.mkdir(parents=True, exist_ok=True)
        data = build_user_briefing(user_id, inp)
        out_path = out_dir / "briefing_data.json"
        out_path.write_text(json.dumps(data, indent=2, ensure_ascii=False))
        print(f"✓  {out_path.relative_to(REPO_ROOT)}  ({data['total_articles']} articles, {len(data['talking_points'])} talking points)")


if __name__ == "__main__":
    main()
