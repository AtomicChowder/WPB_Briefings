import json
import logging
import os
import re
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple

from jinja2 import Environment, FileSystemLoader, select_autoescape

from briefing_analyzer import AnalysisResult, ScoredArticle, TalkingPoint
from config import (
    CATEGORY_COLORS,
    MAX_ARTICLES_PER_CATEGORY,
    MIN_ARTICLE_SCORE,
    UserProfile,
)
from news_fetcher import Article

logger = logging.getLogger(__name__)

TEMPLATES_DIR = os.path.join(os.path.dirname(__file__), "..", "templates")


def _slugify(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def _bold_names(text: str) -> str:
    """Convert **Name, Title** markdown to <strong> HTML."""
    return re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)


def _format_date_display(iso_str: str) -> str:
    if not iso_str:
        return ""
    try:
        dt = datetime.fromisoformat(iso_str.replace("Z", "+00:00"))
        return dt.strftime("%-d %b %Y")
    except Exception:
        return iso_str[:10]


class HTMLGenerator:
    def __init__(self):
        self.env = Environment(
            loader=FileSystemLoader(TEMPLATES_DIR),
            autoescape=select_autoescape(["html"]),
        )
        self.env.filters["slugify"] = _slugify
        self.env.filters["bold_names"] = _bold_names
        self.env.filters["format_date"] = _format_date_display

    def generate(
        self,
        user: UserProfile,
        analysis: AnalysisResult,
        raw_articles: List[Article],
        date_str: str,
    ) -> str:
        url_to_article: Dict[str, Article] = {a.url: a for a in raw_articles}

        scored_map: Dict[str, ScoredArticle] = {
            s.article_url: s for s in analysis.scored_articles
        }

        enriched = []
        for scored in analysis.scored_articles:
            raw = url_to_article.get(scored.article_url)
            if raw is None:
                continue
            combined_score = scored.hsbc_relevancy + scored.user_relevance
            if combined_score < MIN_ARTICLE_SCORE:
                continue
            enriched.append(
                {
                    "id": raw.id,
                    "title": raw.title,
                    "url": raw.url,
                    "source": raw.source,
                    "published_at": raw.published_at,
                    "summary": scored.summary,
                    "hsbc_relevancy": scored.hsbc_relevancy,
                    "user_relevance": scored.user_relevance,
                    "noise_level": scored.noise_level,
                    "category": scored.category,
                    "key_entities": scored.key_entities,
                    "combined_score": combined_score,
                }
            )

        enriched.sort(key=lambda x: x["combined_score"], reverse=True)

        articles_by_category: Dict[str, List[dict]] = {}
        category_counts: Dict[str, int] = {}
        for article in enriched:
            cat = article["category"]
            if cat not in articles_by_category:
                articles_by_category[cat] = []
            if category_counts.get(cat, 0) < MAX_ARTICLES_PER_CATEGORY:
                articles_by_category[cat].append(article)
                category_counts[cat] = category_counts.get(cat, 0) + 1

        chart_articles = [
            a for articles in articles_by_category.values() for a in articles
        ]
        chart_data = {
            "articles": [
                {
                    "id": a["id"],
                    "title": a["title"][:90] + ("…" if len(a["title"]) > 90 else ""),
                    "url": a["url"],
                    "source": a["source"],
                    "hsbc_relevancy": a["hsbc_relevancy"],
                    "user_relevance": a["user_relevance"],
                    "noise_level": a["noise_level"],
                    "category": a["category"],
                    "summary": a["summary"],
                }
                for a in chart_articles
            ],
            "categories": {
                cat: CATEGORY_COLORS.get(cat, "#64748b")
                for cat in articles_by_category.keys()
            },
        }

        talking_points_display = []
        for tp in analysis.talking_points:
            source_links = []
            for url in tp.supporting_article_urls[:3]:
                raw = url_to_article.get(url)
                title = raw.title if raw else url
                source_links.append((url, title[:60] + ("…" if len(title) > 60 else "")))
            talking_points_display.append(
                {
                    "headline": tp.headline,
                    "context_html": _bold_names(tp.context),
                    "source_links": source_links,
                    "is_update": tp.is_update,
                    "update_context": tp.update_context,
                }
            )

        generated_at = datetime.now(timezone.utc).strftime("%d %b %Y, %H:%M UTC")

        try:
            display_date = datetime.strptime(date_str, "%Y-%m-%d").strftime("%A, %-d %B %Y")
        except Exception:
            display_date = date_str

        template = self.env.get_template("briefing.html")
        return template.render(
            user=user,
            briefing_date=display_date,
            date_str=date_str,
            talking_points=talking_points_display,
            articles_by_category=articles_by_category,
            category_colors=CATEGORY_COLORS,
            chart_data_json=json.dumps(chart_data),
            generated_at=generated_at,
            total_articles=len(chart_articles),
        )
