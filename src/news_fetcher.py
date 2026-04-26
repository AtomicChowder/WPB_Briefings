"""
News fetcher — uses Anthropic web search tool via parallel Haiku agents.
No external NEWS_API_KEY required; billed to the ANTHROPIC_API_KEY account.

Each search query is dispatched concurrently to a claude-haiku-4-5 instance
with the web_search tool enabled. Results are deduplicated and returned as
a flat list of Article objects.
"""

import hashlib
import json
import logging
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from typing import List, Optional

import anthropic

from config import UserProfile, ARTICLES_PER_FETCH

logger = logging.getLogger(__name__)

HAIKU_MODEL = "claude-haiku-4-5-20251001"
MAX_PARALLEL_SEARCHES = 6
MAX_WEB_SEARCH_USES = 5   # searches per Haiku call
SEARCH_MAX_TOKENS = 2048


@dataclass
class Article:
    id: str
    title: str
    description: str
    content: str
    url: str
    source: str
    published_at: str
    image_url: Optional[str] = None

    @staticmethod
    def make_id(url: str) -> str:
        return hashlib.md5(url.encode()).hexdigest()[:12]


SEARCH_PROMPT = """\
Search for financial and banking news published in the last 48 hours about: {query}

After searching, respond with ONLY a valid JSON array of the most relevant articles found.
Each object must have exactly these keys:
  "title"        - full article headline
  "url"          - full article URL
  "source"       - publication name (e.g. "Financial Times", "Bloomberg")
  "description"  - 2-3 sentence summary of the article
  "published_at" - ISO date string (YYYY-MM-DD) if available, else ""

Return [] if no relevant results are found.
Output ONLY the JSON array — no markdown, no explanation."""


class NewsFetcher:
    def __init__(self):
        self.client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

    def fetch_articles(self, user: UserProfile) -> List[Article]:
        queries = user.search_keywords[:MAX_PARALLEL_SEARCHES]
        logger.info(f"Launching {len(queries)} parallel Haiku web searches…")

        articles: List[Article] = []
        seen_urls: set = set()

        with ThreadPoolExecutor(max_workers=MAX_PARALLEL_SEARCHES) as pool:
            futures = {pool.submit(self._search, q): q for q in queries}
            for future in as_completed(futures):
                query = futures[future]
                try:
                    results = future.result()
                    new = 0
                    for a in results:
                        if a.url and a.url not in seen_urls:
                            seen_urls.add(a.url)
                            articles.append(a)
                            new += 1
                    logger.info(f"  '{query[:50]}…' → {new} new articles")
                except Exception as e:
                    logger.warning(f"  Search failed for '{query[:50]}': {e}")

        articles.sort(key=lambda a: a.published_at, reverse=True)
        logger.info(f"Total unique articles: {len(articles)}")
        return articles[:ARTICLES_PER_FETCH]

    def _search(self, query: str) -> List[Article]:
        response = self.client.messages.create(
            model=HAIKU_MODEL,
            max_tokens=SEARCH_MAX_TOKENS,
            tools=[
                {
                    "type": "web_search_20250305",
                    "name": "web_search",
                    "max_uses": MAX_WEB_SEARCH_USES,
                }
            ],
            messages=[
                {
                    "role": "user",
                    "content": SEARCH_PROMPT.format(query=query),
                }
            ],
        )

        text = "".join(
            block.text for block in response.content if block.type == "text"
        )

        return self._parse_articles(text, query)

    @staticmethod
    def _parse_articles(text: str, query: str) -> List[Article]:
        start = text.find("[")
        end = text.rfind("]") + 1
        if start < 0 or end <= start:
            logger.debug(f"No JSON array found in response for '{query[:40]}'")
            return []

        try:
            data = json.loads(text[start:end])
        except json.JSONDecodeError as e:
            logger.debug(f"JSON parse error for '{query[:40]}': {e}")
            return []

        articles = []
        for item in data:
            url = (item.get("url") or "").strip()
            title = (item.get("title") or "").strip()
            if not url or not title:
                continue
            desc = (item.get("description") or "").strip()
            articles.append(
                Article(
                    id=Article.make_id(url),
                    title=title,
                    description=desc,
                    content=desc,
                    url=url,
                    source=(item.get("source") or "Unknown").strip(),
                    published_at=(item.get("published_at") or "").strip(),
                )
            )
        return articles
