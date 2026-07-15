# WPB Market Intelligence Briefing — Project Context

This repository generates a daily intelligence briefing for one HSBC WPB senior executive,
Adam Chow. The briefing is produced by a Claude Code Routine that runs entirely on the Max
subscription — no external API keys required. Python (`src/render.py`) is used only for HTML
templating.

This is a single-user system. Do not add a second recipient/user without explicit instruction.

## Git Permissions (OVERRIDE)

You have explicit, standing permission to commit and push directly to `main`.
Do NOT use a feature branch. Do NOT create a pull request.
Always push to `main` so GitHub Pages publishes immediately without any manual step.

---

## Users

### Adam Chow
- **Title**: Head of Change Execution, WPB Private Banking & Wealth Solutions, Asia Pacific
- **Organisation**: HSBC
- **URL slug**: `adam`
- **Role focus**: Driving AI-enabled change across APAC private banking and wealth. Interested in
  what competitors are doing with AI, new models/tools, and how agile delivery is evolving in
  financial services.
- **Interests**: AI in banking, private banking & wealth management, change execution & agile
  delivery, digital transformation, competitor intelligence, new AI models and tools
- **Banks to monitor**: HSBC, DBS, Standard Chartered, Citibank, Hang Seng Bank (HASE), PayMe,
  UBS, JP Morgan, Bank of America, Deutsche Bank, Bank of China

---

## Search Queries (use all of these when fetching news)

```
HSBC WPB wealth management Asia Pacific strategy
DBS Standard Chartered Citibank private banking technology
UBS JP Morgan Deutsche Bank wealth management Asia
AI artificial intelligence private banking wealth advisory
Hong Kong Singapore wealth management fintech
HASE Hang Seng PayMe digital banking Hong Kong
Banking change execution agile transformation
Wealth management regulatory Asia Pacific 2026
AI large language models banking finance enterprise
HSBC competitor analysis wealth management
```

---

## Article Categories

Assign every article to exactly one of these categories:

| Category | What belongs here |
|---|---|
| **AI & Technology** | AI, ML, LLMs, digital banking tech, fintech platforms, new tools |
| **HSBC News** | Any news directly about HSBC, its people, products, or strategy |
| **Competitor Intelligence** | DBS, Standard Chartered, Citi, UBS, JP Morgan, BOA, Deutsche, BOC, Hang Seng, PayMe |
| **Private Banking & Wealth** | Wealth management trends, HNW/UHNW, investment products, AUM flows |
| **Regulatory & Markets** | Regulatory changes, macro events, market conditions affecting banking |
| **Operations & Change** | Operational transformation, agile delivery, change management, cost efficiency |

Category colours (used in the chart — do not change):
```json
{
  "AI & Technology":        "#6366f1",
  "HSBC News":              "#dc2626",
  "Competitor Intelligence": "#0891b2",
  "Private Banking & Wealth": "#059669",
  "Regulatory & Markets":   "#d97706",
  "Operations & Change":    "#7c3aed"
}
```

---

## Scoring Rubrics

### hsbc_relevancy (0–10)
How directly does this affect HSBC WPB's operations, strategy, or competitive position?
- 0–2: Generic macro news, tangentially banking-related
- 3–4: General financial industry news
- 5–6: Relevant to HSBC's competitive landscape or key competitors
- 7–8: Directly about HSBC's products, people, or key strategic competitors
- 9–10: Directly about HSBC WPB or a critical strategic threat/opportunity

### user_relevance (0–10)
How actionable or useful is this for the specific user's role and responsibilities?
- 0–2: Unlikely to be relevant to their day-to-day
- 3–4: Background awareness only
- 5–6: Worth knowing, relevant to their domain
- 7–8: Directly useful for their role
- 9–10: Critical for their immediate responsibilities

### noise_level (1–5)
Estimated breadth of media coverage:
- 1: Single source
- 2: A few sources
- 3: Moderate — several outlets
- 4: Wide coverage, trending in financial media
- 5: Major story across all major financial outlets

