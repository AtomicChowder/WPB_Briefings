import json
import logging
import os
from dataclasses import dataclass, field
from typing import List, Optional

import anthropic

from config import UserProfile, CATEGORIES
from news_fetcher import Article

logger = logging.getLogger(__name__)

ANALYSIS_SYSTEM_PROMPT = """You are a financial intelligence analyst specializing in HSBC WPB (Wealth and Personal Banking) \
competitive intelligence and senior executive briefings. Your analyses are used by C-suite and senior VP level \
executives at HSBC. You are precise, insight-driven, and always context-aware.

## Scoring Rubrics

**hsbc_relevancy (0–10)**: How directly does this affect HSBC WPB's operations, strategy, or competitive position?
- 0–2: Generic macro news, tangentially related to banking
- 3–4: General financial industry news, broad banking sector
- 5–6: Relevant to HSBC's competitive landscape or a key competitor
- 7–8: Directly related to HSBC's business areas, products, or key strategic competitors
- 9–10: Directly about HSBC WPB or a critical strategic threat/opportunity

**user_relevance (0–10)**: How useful is this for the specific user's role, responsibilities, and stated interests?
- 0–2: Unlikely to be useful given their role
- 3–4: Marginally relevant background information
- 5–6: Relevant to their domain, worth awareness
- 7–8: Directly actionable for their role or key interest area
- 9–10: Critical intelligence for their immediate responsibilities

**noise_level (1–5)**: Estimated media coverage breadth
- 1: Single source, niche coverage
- 2: Two to three sources
- 3: Moderate — picked up by several outlets
- 4: Wide coverage, trending in financial media
- 5: Major story, all major financial outlets covering it

## Category Definitions
- **AI & Technology**: AI, machine learning, digital banking technology, fintech platforms
- **HSBC News**: Any news directly about HSBC, its people, products, or strategy
- **Competitor Intelligence**: News about DBS, Standard Chartered, Citi, UBS, JP Morgan, BOA, Deutsche, BOC, Hang Seng, PayMe
- **Private Banking & Wealth**: Wealth management trends, HNW/UHNW insights, investment products
- **Regulatory & Markets**: Regulatory changes, market conditions, macro events affecting banking
- **Operations & Change**: Operational transformation, agile delivery, change management, cost efficiency

## Name Formatting
In talking point context text: wrap all person names with **double asterisks** (e.g., **John Smith, CEO of DBS**). \
Include job titles wherever known. Bold organisation names are NOT required — only people.

## Context Awareness
If previously covered article URLs or topics are provided, do not repeat them as talking points unless there has been \
a material development or significant update. Mark updates explicitly."""

ANALYSIS_TOOL = {
    "name": "submit_briefing_analysis",
    "description": "Submit the structured analysis of news articles and generate the daily intelligence briefing",
    "input_schema": {
        "type": "object",
        "required": ["scored_articles", "talking_points"],
        "properties": {
            "scored_articles": {
                "type": "array",
                "description": "All articles scored and categorised",
                "items": {
                    "type": "object",
                    "required": ["article_url", "hsbc_relevancy", "user_relevance", "noise_level", "category", "summary"],
                    "properties": {
                        "article_url": {"type": "string"},
                        "hsbc_relevancy": {"type": "integer", "minimum": 0, "maximum": 10},
                        "user_relevance": {"type": "integer", "minimum": 0, "maximum": 10},
                        "noise_level": {"type": "integer", "minimum": 1, "maximum": 5},
                        "category": {
                            "type": "string",
                            "enum": [
                                "AI & Technology", "HSBC News", "Competitor Intelligence",
                                "Private Banking & Wealth", "Regulatory & Markets", "Operations & Change",
                            ],
                        },
                        "summary": {
                            "type": "string",
                            "description": "2–3 sentence neutral summary of the article",
                        },
                        "key_entities": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Named people in 'Name, Title' format. Leave empty if none.",
                        },
                        "is_update_of": {
                            "type": "string",
                            "description": "URL of a previously covered story this updates. Omit if new.",
                        },
                    },
                },
            },
            "talking_points": {
                "type": "array",
                "minItems": 3,
                "maxItems": 3,
                "description": "Exactly 3 key talking points for the user, ranked by importance",
                "items": {
                    "type": "object",
                    "required": ["headline", "context", "supporting_article_urls"],
                    "properties": {
                        "headline": {
                            "type": "string",
                            "description": "Sharp, executive-level headline (max 120 chars)",
                        },
                        "context": {
                            "type": "string",
                            "description": (
                                "2–3 sentence explanation of why this matters specifically to the user's role. "
                                "Wrap person names in **double asterisks** with their title. "
                                "Be direct and actionable — what should the user think or do about this?"
                            ),
                        },
                        "supporting_article_urls": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "1–3 article URLs that back this talking point",
                        },
                        "is_update": {
                            "type": "boolean",
                            "description": "True if this updates a previously reported talking point",
                        },
                        "update_context": {
                            "type": "string",
                            "description": "If is_update=true, briefly note what has materially changed",
                        },
                    },
                },
            },
        },
    },
}


