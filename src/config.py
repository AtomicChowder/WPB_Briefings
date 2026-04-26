from dataclasses import dataclass, field
from typing import List


@dataclass
class UserProfile:
    id: str
    name: str
    display_name: str
    title: str
    organization: str
    interests: List[str]
    banks_of_interest: List[str]
    search_keywords: List[str]
    url_slug: str
    notion_database_id: str = ""


USERS = {
    "adam": UserProfile(
        id="adam",
        name="Adam Chow",
        display_name="Adam",
        title="Head of Change Execution, WPB Private Banking & Wealth Solutions, Asia Pacific",
        organization="HSBC",
        interests=[
            "AI in banking and financial services",
            "Private banking and wealth management Asia Pacific",
            "Change execution and agile delivery",
            "Digital transformation in banking",
            "Banking technology and fintech",
            "Competitor intelligence for HSBC",
            "New AI models, tools, and platforms",
            "AI-powered wealth advisory",
        ],
        banks_of_interest=[
            "HSBC", "DBS", "Standard Chartered", "Citibank", "Hang Seng Bank",
            "HASE", "PayMe", "UBS", "JP Morgan", "Bank of America",
            "Deutsche Bank", "Bank of China",
        ],
        search_keywords=[
            "HSBC WPB wealth management Asia Pacific",
            "private banking AI Hong Kong Singapore",
            "DBS Standard Chartered digital wealth",
            "wealth management fintech innovation",
            "banking AI transformation change management",
            "agile delivery financial services",
            "JP Morgan UBS private banking technology",
            "PayMe HASE Hong Kong digital banking",
            "Citibank Deutsche Bank wealth Asia",
            "AI large language models banking finance",
        ],
        url_slug="adam",
    ),
    "sirali": UserProfile(
        id="sirali",
        name="Sirali Siriwardene",
        display_name="Sirali",
        title="COO & Global Head of Change Execution, WPS",
        organization="HSBC",
        interests=[
            "WPS COO strategy and operations",
            "Global change execution and governance",
            "Business management and cost efficiency",
            "AI in banking and financial services",
            "Private banking and wealth management",
            "Regulatory compliance and risk management",
            "Operational resilience and transformation",
            "Banking technology infrastructure",
        ],
        banks_of_interest=[
            "HSBC", "DBS", "Standard Chartered", "Citibank", "Hang Seng Bank",
            "HASE", "PayMe", "UBS", "JP Morgan", "Bank of America",
            "Deutsche Bank", "Bank of China",
        ],
        search_keywords=[
            "HSBC WPS operations strategy global",
            "wealth management COO operational efficiency",
            "global banking change execution governance",
            "private banking regulatory compliance",
            "banking operations AI automation cost",
            "wealth management competitor strategy",
            "financial services business management",
            "HSBC competitor analysis Asia Pacific",
        ],
        url_slug="sirali",
    ),
}

CATEGORIES = [
    "AI & Technology",
    "HSBC News",
    "Competitor Intelligence",
    "Private Banking & Wealth",
    "Regulatory & Markets",
    "Operations & Change",
]

CATEGORY_COLORS = {
    "AI & Technology": "#6366f1",
    "HSBC News": "#dc2626",
    "Competitor Intelligence": "#0891b2",
    "Private Banking & Wealth": "#059669",
    "Regulatory & Markets": "#d97706",
    "Operations & Change": "#7c3aed",
}

RSS_FEEDS = [
    "https://feeds.bloomberg.com/markets/news.rss",
    "https://feeds.reuters.com/reuters/businessNews",
    "https://www.ft.com/?format=rss",
]

MAX_ARTICLES_PER_CATEGORY = 5
ARTICLES_PER_FETCH = 40
BRIEFING_HISTORY_DAYS = 30
MIN_ARTICLE_SCORE = int(__import__("os").getenv("MIN_ARTICLE_SCORE", "6"))
