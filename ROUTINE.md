# WPB Daily Market Intelligence Briefing — Claude Code Routine

## Routine Prompt

Run the daily WPB Market Intelligence Briefing for **Adam Chow** and **Sirali Siriwardene**.

### Steps

1. Navigate to the repository root
2. Install dependencies: `pip install -r requirements.txt -q`
3. Run the briefing generator for both users:
   ```
   python src/main.py
   ```
   This fetches news via parallel web searches, analyses everything with Claude, generates HTML briefings, and writes `docs/adam/index.html`, `docs/adam/briefing_data.json`, `docs/sirali/index.html`, and `docs/sirali/briefing_data.json`.

4. **Publish to Notion using the Notion connector** — for each user (adam, sirali):
   - Read `docs/{user}/briefing_data.json`
   - In the Notion database **"WPB Weekly Intelligence Briefings"**, create a new page with:
     - **Title**: `[{user_name}] WPB Briefing — {date}` (e.g. `[Adam] WPB Briefing — 26 April 2026`)
     - **User** property: the user's name
     - **Date** property: today's date
   - Add these content blocks to the page:
     - A red callout: `Daily intelligence briefing for {user_name} · {user_title}`
     - A divider
     - Heading "🎯 Key Talking Points"
     - For each of the 3 talking points:
       - Heading 3 with the headline (bold any person names mentioned)
       - Paragraph with the context text
       - Bulleted links to supporting articles
     - A divider
     - Heading "📰 Intelligence Feed"
     - For each article, grouped by category:
       - Category as Heading 3
       - Bulleted list item: `[HSBC {score}/10 · Rel {score}/10] Article title` linked to the article URL
       - Grey paragraph with the summary

5. Commit the generated files and push:
   ```
   git add docs/
   git commit -m "briefing: $(date +%Y-%m-%d) daily intelligence update"
   git push
   ```
   This triggers GitHub Pages to deploy the updated briefings.

6. If any step errors, check the logs, fix the issue, and retry that step once before reporting.

---

## Schedule

Daily at **07:00 HKT** (Hong Kong Time, UTC+8) = `0 23 * * *` (UTC cron)

---

## Environment Variables

| Variable | Purpose | Required? |
|---|---|---|
| `ANTHROPIC_API_KEY` | Used by the Python subprocess for web search (Haiku) + analysis (Sonnet) | **Yes** |
| `GCS_BUCKET_NAME` | GCS bucket for HTML mirror | Optional |

> **Why is ANTHROPIC_API_KEY needed if I'm a Max subscriber?**
> The Routine itself (Claude thinking, tool calls, Notion MCP) runs on your Max subscription with no key needed.
> However, `python src/main.py` is a subprocess that calls the Anthropic SDK directly — that needs its own key.
> Get yours at [console.anthropic.com](https://console.anthropic.com) → API Keys.
> Cost per daily run is very low: ~6 Haiku web search calls + 2 Sonnet analysis calls ≈ $0.05–0.20/day.

> **Notion** is handled via the Notion MCP connector — no NOTION_TOKEN needed in env vars.
> **News** is fetched via Anthropic's web search tool (Haiku agents) — no NEWS_API_KEY needed.

---

## Connectors Required

- **Notion** — add your existing Notion connector to this routine in the Routine settings

---

## Public URLs (GitHub Pages)

Enable GitHub Pages on the `main` branch with `/docs` as the source folder:

- Adam: `https://atomicchowder.github.io/wpb_briefings/adam/`
- Sirali: `https://atomicchowder.github.io/wpb_briefings/sirali/`

---

## Routine Setup (Claude Code UI)

1. Claude Code → Routines → **New Routine**
2. **Name**: `WPB Daily Briefing`
3. **Prompt**: paste the Steps section above
4. **Repository**: `AtomicChowder/WPB_Briefings` (branch: `main`)
5. **Schedule**: Daily, custom cron `0 23 * * *`
6. **Connectors**: add your Notion connector
7. **Environment variables**: set `ANTHROPIC_API_KEY`
8. **Create**
