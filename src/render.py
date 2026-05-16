"""
HTML renderer for WPB briefings.
Reads docs/{user_id}/briefing_data.json and writes docs/{user_id}/index.html
plus a dated archive copy docs/{user_id}/{date_str}.html.

A nav.json file tracks all briefing dates for that user so the template can
render prev/next navigation links.

Usage:
    python src/render.py adam
    python src/render.py surali
"""

import json
import re
import sys
from datetime import date as _date, datetime, timezone
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

REPO_ROOT = Path(__file__).parent.parent
TEMPLATES_DIR = REPO_ROOT / "templates"
DOCS_DIR = REPO_ROOT / "docs"


def _slugify(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def _format_date(iso_str: str) -> str:
    if not iso_str:
        return ""
    try:
        dt = datetime.fromisoformat(iso_str.replace("Z", "+00:00"))
        return dt.strftime("%-d %b %Y")
    except Exception:
        return iso_str[:10]


def _fmt_nav_date(iso_str: str) -> str:
    """Short date label for nav buttons, e.g. '15 May 2026'."""
    try:
        return _date.fromisoformat(iso_str).strftime("%-d %b %Y")
    except Exception:
        return iso_str


def _load_nav(user_dir: Path) -> list[str]:
    nav_path = user_dir / "nav.json"
    if nav_path.exists():
        try:
            return json.loads(nav_path.read_text(encoding="utf-8"))
        except Exception:
            pass
    return []


def _save_nav(user_dir: Path, dates: list[str]) -> None:
    (user_dir / "nav.json").write_text(
        json.dumps(sorted(set(dates)), indent=2), encoding="utf-8"
    )


def render(user_id: str) -> None:
    user_dir = DOCS_DIR / user_id
    data_path = user_dir / "briefing_data.json"
    if not data_path.exists():
        print(f"Error: {data_path} not found", file=sys.stderr)
        sys.exit(1)

    data = json.loads(data_path.read_text(encoding="utf-8"))
    date_str = data["date_str"]

    # Load nav history, add today, compute prev link
    nav_dates = _load_nav(user_dir)
    if date_str not in nav_dates:
        nav_dates.append(date_str)
    nav_dates = sorted(set(nav_dates))
    idx = nav_dates.index(date_str)
    prev_date = nav_dates[idx - 1] if idx > 0 else None
    prev_label = _fmt_nav_date(prev_date) if prev_date else None
    prev_url = f"./{prev_date}.html" if prev_date else None

    env = Environment(
        loader=FileSystemLoader(str(TEMPLATES_DIR)),
        autoescape=select_autoescape(["html"]),
    )
    env.filters["slugify"] = _slugify
    env.filters["format_date"] = _format_date
    env.filters["bold_names"] = lambda t: t  # already HTML in JSON

    class _User:
        name = data["user_name"]
        display_name = data["user_display_name"]
        title = data["user_title"]

    html = env.get_template("briefing.html").render(
        user=_User(),
        briefing_date=data["briefing_date"],
        date_str=date_str,
        talking_points=data["talking_points"],
        articles_by_category=data["articles_by_category"],
        category_colors={
            "AI & Technology": "#6366f1",
            "HSBC News": "#dc2626",
            "Competitor Intelligence": "#0891b2",
            "Private Banking & Wealth": "#059669",
            "Regulatory & Markets": "#d97706",
            "Operations & Change": "#7c3aed",
        },
        chart_data_json=json.dumps(data["chart_data"]),
        generated_at=data.get("generated_at", ""),
        total_articles=data.get("total_articles", 0),
        prev_label=prev_label,
        prev_url=prev_url,
    )

    user_dir.mkdir(parents=True, exist_ok=True)

    # Always write the canonical index.html (latest briefing)
    out_path = user_dir / "index.html"
    out_path.write_text(html, encoding="utf-8")
    print(f"✓  {out_path.relative_to(REPO_ROOT)}")

    # Also archive as a dated snapshot so old briefings remain browsable
    dated_path = user_dir / f"{date_str}.html"
    dated_path.write_text(html, encoding="utf-8")
    print(f"✓  {dated_path.relative_to(REPO_ROOT)}")

    # Persist the updated nav list
    _save_nav(user_dir, nav_dates)


if __name__ == "__main__":
    user_id = sys.argv[1] if len(sys.argv) > 1 else "adam"
    render(user_id)
