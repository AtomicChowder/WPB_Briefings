"""
HTML renderer for WPB briefings.
Reads docs/{user_id}/briefing_data.json and writes docs/{user_id}/index.html.
No API calls — pure Jinja2 templating.

Usage:
    python src/render.py adam
    python src/render.py sirali
"""

import json
import re
import sys
from datetime import datetime, timezone
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


def render(user_id: str) -> None:
    data_path = DOCS_DIR / user_id / "briefing_data.json"
    if not data_path.exists():
        print(f"Error: {data_path} not found", file=sys.stderr)
        sys.exit(1)

    data = json.loads(data_path.read_text(encoding="utf-8"))

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
        date_str=data["date_str"],
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
    )

    out_path = DOCS_DIR / user_id / "index.html"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(html, encoding="utf-8")
    print(f"✓  {out_path.relative_to(REPO_ROOT)}")


if __name__ == "__main__":
    user_id = sys.argv[1] if len(sys.argv) > 1 else "adam"
    render(user_id)
