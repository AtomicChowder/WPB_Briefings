"""Build docs/adam/briefing_data.json from a single input file.

The Claude Code Routine produces /tmp/briefing_input.json containing:
- the date strings
- a flat list of scored articles (with adam_rel on each)
- talking points
- optional breaking_news

This script handles all the deterministic JSON gymnastics: filtering by
combined score >= 6, grouping by category, capping at 3 articles per category,
sorting, and writing the final briefing_data.json file.

Doing this in a Python script (not via Claude's Write/Edit tools) avoids the
stream-idle timeouts that have been the dominant failure mode.

Usage:
    python src/build_briefing.py /tmp/briefing_input.json

Input schema (briefing_input.json):
{
  "date_str": "2026-05-01",
  "briefing_date": "Friday, 1 May 2026",
  "articles": [
    {
      "id": "art01",
      "title": "...",
      "url": "https://...",
      "source": "Reuters",
      "published_at": "2026-05-01",
      "summary": "One sentence — why should the user care?",
      "hsbc_relevancy": 7,
      "adam_rel": 9,
      "noise_level": 3,
      "category": "AI & Technology"
    }
  ],
  "users": {
    "adam": {"talking_points": [{"headline": "...", "why_it_matters": "...",
                                  "bullets": ["...", "..."],
                                  "source_links": [{"url": "...", "title": "..."}],
                                  "is_update": false}]}
  },
  "breaking_news": {"adam": []}   // optional
}
"""
from __future__ import annotations

import json
import sys
from datetime import date, datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
HIST_PATH = REPO / "context" / "history.json"

CATEGORY_COLOURS = {
    "AI & Technology":          "#6366f1",
    "HSBC News":                "#dc2626",
    "Competitor Intelligence":  "#0891b2",
    "Private Banking & Wealth": "#059669",
    "Regulatory & Markets":     "#d97706",
    "Operations & Change":      "#7c3aed",
    "On Adam's Desk":           "#be123c",
}

# Single source of truth for user metadata. Names are hardcoded here so a
# typo in the routine prompt cannot leak into published output.
#
# This is a single-user system (Adam Chow only). Do not add a second user
# without explicit instruction — a prior second recipient was fully removed.
USERS = {
    "adam": {
        "user_name":         "Adam Chow",
        "user_display_name": "Adam",
        "user_title":        "Head of Change Execution, WPB Private Banking & Wealth Solutions, Asia Pacific",
        "score_key":         "adam_rel",
    },
}

REQUIRED_ARTICLE_FIELDS = (
    "id", "title", "url", "source", "published_at", "summary",
    "hsbc_relevancy", "adam_rel", "noise_level", "category",
)

MAX_PER_CATEGORY = 3
MIN_COMBINED_SCORE = 6

# Thread hits (added 2026-09-17). The combined-score gate asks "is this about HSBC"; an Avaloq
# or eCRM story is not, scores 2-3 on hsbc_relevancy, and was dropped before it could be seen.
# thread_rel / threads arrive on /tmp/briefing_input.json (never committed) and are STRIPPED
# from every output below, so internal thread labels cannot reach docs/ or briefing_data.json.
THREAD_CATEGORY = "On Adam's Desk"
MIN_THREAD_REL = 5                  # at or above this, an article is a thread hit
HIGH_THREAD_REL = 8                 # "lands on his desk" band; reserved by the sort order
MIN_COMBINED_SCORE_THREAD = 3       # relaxed gate, thread hits only
LENS_FIELDS = ("thread_rel", "threads")


def _strip_lens(a: dict) -> dict:
    """Remove internal lens fields. docs/ and briefing_data.json are PUBLIC."""
    return {k: v for k, v in a.items() if k not in LENS_FIELDS}


def _validate_articles(articles):
    seen_ids = set()
    for a in articles:
        for k in REQUIRED_ARTICLE_FIELDS:
            if k not in a:
                raise SystemExit(f"article missing field {k!r}: {a.get('id', '<no-id>')}")
        if a["id"] in seen_ids:
            raise SystemExit(f"duplicate article id: {a['id']}")
        seen_ids.add(a["id"])
        if a["category"] not in CATEGORY_COLOURS:
            raise SystemExit(f"unknown category {a['category']!r} on {a['id']}")


def _normalize_talking_points(tps: list[dict]) -> list[dict]:
    """Coerce talking points into the exact shape templates/briefing.html expects:
    headline, context_html (analysis), source_links as [[url, title], ...] pairs."""
    out = []
    for tp in tps or []:
        tp = dict(tp)
        if not tp.get("context_html"):
            parts = [tp.pop("why_it_matters", "")] + list(tp.pop("bullets", []))
            tp["context_html"] = " ".join(p for p in parts if p)
        if not tp.get("headline") or not tp.get("context_html"):
            raise SystemExit(f"talking point missing headline/context_html: {tp}")
        links = []
        for link in tp.get("source_links", []):
            if isinstance(link, dict):
                links.append([link["url"], link["title"]])
            else:
                links.append(list(link))
        tp["source_links"] = links
        tp.setdefault("is_update", False)
        out.append(tp)
    return out


