# WPB Daily Briefing — Claude Code Routine

## Routine Prompt

> Read CLAUDE.md first — it contains the user profile, scoring rubrics, the JSON schema,
> and context awareness instructions.

Run the daily WPB Market Intelligence Briefing for **Adam Chow** only. This is a single-user
system — do not create or publish a briefing for anyone else.

**CRITICAL — output directory. Use this exactly. Never infer a path from
what files already exist in the repo — always use the path below, verbatim:**
- Adam → `docs/adam/`

**1. Check history**
Read `context/history.json`. Note the URLs and topics covered in the last 7 days so you
don't repeat them unless there's a material update.

**2. Search for news**
Use your web search tool to run each of the search queries listed in CLAUDE.md. Collect
all articles published in the last 48 hours. Aim for 20–40 articles across all queries.

**3. Score and categorise**
For each article, assign:
- `hsbc_relevancy` (0–10) — per the rubric in CLAUDE.md
- `user_relevance` (0–10) — based on Adam's role and interests
- `noise_level` (1–5) — breadth of coverage
- `category` — one of the 6 categories in CLAUDE.md

Discard articles with combined score (hsbc + relevance) below 6.
Keep a maximum of 5 articles per category, sorted by combined score descending.

**4. Write 3 talking points**
Select the 3 most strategically significant stories. Each talking point needs:
- A sharp headline (max 120 chars)
- 2–3 sentences of context explaining why it matters *specifically* to Adam's role
- Wrap person names in `<strong>Name, Title</strong>` HTML tags
- 1–3 supporting article URLs

Do not repeat talking points covered in the last 7 days unless there's a material update.

**5. Write `docs/adam/briefing_data.json`**
Write the complete JSON file following the exact schema in CLAUDE.md.
Include `briefing_date` as a formatted string (e.g. "Saturday, 26 April 2026").
Include `generated_at` as UTC time.

**6. Render HTML and archive**
```bash
pip install -r requirements.txt -q
python src/render.py adam
```
This reads the JSON and writes `docs/adam/index.html`.

Also copy today's rendered page as a dated archive file and update the nav index:
```bash
cp docs/adam/index.html docs/adam/{date_str}.html
python3 -c "
import os, json
files = sorted(f.replace('.html','') for f in os.listdir('docs/adam')
               if f.endswith('.html') and f != 'index.html' and len(f) == 15)
open('docs/adam/nav.json','w').write(json.dumps(files, indent=2))
"
```

**7. Publish to Notion**
Using the Notion MCP connector, create a new page in the database
**"WPB Weekly Intelligence Briefings"** with:
- Title: `[Adam] WPB Briefing — {date}` (e.g. `[Adam] WPB Briefing — 26 Apr 2026`)
- A red callout with Adam's name and title
- A divider
- Heading: "🎯 Key Talking Points" — then each talking point as Heading 3 + paragraph + bullet links
- A divider
- Heading: "📰 Intelligence Feed" — articles grouped by category as Heading 3 + bulleted links
  with scores: `[HSBC 7/10 · Rel 9/10] Article title` linked to article URL,
  followed by a grey paragraph for the summary
- Set the "Recipient" property to `Adam Chow`

**8. Update history**
Merge today's covered URLs and talking point headlines into `context/history.json`.
Keep only the last 7 days of data.

**9. Commit and push directly to `main`**
```bash
git add docs/ context/history.json
git commit -m "briefing: YYYY-MM-DD daily intelligence update"
git push origin main
```
No pull request or branch review is needed — push straight to `main`.

**10. QA check — verify the page is live**
Wait up to 3 minutes for GitHub Pages to deploy, then confirm the URL returns HTTP 200:
```bash
for i in $(seq 1 18); do
  code=$(curl -s -o /dev/null -w "%{http_code}" \
    "https://atomicchowder.github.io/WPB_Briefings/adam/")
  if [ "$code" = "200" ]; then
    echo "✓ adam briefing live (200)"
    break
  fi
  [ $i -eq 18 ] && echo "✗ adam still returning ${code} after 3 min"
  sleep 10
done
```
If the URL does not return 200, send a PushNotification flagging the failure.

---

## Schedule

`0 23 * * *` (UTC) = **07:00 HKT** daily

---

## Connectors Required

- **Notion** — add your existing Notion connector in Routine settings

## Environment Variables

None required. Everything runs on your Max subscription.

---

## Public URLs

Enable GitHub Pages on `main` branch, source: `/docs` folder.

- Adam → `https://atomicchowder.github.io/WPB_Briefings/adam/`

---

## Routine Setup (Claude Code UI)

1. Claude Code → Routines → **New Routine**
2. **Name**: `WPB Daily Briefing`
3. **Prompt**: paste everything in the "Routine Prompt" section above
4. **Repository**: `AtomicChowder/WPB_Briefings` (branch: `main`)
5. **Schedule**: custom cron `0 23 * * *`
6. **Connectors**: add your Notion connector
7. No environment variables needed
8. **Create** → **Run now** to generate the first briefing