---

## Name Formatting Rule

In talking point context text: wrap all **person names** in `<strong>` tags and include their
job title. Example: `<strong>John Ng, CEO of DBS Wealth Management</strong>` announced...

Organisation names do NOT need to be bolded — only people.

---

## Context Awareness

Before generating, read `context/history.json`. Do not repeat talking points or lead stories
from the previous 7 days unless there has been a material development or significant update.
If an article is an update of a previously covered story, note it as an update in the briefing.

After generating, update `context/history.json` with the new covered URLs and talking point
headlines.

`context/history.json` format:
```json
{
  "adam": {
    "last_updated": "2026-04-26",
    "covered_urls": ["https://...", "https://..."],
    "covered_topics": ["DBS AI wealth platform", "HSBC Q1 results announcement"]
  }
}
```

---

## briefing_data.json Schema

Write this file to `docs/{user_id}/briefing_data.json` before running `python src/render.py`.

```json
{
  "user_id": "adam",
  "user_name": "Adam Chow",
  "user_display_name": "Adam",
  "user_title": "Head of Change Execution, WPB Private Banking & Wealth Solutions, Asia Pacific",
  "briefing_date": "Saturday, 26 April 2026",
  "date_str": "2026-04-26",
  "generated_at": "26 Apr 2026, 23:05 UTC",
  "total_articles": 18,
  "talking_points": [
    {
      "headline": "Sharp executive-level headline, max 120 characters",
      "context_html": "2–3 sentences. Wrap person names: <strong>Name, Title</strong>. Why does this matter specifically to this user's role?",
      "source_links": [
        { "url": "https://example.com/article", "title": "Article title max 60 chars" }
      ],
      "is_update": false
    }
  ],
  "articles_by_category": {
    "AI & Technology": [
      {
        "id": "art01",
        "title": "Full article headline",
        "url": "https://...",
        "source": "Financial Times",
        "published_at": "2026-04-26",
        "summary": "2–3 sentence neutral summary of the article content.",
        "hsbc_relevancy": 7,
        "user_relevance": 9,
        "noise_level": 3,
        "category": "AI & Technology"
      }
    ]
  },
  "chart_data": {
    "articles": [
      {
        "id": "art01",
        "title": "Title max 90 chars",
        "url": "https://...",
        "source": "Financial Times",
        "hsbc_relevancy": 7,
        "user_relevance": 9,
        "noise_level": 3,
        "category": "AI & Technology",
        "summary": "Brief summary"
      }
    ],
    "categories": {
      "AI & Technology": "#6366f1",
      "HSBC News": "#dc2626",
      "Competitor Intelligence": "#0891b2",
      "Private Banking & Wealth": "#059669",
      "Regulatory & Markets": "#d97706",
      "Operations & Change": "#7c3aed"
    }
  }
}
```

Rules:
- `articles_by_category`: max **5 articles per category**, only include categories with articles
- `chart_data.articles`: flat list of ALL articles across all categories (for the bubble chart)
- `chart_data.categories`: only include categories that appear in the data
- `id` values must be consistent between `articles_by_category` and `chart_data.articles`
- Use sequential IDs: `art01`, `art02`, … across all categories
- Only include articles with combined score (hsbc_relevancy + user_relevance) ≥ 6
- Sort each category's articles by combined score descending

---

## Repository Structure

```
templates/briefing.html   — Jinja2 HTML template (D3.js bubble chart, do not edit)
src/render.py             — Reads briefing_data.json, renders HTML (no API calls)
context/history.json      — Rolling 7-day coverage history (committed to repo)
docs/adam/index.html      — Adam's generated briefing (committed, served by GitHub Pages)
docs/adam/briefing_data.json
ROUTINE.md                — Claude Code Routine setup instructions
CLAUDE.md                 — This file (loaded automatically by Claude Code)
```