@dataclass
class ScoredArticle:
    article_url: str
    hsbc_relevancy: int
    user_relevance: int
    noise_level: int
    category: str
    summary: str
    key_entities: List[str] = field(default_factory=list)
    is_update_of: Optional[str] = None


@dataclass
class TalkingPoint:
    headline: str
    context: str
    supporting_article_urls: List[str]
    is_update: bool = False
    update_context: str = ""


@dataclass
class AnalysisResult:
    scored_articles: List[ScoredArticle]
    talking_points: List[TalkingPoint]


class BriefingAnalyzer:
    def __init__(self):
        self.client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

    def analyze_articles(
        self,
        articles: List[Article],
        user: UserProfile,
        previous_context: dict,
    ) -> AnalysisResult:
        if not articles:
            logger.warning("No articles to analyze")
            return AnalysisResult(scored_articles=[], talking_points=[])

        articles_payload = self._format_articles(articles)
        prev_urls = previous_context.get("covered_urls", [])
        prev_topics = previous_context.get("covered_topics", [])

        user_block = (
            f"**User:** {user.name}\n"
            f"**Title:** {user.title}\n"
            f"**Key interests:** {', '.join(user.interests)}\n"
            f"**Banks of focus:** {', '.join(user.banks_of_interest)}"
        )

        context_block = ""
        if prev_urls or prev_topics:
            context_block = (
                "\n\n**Previously covered (avoid repeating unless material update):**\n"
                f"URLs: {json.dumps(prev_urls[:40])}\n"
                f"Topics: {json.dumps(prev_topics[:15])}"
            )

        user_message = (
            f"{user_block}{context_block}\n\n"
            f"**Today's articles to analyse ({len(articles)} total):**\n\n"
            f"{articles_payload}"
        )

        try:
            response = self.client.messages.create(
                model="claude-sonnet-4-6",
                max_tokens=8192,
                system=[
                    {
                        "type": "text",
                        "text": ANALYSIS_SYSTEM_PROMPT,
                        "cache_control": {"type": "ephemeral"},
                    }
                ],
                tools=[ANALYSIS_TOOL],
                tool_choice={"type": "tool", "name": "submit_briefing_analysis"},
                messages=[{"role": "user", "content": user_message}],
            )
        except anthropic.APIError as e:
            logger.error(f"Claude API error during analysis: {e}")
            raise

        return self._parse_response(response)

    def _format_articles(self, articles: List[Article]) -> str:
        lines = []
        for i, a in enumerate(articles, 1):
            content_preview = (a.content or a.description or "")[:500]
            lines.append(
                f"[{i}] URL: {a.url}\n"
                f"    Title: {a.title}\n"
                f"    Source: {a.source} | Published: {a.published_at[:10] if a.published_at else 'unknown'}\n"
                f"    Content: {content_preview}\n"
            )
        return "\n".join(lines)

    def _parse_response(self, response) -> AnalysisResult:
        tool_use_block = next(
            (b for b in response.content if b.type == "tool_use"), None
        )
        if not tool_use_block:
            logger.error("No tool_use block in Claude response")
            return AnalysisResult(scored_articles=[], talking_points=[])

        data = tool_use_block.input

        scored = [
            ScoredArticle(
                article_url=a["article_url"],
                hsbc_relevancy=a["hsbc_relevancy"],
                user_relevance=a["user_relevance"],
                noise_level=a["noise_level"],
                category=a["category"],
                summary=a["summary"],
                key_entities=a.get("key_entities", []),
                is_update_of=a.get("is_update_of"),
            )
            for a in data.get("scored_articles", [])
        ]

        talking_points = [
            TalkingPoint(
                headline=tp["headline"],
                context=tp["context"],
                supporting_article_urls=tp.get("supporting_article_urls", []),
                is_update=tp.get("is_update", False),
                update_context=tp.get("update_context", ""),
            )
            for tp in data.get("talking_points", [])
        ]

        return AnalysisResult(scored_articles=scored, talking_points=talking_points)
