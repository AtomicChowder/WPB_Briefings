# WPB Market Intelligence Briefing — Project Context

This repository generates a daily intelligence briefing for two HSBC WPB senior executives.
The briefing is produced by a Claude Code Routine that runs entirely on the Max subscription —
no external API keys required. Python (`src/render.py`) is used only for HTML templating.

---

## Operational Lessons (durable, do not violate)

1. **Always run `bash bin/briefing-sync` first.** It pulls the live `context/history.json`
   and `docs/` from `origin/main` regardless of which branch the session was started on.
   Skipping this is the #1 cause of lost history and stale outputs.
2. **Always publish via `bash bin/briefing-publish`.** It commits and pushes to `origin/main`
   (with retries + auto-rebase). Never run `git push` directly to a feature branch.
   GitHub Pages deploys from `main` only.
3. **Use `src/build_briefing.py` to write the briefing JSON.** Never write
   `docs/{user}/briefing_data.json` directly with the Write/Edit tools. The script
   handles filtering, sorting, capping, and naming deterministically. Names ("Adam Chow",
   "Surali Siriwardene") are hardcoded in the script and cannot be overridden.
4. **Spelling: `Surali` (not Sirali)** — slug `surali`, history key `surali`,
   per-article scores `adam_rel` and `surali_rel`. Notion `Recipient` is `Surali Siriwardene`.
5. **Run all 10 search queries in parallel** in a single batch — never sequentially.
   Stream-idle timeouts are the second-most-common failure after sync skipping.
6. **Notion DB**: *WPB Weekly Intelligence Briefings* (data source
   `3336f349-23b7-8053-9230-000b278a9f1a`).

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

### Surali Siriwardene
- **Title**: COO & Global Head of Change Execution, WPS
- **Organisation**: HSBC
- **URL slug**: `surali`
- **Role focus**: Global COO strategy, operational efficiency, business management, and governing
  the worldwide change execution programme. Adam's direct manager.
- **Interests**: WPS COO strategy, global change execution governance, business management &
  cost efficiency, operational resilience, regulatory compliance, AI in banking, wealth management
- **Banks to monitor**: Same as Adam

---

## Search Queries (use ALL of these when fetching news — 12 total)

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
Anthropic OpenAI Google Gemini AI model release banking finance enterprise
DeepSeek Qwen Kimi Chinese AI model financial services Asia
```

> **Why 12?** Queries 1–10 cover markets, competitors, and macro. Queries 11–12
> were added after AI lab announcements (Anthropic finance agents, OpenAI GPT-5.4,
> Google Gemma 4, DeepSeek V4) were systematically missed. Always run all 12 in
> a single parallel batch.

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

## Article Freshness Rule

**Always**: only include articles **published or last updated within the prior 48 hours** of the
briefing date. Discard any article whose `published_at` is older than 48 hours, even if it scores
highly — it should have been caught in an earlier run. This applies on every run, including the
first.

If a known article has a **material update** (new data, regulatory decision, company announcement
that changes the story), it may be re-included and flagged as an update (`"is_update": true`).

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
  },
  "surali": {
    "last_updated": "2026-04-26",
    "covered_urls": [],
    "covered_topics": []
  }
}
```

---

## briefing_input.json Schema (what the LLM produces)

The routine writes a single small file `/tmp/briefing_input.json` and lets
`src/build_briefing.py` produce both per-user `briefing_data.json` files.

See `briefing_input.example.json` for a working schema reference. The structure is:

```json
{
  "date_str": "2026-05-01",
  "briefing_date": "Friday, 1 May 2026",
  "articles": [ {"id":"art01", "title":"...", "url":"...", "source":"...",
                 "published_at":"2026-05-01", "summary":"...",
                 "hsbc_relevancy":7, "adam_rel":9, "surali_rel":5,
                 "noise_level":3, "category":"AI & Technology",
                 "is_update":false} ],
  "users": {
    "adam":   {"talking_points": [...]},
    "surali": {"talking_points": [...]}
  },
  "breaking_news": {"adam": [], "surali": []}
}
```

`build_briefing.py` validates required fields, then applies two gates before the score filter:

**Gate 1 — Freshness**: articles with `published_at` older than 48 hours are dropped.
**Gate 2 — Deduplication**: articles whose URL already appears in `context/history.json`
`covered_urls` for that user are dropped.

