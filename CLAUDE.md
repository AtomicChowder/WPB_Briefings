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

## Domain Notes (institutional context — use when writing analysis)

Facts about HSBC's own stack that competitor stories must be framed against:

- **HSBC has used BlackRock's Aladdin for 6+ years.** The **PRISM advisory service**
  is built on Aladdin. A competitor adopting Aladdin/Aladdin Wealth is *catching up*
  to capability HSBC already runs at scale — never frame it as HSBC being behind.
- **Wealth Intelligence** (launched Sept 2025) is HSBC's **staff-facing GenAI
  research/insights ecosystem** (OpenAI-powered summarisation of CIO research and
  news for RMs/investment counsellors). It is NOT a portfolio-analytics platform and
  is not the head-to-head surface against Aladdin-type tools — don't compare them.
- When a competitor adopts a vendor HSBC also uses, the analytical angles are:
  convergence on the same stack (differentiation shifts to advisory workflow,
  adoption and delivery pace) and vendor concentration risk — not "buy vs build".

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

## Freshness & Context Rules (CRITICAL — read before selecting any article)

This is a **daily** intelligence product. Stale content destroys its credibility.

1. **48-hour window.** Only include articles published within 48 hours of the briefing
   date. The pipeline (`src/build_briefing.py`) enforces this and silently drops
   anything older — do not try to route around it.
2. **Updates are the only exception.** An older story may appear only with
   `is_update: true`, and only when there is a genuinely NEW development. Its summary
   must open with the new fact and explicitly anchor to the prior coverage
   (e.g. "Following the Citi Sky launch we covered in April, Citi today announced…").
3. **Never pad.** If fresh news is thin, publish a lean briefing. Six genuinely new
   articles beat eighteen recycled ones. An empty category is fine.
4. **Check history first.** Cross-reference every candidate against
   `context/history.json` (`covered_urls` and `covered_topics`) before scoring.
5. **Analysis, not aggregation.** Every article summary follows three beats:
   (a) the new fact, (b) context — how it connects to prior coverage or the
   competitive landscape, (c) why it matters to Adam — through the change-execution /
   AI / private banking & wealth / COO lens. Talking points must answer
   "so what for Adam?" explicitly in `context_html`.

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
| **On Adam's Desk** | Thread hits, routed by the builder, emitted first, relaxed gate. Never assign this category yourself — `src/build_briefing.py` moves any article with `thread_rel >= 5` here |

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

Do NOT hand-write this file. Write a `briefing_input.json` (see
`briefing_input.example.json`) and run `python src/build_briefing.py <input>` — it
applies the freshness gate, the history dedup gate, score filtering, category caps,
and sorting deterministically, then writes `docs/adam/briefing_data.json` in the
schema below.

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
- `articles_by_category`: max **3 articles per category** (enforced by the pipeline), only include categories with articles
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

---

## Internal Context Lens (MANDATORY since 2026-09-13 — read before Step 1 of the Routine)

Adam's meeting pipeline (Plaud → Whisper → Notion, local) writes ONE Notion page every morning
at ~05:15 HKT: **"MI Context — current"**, page id `3da6f349-23b7-810c-aa64-f291d14948c0`.
It lists, as labelled plain-text lines inside a code block: `workstream:` / `thread:` labels,
`entity:` lines (canonical name | category | count | expansion), `decision:`, `open:`,
`upcoming:` lines from the last 14 days of minutes, and `canonical:` spellings.

This page is a SECOND LENS. It never narrows the scan. Adam, 2026-09-13: "i still need to see
outside world contextual information that might change the macro environment i operate in" —
AND the context of his current top challenges. Both, kept apart.

### 1. Read it (between Routine steps 1 and 2)

`notion-fetch` the page. Parse the `generated:` line. If the page is unreachable, or `generated`
is more than 3 days before today, run in **macro-only mode**: skip §2 and §4 below, and write
`Context lens: unavailable (<reason>)` in the Notion callout (§5). Never fail the briefing over it.

### 2. Expand the search (Routine step 2)

Run EVERY standing query above. THEN run EVERY `query:` line in SECTION 8 of the context page.

