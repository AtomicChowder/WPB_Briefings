"""
WPB Daily Intelligence Briefing — main generation script.

Usage:
    python src/main.py                   # generate for all users
    python src/main.py --user adam       # single user
    python src/main.py --dry-run         # fetch + analyse, skip publish/commit
"""

import argparse
import logging
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

# Resolve paths relative to repo root regardless of cwd
REPO_ROOT = Path(__file__).parent.parent
DOCS_DIR = REPO_ROOT / "docs"
SRC_DIR = REPO_ROOT / "src"
sys.path.insert(0, str(SRC_DIR))

from briefing_analyzer import BriefingAnalyzer
from config import USERS
from context_store import ContextStore
from html_generator import HTMLGenerator
from news_fetcher import NewsFetcher
from notion_publisher import NotionPublisher


def generate_for_user(user_id: str, dry_run: bool = False) -> str:
    user = USERS[user_id]
    date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    logger.info(f"── Generating briefing for {user.name} ({date_str}) ──")

    # 1. Fetch news
    logger.info("Fetching articles…")
    fetcher = NewsFetcher()
    articles = fetcher.fetch_articles(user)
    logger.info(f"  {len(articles)} articles fetched")

    if not articles:
        logger.warning("No articles found — aborting for this user")
        return ""

    # 2. Load previous context for deduplication
    ctx_store = ContextStore()
    prev_context = ctx_store.load_context(user_id)
    logger.info(f"  Context loaded: {len(prev_context.get('covered_urls', []))} prior URLs")

    # 3. Analyse with Claude (retry up to 3 times on API error)
    logger.info("Analysing with Claude API…")
    analyzer = BriefingAnalyzer()
    analysis = None
    for attempt in range(1, 4):
        try:
            analysis = analyzer.analyze_articles(articles, user, prev_context)
            logger.info(
                f"  Analysis complete: {len(analysis.scored_articles)} articles scored, "
                f"{len(analysis.talking_points)} talking points"
            )
            break
        except Exception as e:
            wait = 2 ** attempt
            logger.warning(f"  Claude API attempt {attempt} failed: {e}. Retrying in {wait}s…")
            time.sleep(wait)

    if analysis is None:
        logger.error("Claude API failed after 3 attempts — skipping this user")
        return ""

    # 4. Generate HTML
    logger.info("Generating HTML…")
    generator = HTMLGenerator()
    html = generator.generate(user, analysis, articles, date_str)

    if dry_run:
        logger.info("  [dry-run] skipping file write, Notion, and context update")
        preview_path = REPO_ROOT / f"output_{user_id}.html"
        preview_path.write_text(html, encoding="utf-8")
        logger.info(f"  Preview written to {preview_path}")
        return html

    # 5. Write HTML to docs/
    out_dir = DOCS_DIR / user_id
    out_dir.mkdir(parents=True, exist_ok=True)
    html_path = out_dir / "index.html"
    html_path.write_text(html, encoding="utf-8")
    logger.info(f"  HTML written → {html_path.relative_to(REPO_ROOT)}")

    # Also mirror to GCS if configured
    _mirror_to_gcs(user_id, html, date_str)

    # 6. Publish to Notion
    logger.info("Publishing to Notion…")
    try:
        publisher = NotionPublisher()
        publisher.publish_briefing(user, analysis, articles, date_str)
    except Exception as e:
        logger.warning(f"  Notion publish error (non-fatal): {e}")

    # 7. Update deduplication context
    ctx_store.update_context(user_id, analysis, date_str)
    logger.info(f"  Context updated")

    return html


def _mirror_to_gcs(user_id: str, html: str, date_str: str):
    bucket_name = os.getenv("GCS_BUCKET_NAME", "")
    if not bucket_name:
        return
    try:
        from google.cloud import storage
        client = storage.Client()
        bucket = client.bucket(bucket_name)
        for blob_name in [f"briefings/latest/{user_id}/index.html",
                          f"briefings/archive/{date_str}/{user_id}/index.html"]:
            b = bucket.blob(blob_name)
            b.upload_from_string(html, content_type="text/html")
            b.make_public()
        logger.info(f"  GCS mirror updated for {user_id}")
    except Exception as e:
        logger.warning(f"  GCS mirror failed (non-fatal): {e}")


def _write_docs_index():
    """Write a root docs/index.html that redirects to /adam."""
    idx = DOCS_DIR / "index.html"
    idx.write_text(
        '<!DOCTYPE html><html><head><meta http-equiv="refresh" content="0;url=adam/"></head>'
        '<body><a href="adam/">Redirecting…</a></body></html>',
        encoding="utf-8",
    )


def main():
    parser = argparse.ArgumentParser(description="WPB Briefing Generator")
    parser.add_argument("--user", choices=list(USERS.keys()), help="Generate for one user only")
    parser.add_argument("--dry-run", action="store_true", help="Analyse only, don't write output")
    args = parser.parse_args()

    if not os.getenv("ANTHROPIC_API_KEY"):
        logger.error("ANTHROPIC_API_KEY is not set — cannot proceed")
        sys.exit(1)

    DOCS_DIR.mkdir(parents=True, exist_ok=True)

    user_ids = [args.user] if args.user else list(USERS.keys())
    for uid in user_ids:
        generate_for_user(uid, dry_run=args.dry_run)

    if not args.dry_run:
        _write_docs_index()
        logger.info("docs/index.html written (redirects to /adam)")

    logger.info("✓ Done")


if __name__ == "__main__":
    main()