Both gates are bypassed when `"is_update": true` is set on the article. Use this **only**
when re-introducing a previously covered story because a major new development warrants it.
When `is_update: true`, the `summary` field **must** explain what changed since prior coverage —
not repeat the original summary. After both gates, the score filter
(`hsbc_relevancy + {user}_rel ≥ 6`) is applied, articles are sorted by combined score, capped at 3
per category, and the full per-user `briefing_data.json` is written.

## briefing_data.json Schema (what the script writes — for reference only)

```json
{
  "user_id": "adam",
  "user_name": "Adam Chow",
  "user_display_name": "Adam",
  "user_title": "Head of Change Execution, WPB Private Banking & Wealth Solutions, Asia Pacific",
  "briefing_date": "Sunday, 26 April 2026",
  "date_str": "2026-04-26",
  "generated_at": "26 Apr 2026, 10:00 UTC",
  "total_articles": 12,
  "breaking_news": [],
  "talking_points": [
    {
      "headline": "Sharp executive-level headline, max 100 characters",
      "why_it_matters": "One sentence: why this is directly relevant to this user's specific role.",
      "bullets": [
        "Key fact or development — include <strong>Person Name, Title</strong> where relevant",
        "Second key point with implications",
        "Third point or call to action"
      ],
      "source_links": [
        { "url": "https://example.com/article", "title": "Source label max 55 chars" }
      ],
      "is_update": false
    }
  ],
  "articles_by_category": {
    "AI & Technology": [
      {
        "id": "art01",
        "title": "Full article headline (max 90 chars)",
        "url": "https://...",
        "source": "Financial Times",
        "published_at": "2026-04-26",
        "summary": "One sentence: why should this user care? What is the direct implication?",
        "hsbc_relevancy": 7,
        "adam_rel": 9,
        "surali_rel": 7,
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
        "adam_rel": 9,
        "surali_rel": 7,
        "user_relevance": 9,
        "noise_level": 3,
        "category": "AI & Technology",
        "summary": "One sentence summary"
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
- `breaking_news`: list only if there is a truly urgent HSBC story (AI strategy shift, major regulatory action, CEO announcement). Otherwise set to `[]`.
- `articles_by_category`: max **3 articles per category**, only include categories with articles
- `chart_data.articles`: flat list of ALL articles across all categories (for the bubble chart)
- `chart_data.categories`: only include categories that appear in the data
- `id` values must be consistent between `articles_by_category` and `chart_data.articles`
- Use sequential IDs: `art01`, `art02`, … across all categories
- Only include articles with combined score (hsbc_relevancy + user_relevance) ≥ 6
- Sort each category's articles by combined score descending
- `summary` field: one concise sentence framed as "why should I care" — not a neutral description

---

## Repository Structure

```
bin/briefing-sync         — Pulls history.json + docs/ from origin/main (run first)
bin/briefing-render       — Renders both users' HTML pages
bin/briefing-publish      — Commits + pushes to origin/main with retry/rebase
src/build_briefing.py     — /tmp/briefing_input.json → both docs/{user}/briefing_data.json
src/update_history.py     — Merges today's URLs/topics into history.json (7-day window)
src/render.py             — Reads briefing_data.json, renders HTML
templates/briefing.html   — Jinja2 HTML template (do not edit)
context/history.json      — 7-day rolling coverage history (committed to main)
docs/adam/                — Adam's published briefing (GitHub Pages from main)
docs/surali/              — Surali's published briefing (GitHub Pages from main)
briefing_input.example.json — Schema reference for /tmp/briefing_input.json
ROUTINE.md                — Routine prompt and setup
CLAUDE.md                 — This file
```

## Publishing

Always use `bash bin/briefing-publish`. It commits `docs/`, `context/history.json`, and
any code changes, then pushes to `origin/main` with retries and auto-rebase. GitHub Pages
deploys automatically from `main` on every push touching `docs/**`.

Optional GCS mirror (only if `GCS_BUCKET_NAME` is set):
```bash
gsutil -m rsync -r -d docs/ gs://${GCS_BUCKET_NAME}/
gsutil -m setmeta -h "Cache-Control:no-cache, max-age=0" \
  "gs://${GCS_BUCKET_NAME}/adam/index.html" \
  "gs://${GCS_BUCKET_NAME}/surali/index.html"
```

Required env vars: `GCS_BUCKET_NAME`, `GOOGLE_CLOUD_PROJECT`.
The `gcloud` CLI must be installed and authenticated before running.