def _build_for_user(user_id: str, raw: dict, generated_at: str,
                    briefing_dt: date, covered_urls: set[str]) -> dict:
    meta = USERS[user_id]
    score_key = meta["score_key"]

    cats: dict[str, list[dict]] = {}
    flat: list[dict] = []
    for a in raw["articles"]:
        is_update = a.get("is_update", False)

        # Gate 1 — freshness: reject articles older than 48 h unless flagged as update
        age_days = (briefing_dt - date.fromisoformat(a["published_at"])).days
        if age_days > 1 and not is_update:
            print(f"[build] SKIP stale {a['id']} ({a['published_at']}, {age_days}d old)")
            continue

        # Gate 2 — dedup: reject URLs already in this user's history unless flagged as update
        if a["url"] in covered_urls and not is_update:
            print(f"[build] SKIP duplicate {a['id']} already covered for {user_id}")
            continue

        combined = a["hsbc_relevancy"] + a[score_key]
        try:
            thread_rel = int(a.get("thread_rel") or 0)
        except (TypeError, ValueError):
            thread_rel = 0
        is_thread_hit = thread_rel >= MIN_THREAD_REL
        floor = MIN_COMBINED_SCORE_THREAD if is_thread_hit else MIN_COMBINED_SCORE
        if combined < floor:
            continue
        art = dict(a)
        art["user_relevance"] = a[score_key]
        # The BUILDER routes, not the routine - the routine never emits this category name.
        cats.setdefault(THREAD_CATEGORY if is_thread_hit else a["category"], []).append(art)

    # Sort each category by combined score, cap at MAX_PER_CATEGORY
    for cat, items in cats.items():
        if cat == THREAD_CATEGORY:
            # Rank by how directly it lands on a live thread, then by combined score.
            # thread_rel leads the sort key, so a thread_rel >= HIGH_THREAD_REL article is
            # always inside the cap when one exists — the reserved slot is structural and
            # needs no separate swap. Keep thread_rel first if this sort is ever revisited.
            items.sort(key=lambda x: (int(x.get("thread_rel") or 0),
                                      x["hsbc_relevancy"] + x[score_key]), reverse=True)
            cats[cat] = items[:MAX_PER_CATEGORY]
        else:
            items.sort(key=lambda x: x["hsbc_relevancy"] + x[score_key], reverse=True)
            cats[cat] = items[:MAX_PER_CATEGORY]

    # "On Adam's Desk" is emitted FIRST; the rest keep their existing order.
    if THREAD_CATEGORY in cats:
        cats = {THREAD_CATEGORY: cats[THREAD_CATEGORY],
                **{k: v for k, v in cats.items() if k != THREAD_CATEGORY}}

    # Drop empty categories (none should be, but be defensive)
    cats = {k: [_strip_lens(a) for a in v] for k, v in cats.items() if v}

    # Flat list mirrors what's in articles_by_category (post-cap)
    final_ids: set[str] = {a["id"] for arts in cats.values() for a in arts}
    flat = [_strip_lens(dict(a, user_relevance=a[score_key]))
            for a in raw["articles"] if a["id"] in final_ids]

    user_block = (raw.get("users") or {}).get(user_id, {}) or {}
    breaking = (raw.get("breaking_news") or {}).get(user_id, []) or []

    return {
        "user_id":           user_id,
        "user_name":         meta["user_name"],
        "user_display_name": meta["user_display_name"],
        "user_title":        meta["user_title"],
        "briefing_date":     raw["briefing_date"],
        "date_str":          raw["date_str"],
        "generated_at":      generated_at,
        "total_articles":    len(flat),
        "breaking_news":     breaking,
        "talking_points":    _normalize_talking_points(user_block.get("talking_points", [])),
        "articles_by_category": cats,
        "chart_data": {
            "articles":   flat,
            "categories": {k: CATEGORY_COLOURS[k] for k in cats},
        },
    }


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print("usage: build_briefing.py <briefing_input.json>", file=sys.stderr)
        return 1

    raw = json.loads(Path(argv[1]).read_text(encoding="utf-8"))

    for required in ("date_str", "briefing_date", "articles", "users"):
        if required not in raw:
            print(f"input missing required field: {required}", file=sys.stderr)
            return 1

    _validate_articles(raw["articles"])

    generated_at = datetime.now(timezone.utc).strftime("%-d %b %Y, %H:%M UTC")
    briefing_dt = date.fromisoformat(raw["date_str"])

    hist = {}
    if HIST_PATH.exists():
        hist = json.loads(HIST_PATH.read_text(encoding="utf-8"))

    for user_id in USERS:
        # Dedup against prior days only — a same-day re-run must not treat its
        # own earlier output as "already covered" (re-run idempotency).
        ub = hist.get(user_id, {})
        if ub.get("daily"):
            covered_urls = {u for d in ub["daily"] if d.get("date") != raw["date_str"]
                            for u in d.get("urls", [])}
        else:
            covered_urls = set(ub.get("covered_urls", []))
        data = _build_for_user(user_id, raw, generated_at,
                               briefing_dt=briefing_dt, covered_urls=covered_urls)
        out = REPO / "docs" / user_id / "briefing_data.json"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(data, indent=2), encoding="utf-8")
        cats_summary = ", ".join(f"{k}:{len(v)}" for k, v in data["articles_by_category"].items())
        print(f"[build] {out.relative_to(REPO)} — {data['total_articles']} articles "
              f"({cats_summary}), {len(data['talking_points'])} TPs")

    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
