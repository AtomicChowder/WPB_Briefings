import os
import hashlib
import logging
import requests
import feedparser
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import List, Optional
from dateutil import parser as dateparser

from config import UserProfile, ARTICLES_PER_FETCH, RSS_FEEDS

logger = logging.getLogger(__name__)

NEWS_API_BASE = "https://newsapi.org/v2/everything"
NEWS_API_KEY = os.getenv("NEWS_API_KEY", "")


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


class NewsFetcher:
    def fetch_articles(self, user: UserProfile) -> List[Article]:
        articles: List[Article] = []
        seen_urls: set = set()

        if NEWS_API_KEY:
            for query in user.search_keywords[:5]:
                try:
                    fetched = self._fetch_newsapi(query)
                    for a in fetched:
                        if a.url not in seen_urls:
                            seen_urls.add(a.url)
                            articles.append(a)
                except Exception as e:
                    logger.warning(f"NewsAPI fetch failed for '{query}': {e}")
        else:
            logger.info("NEWS_API_KEY not set — falling back to RSS feeds")

        if len(articles) < 10:
            for feed_url in RSS_FEEDS:
                try:
                    fetched = self._fetch_rss(feed_url)
                    for a in fetched:
                        if a.url not in seen_urls:
                            seen_urls.add(a.url)
                            articles.append(a)
                except Exception as e:
                    logger.warning(f"RSS fetch failed for {feed_url}: {e}")

        articles.sort(key=lambda a: a.published_at, reverse=True)
        return articles[:ARTICLES_PER_FETCH]

    def _fetch_newsapi(self, query: str) -> List[Article]:
        cutoff = (datetime.now(timezone.utc) - timedelta(days=2)).strftime("%Y-%m-%d")
        resp = requests.get(
            NEWS_API_BASE,
            params={
                "q": query,
                "apiKey": NEWS_API_KEY,
                "language": "en",
                "pageSize": 15,
                "sortBy": "publishedAt",
                "from": cutoff,
            },
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()

        articles = []
        for item in data.get("articles", []):
            url = item.get("url", "")
            if not url or url == "https://removed.com":
                continue
            title = item.get("title", "").strip()
            if not title or title == "[Removed]":
                continue
            articles.append(
                Article(
                    id=Article.make_id(url),
                    title=title,
                    description=item.get("description") or "",
                    content=(item.get("content") or item.get("description") or "")[:800],
                    url=url,
                    source=item.get("source", {}).get("name", "Unknown"),
                    published_at=item.get("publishedAt", ""),
                    image_url=item.get("urlToImage"),
                )
            )
        return articles

    def _fetch_rss(self, feed_url: str) -> List[Article]:
        feed = feedparser.parse(feed_url)
        cutoff = datetime.now(timezone.utc) - timedelta(days=3)
        articles = []

        for entry in feed.entries[:20]:
            url = entry.get("link", "")
            if not url:
                continue

            pub_str = ""
            if hasattr(entry, "published_parsed") and entry.published_parsed:
                dt = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
                if dt < cutoff:
                    continue
                pub_str = dt.isoformat()

            articles.append(
                Article(
                    id=Article.make_id(url),
                    title=entry.get("title", "").strip(),
                    description=entry.get("summary", "")[:400],
                    content=entry.get("summary", "")[:800],
                    url=url,
                    source=feed.feed.get("title", "RSS Feed"),
                    published_at=pub_str,
                )
            )
        return articles
