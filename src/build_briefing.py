"""
Build briefing_data.json for each user from a shared briefing_input.json.

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

USERS = {
    "adam": {
        "user_id": "adam",
        "user_name": "Adam Chow",
        "user_display_name": "Adam",
        "user_title": "Head of Change Execution, WPB Private Banking & Wealth Solutions, Asia Pacific",
        "rel_field": "adam_rel",
    },
    "sirali": {
        "user_id": "sirali",
        "user_name": "Sirali Siriwardene",
        "user_display_name": "Sirali",
        "user_title": "COO & Global Head of Change Execution, WPS",
        "rel_field": "surali_rel",
    },
}

MAX_PER_CATEGORY = 5
MIN_COMBINED_SCORE = 6


def build_context_html(tp: dict) -> str:
    why = tp.get("why_it_matters", "")
    bullets = tp.get("bullets", [])
    context_html = tp.get("context_html", "")
    if context_html:
        return context_html
    if bullets:
        bullet_html = "".join(f"<li>{b}</li>" for b in bullets)
        return f"{why} <ul style='margin:8px 0 0 16px;'>{bullet_html}</ul>"
    return why


def build_for_user(inp: dict, user_key: str) -> dict:
    meta = USERS[user_key]
    rel_field = meta["rel_field"]

    now_utc = datetime.now(timezone.utc)
    generated_at = now_utc.strftime("%-d %b %Y, %H:%M UTC")

    # Filter and score articles
    raw_articles = inp.get("articles", [])
    scored = []
    for art in raw_articles:
        hsbc = art.get("hsbc_relevancy", 0)
        rel = art.get(rel_field, 0)
        if hsbc + rel < MIN_COMBINED_SCORE:
            continue
        scored.append({**art, "_user_rel": rel, "_combined": hsbc + rel})

    # Assign sequential IDs, cap per category
    by_cat: dict[str, list] = {}
    for art in scored:
        cat = art.get("category", "AI & Technology")
        by_cat.setdefault(cat, []).append(art)

    articles_by_category: dict[str, list] = {}
    all_articles_flat: list[dict] = []
    art_id = 1

    for cat in CATEGORY_COLORS:
        if cat not in by_cat:
            continue
        cat_arts = sorted(by_cat[cat], key=lambda a: a["_combined"], reverse=True)
        cat_arts = cat_arts[:MAX_PER_CATEGORY]
        out_arts = []
        for art in cat_arts:
            a_id = f"art{art_id:02d}"
            art_id += 1
            out_art = {
                "id": a_id,
                "title": art["title"],
                "url": art["url"],
                "source": art.get("source", ""),
                "published_at": art.get("published_at", ""),
                "summary": art.get("summary", ""),
                "hsbc_relevancy": art["hsbc_relevancy"],
                "user_relevance": art["_user_rel"],
                "noise_level": art.get("noise_level", 2),
                "category": cat,
            }
            out_arts.append(out_art)
            all_articles_flat.append({
                "id": a_id,
                "title": art["title"][:90],
                "url": art["url"],
                "source": art.get("source", ""),
                "hsbc_relevancy": art["hsbc_relevancy"],
                "user_relevance": art["_user_rel"],
                "noise_level": art.get("noise_level", 2),
                "category": cat,
                "summary": art.get("summary", "")[:200],
            })
        articles_by_category[cat] = out_arts

    # Talking points — convert from input format to output format
    raw_tps = inp.get("users", {}).get(user_key, {}).get("talking_points", [])
    talking_points = []
    for tp in raw_tps:
        source_links_raw = tp.get("source_links", [])
        # Template expects list of [url, title] arrays
        source_links = []
        for sl in source_links_raw:
            if isinstance(sl, dict):
                source_links.append([sl.get("url", ""), sl.get("title", "")])
            elif isinstance(sl, (list, tuple)) and len(sl) >= 2:
                source_links.append([sl[0], sl[1]])
        talking_points.append({
            "headline": tp.get("headline", ""),
            "context_html": build_context_html(tp),
            "source_links": source_links,
            "is_update": tp.get("is_update", False),
        })

    # Chart data — only categories present
    present_cats = {a["category"] for a in all_articles_flat}
    chart_categories = {k: v for k, v in CATEGORY_COLORS.items() if k in present_cats}

    data = {
        "user_id": meta["user_id"],
        "user_name": meta["user_name"],
        "user_display_name": meta["user_display_name"],
        "user_title": meta["user_title"],
        "briefing_date": inp["briefing_date"],
        "date_str": inp["date_str"],
        "generated_at": generated_at,
        "total_articles": len(all_articles_flat),
        "talking_points": talking_points,
        "articles_by_category": articles_by_category,
        "chart_data": {
            "articles": all_articles_flat,
            "categories": chart_categories,
        },
    }

    out_path = DOCS_DIR / meta["user_id"] / "briefing_data.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"✓  {out_path.relative_to(REPO_ROOT)}  ({len(all_articles_flat)} articles)")
    return data


def main():
    if len(sys.argv) < 2:
        print("Usage: python src/build_briefing.py <briefing_input.json>", file=sys.stderr)
        sys.exit(1)
    inp_path = Path(sys.argv[1])
    inp = json.loads(inp_path.read_text(encoding="utf-8"))
    for user_key in ("adam", "sirali"):
        build_for_user(inp, user_key)


if __name__ == "__main__":
    main()
