# WPB Daily Market Intelligence Briefing — Claude Code Routine

## Routine Prompt

Run the daily WPB Market Intelligence Briefing for Adam Chow and Sirali Siriwardene.

Steps:
1. Navigate to the repository root
2. Install dependencies if not already installed: `pip install -r requirements.txt`
3. Run the briefing generator: `python src/main.py`
4. Stage and commit the generated HTML files under `docs/`: `git add docs/ && git commit -m "briefing: $(date +%Y-%m-%d) daily intelligence update"`
5. Push the commit to trigger GitHub Pages deployment: `git push`
6. If any step errors, investigate the logs, fix the issue, and retry once before reporting failure

## Schedule

Daily at 07:00 HKT (Hong Kong Time, UTC+8) = 23:00 UTC

## Required Environment Variables

Configure these in your Claude Code Routine cloud environment:

| Variable | Purpose |
|---|---|
| `ANTHROPIC_API_KEY` | Claude API for article analysis |
| `NEWS_API_KEY` | NewsAPI.org for article fetching |
| `NOTION_TOKEN` | Notion integration token |
| `NOTION_DATABASE_ID` | Target Notion database ID |
| `GCS_BUCKET_NAME` | (Optional) Google Cloud Storage bucket for HTML mirror |

## Public URLs (GitHub Pages)

After first push, GitHub Pages will serve:
- Adam: `https://atomicchowder.github.io/WPB_Briefings/adam/`
- Sirali: `https://atomicchowder.github.io/WPB_Briefings/sirali/`

## Routine Setup (Claude Code UI)

1. Open Claude Code → Routines → New Routine
2. Name: `WPB Daily Briefing`
3. Paste the prompt above
4. Repository: `AtomicChowder/WPB_Briefings` (branch: `main`)
5. Schedule: Daily, custom cron `0 23 * * *` (= 07:00 HKT)
6. Add environment variables listed above
7. Create