Do not select, rank or trim them, and do not build your own queries from the page. Section 8 is
already ranked, it is rebuilt every run from the rolling window of Adam's minutes, and it changes
daily. The previous rule here — "up to 8 queries built from the page's `entity:` lines, highest
count first" — put internal acronyms (SVS, Capability, WPS, WTP, MSII) at the head of the list.
They return nothing outside HSBC and the targeted scan fell to zero thread-linked items over
13–16 September.

Never search decision text, figures, open-question text or people. Section 8's queries are already
safe by construction: each is a canonical lexicon name or a geography label plus a fixed tail.

The 48-hour window and the history dedup apply unchanged.

### 3. Score the lens (Routine step 4)

For every surviving article assign, IN ADDITION to `hsbc_relevancy` / `adam_rel` / `noise_level`:
- `thread_rel` (0–10): how directly it bears on a live thread — 0–2 none; 5–6 touches an
  `entity:` or `thread:` in play; 8–10 bears on a `decision:` or `open:` line directly.
- `threads`: the matching `thread:` / `workstream:` label(s) from section 1 of the page, or
  `macro` when none applies. Labels ONLY — never a decision or open-question text.

**`thread_rel` and `threads` must never appear in `docs/` or `briefing_data.json`** — those are
committed to a PUBLIC GitHub Pages repo and internal thread labels never go there. That rule is
now enforced in code: `src/build_briefing.py` strips both fields from everything it writes. The
public page is unchanged by this lens.

### Thread hits are gated separately (added 2026-09-17)

The combined-score gate and the category caps judge "is this about HSBC or a major competitor".
That is the wrong test for an article found by a section-8 query — an Avaloq or eCRM story is not
about HSBC, scores 2–3 on `hsbc_relevancy`, and was being dropped before the lens ever saw it.
So, for articles with `thread_rel >= 5` ONLY:

Write `thread_rel` (0-10) and `threads` onto each article in /tmp/briefing_input.json. That file
is NEVER committed - only docs/ and docs/adam/briefing_data.json are public, and the builder
strips both fields from everything it writes.

Do NOT invent or assign a category for thread hits. Keep giving every article its normal
category. src/build_briefing.py owns the routing, the relaxed gate, the cap and the ordering -
it moves any article with thread_rel >= 5 into "On Adam's Desk" itself. Emitting that category
name from here crashes the build on the unknown-category check.

Macro items are unaffected: the >= 6 gate and the 3-per-category cap still apply to them, and a
macro item is never dropped for lacking an internal thread.

If no article reaches `thread_rel >= 5`, emit no "On Adam's Desk" category and say so in the
talking-point note, exactly as now.

### 4. Pick the talking points (Routine step 5) — the 2 + 1 split

- Two talking points = the two most strategically significant items whose `threads` is
  `macro` (environment change), chosen exactly as before.
- One talking point = the item with the highest `thread_rel` (≥ 5) — the one that lands on
  Adam's desk this week. If no item reaches 5, publish three macro points and say so in §5.
- An item that is both (a regulator moves on something Adam has a live decision on) is tagged
  with its thread AND counts as the thread pick; the callout says it is both.
- `context_html` on the public page stays purely external — no thread label, no internal text.

### 5. Annotate the Notion page ONLY (Routine step 8)

On the Notion briefing page (private) and nowhere else:
- Under the red callout add one line: `Context lens: <generated timestamp from the page> ·
  <N> thread-linked · <N> macro · mode: lens|macro-only`.
- Under each Key Talking Point paragraph add a line `Internal thread: <label>` — or
  `Internal thread: macro`. Optionally one clause on how it touches the thread, using the LABEL
  only, never the decision text.
- In the Intelligence Feed, extend each score bracket: `[HSBC 7/10 · Rel 9/10 · Thread avaloq-credit]`
  or `[HSBC 7/10 · Rel 9/10 · macro]`.
- Set the page properties `Briefing Date` and `Date Published` to today's date (ISO), so the
  database views and the downstream jobs (daily email 07:00 HKT, Sunday weekly) can find it.

The daily email and the Sunday weekly read these annotations; the GitHub page is never read by
them. Nothing from the "MI Context — current" page is ever quoted, paraphrased or linked in
`docs/`, `briefing_input.json`, `history.json` or a commit message.
