import logging
import os
from datetime import datetime, timezone
from typing import List

from briefing_analyzer import AnalysisResult
from config import CATEGORY_COLORS, UserProfile
from news_fetcher import Article

logger = logging.getLogger(__name__)


class NotionPublisher:
    """
    Publishes daily briefings as pages in a Notion database.
    Database should be named "WPB Weekly Intelligence Briefings".
    Set NOTION_TOKEN and NOTION_DATABASE_ID in environment.
    """

    NOTION_VERSION = "2022-06-28"
    BASE_URL = "https://api.notion.com/v1"

    def __init__(self):
        self.token = os.getenv("NOTION_TOKEN", "")
        self.database_id = os.getenv("NOTION_DATABASE_ID", "")
        self._enabled = bool(self.token and self.database_id)
        if not self._enabled:
            logger.info("Notion publishing disabled — NOTION_TOKEN or NOTION_DATABASE_ID not set")

    def publish_briefing(
        self,
        user: UserProfile,
        analysis: AnalysisResult,
        raw_articles: List[Article],
        date_str: str,
    ):
        if not self._enabled:
            return

        import requests

        url_to_article = {a.url: a for a in raw_articles}
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Notion-Version": self.NOTION_VERSION,
            "Content-Type": "application/json",
        }

        try:
            display_date = datetime.strptime(date_str, "%Y-%m-%d").strftime("%-d %B %Y")
        except Exception:
            display_date = date_str

        page_title = f"[{user.display_name}] WPB Briefing — {display_date}"
        blocks = self._build_blocks(user, analysis, url_to_article, date_str)

        payload = {
            "parent": {"database_id": self.database_id},
            "properties": {
                "Name": {"title": [{"text": {"content": page_title}}]},
                "User": {"rich_text": [{"text": {"content": user.name}}]},
                "Date": {"date": {"start": date_str}},
                "Articles": {"number": len(analysis.scored_articles)},
            },
            "children": blocks[:100],  # Notion API max 100 blocks per request
        }

        try:
            resp = requests.post(
                f"{self.BASE_URL}/pages",
                headers=headers,
                json=payload,
                timeout=15,
            )
            resp.raise_for_status()
            page_id = resp.json().get("id", "")
            logger.info(f"Notion page created for {user.name}: {page_id}")

            # Append remaining blocks if any
            if len(blocks) > 100:
                requests.patch(
                    f"{self.BASE_URL}/blocks/{page_id}/children",
                    headers=headers,
                    json={"children": blocks[100:200]},
                    timeout=15,
                )
        except Exception as e:
            logger.error(f"Notion publish failed for {user.name}: {e}")

    def _build_blocks(self, user, analysis, url_to_article, date_str):
        blocks = []

        # Header callout
        blocks.append({
            "type": "callout",
            "callout": {
                "rich_text": [{"type": "text", "text": {
                    "content": f"Daily intelligence briefing for {user.name} · {user.title}"
                }}],
                "icon": {"emoji": "📊"},
                "color": "red_background",
            },
        })
        blocks.append({"type": "divider", "divider": {}})

        # Talking points
        blocks.append(self._heading2("🎯 Key Talking Points"))
        for i, tp in enumerate(analysis.talking_points, 1):
            blocks.append(self._heading3(f"{i}. {tp.headline}"))
            blocks.append(self._paragraph(tp.context))
            if tp.supporting_article_urls:
                for url in tp.supporting_article_urls[:2]:
                    art = url_to_article.get(url)
                    link_text = art.title if art else url
                    blocks.append(self._bullet(link_text, url=url))
        blocks.append({"type": "divider", "divider": {}})

        # Articles by category
        blocks.append(self._heading2("📰 Intelligence Feed"))
        from config import CATEGORIES
        articles_by_cat: dict = {}
        for scored in analysis.scored_articles:
            art = url_to_article.get(scored.article_url)
            if art is None:
                continue
            articles_by_cat.setdefault(scored.category, []).append((scored, art))

        for cat, items in articles_by_cat.items():
            blocks.append(self._heading3(cat))
            for scored, art in items[:5]:
                label = (
                    f"[HSBC {scored.hsbc_relevancy}/10 · Rel {scored.user_relevance}/10 · "
                    f"Noise {'●' * scored.noise_level}{'○' * (5 - scored.noise_level)}]  "
                    f"{art.title}"
                )
                blocks.append(self._bullet(label, url=art.url))
                if scored.summary:
                    blocks.append(self._paragraph(scored.summary, color="gray"))

        blocks.append({"type": "divider", "divider": {}})
        blocks.append(self._paragraph(
            f"Generated {datetime.now(timezone.utc).strftime('%d %b %Y %H:%M UTC')} · "
            f"Powered by Claude AI (Anthropic)",
            color="gray",
        ))
        return blocks

    @staticmethod
    def _heading2(text: str) -> dict:
        return {"type": "heading_2", "heading_2": {
            "rich_text": [{"type": "text", "text": {"content": text}}]
        }}

    @staticmethod
    def _heading3(text: str) -> dict:
        return {"type": "heading_3", "heading_3": {
            "rich_text": [{"type": "text", "text": {"content": text}}]
        }}

    @staticmethod
    def _paragraph(text: str, color: str = "default") -> dict:
        return {"type": "paragraph", "paragraph": {
            "rich_text": [{"type": "text", "text": {"content": text[:2000]}}],
            "color": color,
        }}

    @staticmethod
    def _bullet(text: str, url: str = "") -> dict:
        rich = [{"type": "text", "text": {"content": text[:2000]}}]
        if url:
            rich = [{"type": "text", "text": {"content": text[:2000], "link": {"url": url}}}]
        return {"type": "bulleted_list_item", "bulleted_list_item": {"rich_text": rich}}
