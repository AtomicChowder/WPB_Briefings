# WPB Daily Briefing — Claude Code Routine

## Routine Prompt

> Read CLAUDE.md first — it contains the user profile, scoring rubrics, the JSON schema,
> and context awareness instructions.

Run the daily WPB Market Intelligence Briefing for **Adam Chow** only. This is a single-user
system — do not create or publish a briefing for anyone else.

**PURPOSE:** surface genuinely NEW news (last 48 hours) at the intersection of HSBC,
AI, business transformation, private banking & wealth, and the COO agenda — placed in
context of what we've previously reported, with analysis on why each item matters to
Adam. Never republish old stories as if they were news. Read the "Freshness & Context
Rules" section of CLAUDE.md before selecting anything.

**CRITICAL — output directory. Use this exactly. Never infer a path from
what files already exist in the repo — always use the path below, verbatim:**
- Adam → `docs/adam/`

**0. Sync**
```bash
bash bin/briefing-sync
```
Pulls live data (history + docs) from origin/main and installs dependencies.

**1. Check history**
Read `context/history.json`. Build a picture of the last 7 days of coverage — these
URLs and topics are the "already reported" baseline every candidate is judged against.

**2. Search for news — last 48 hours only**
Run each search query listed in CLAUDE.md. Keep only articles verifiably published
within the last 48 hours. It is normal for many queries to return nothing new — do
not reach back further to compensate.

**3. Triage every candidate**
- Published within 48h? If not, discard — unless it is a material NEW development of
  a story in history, in which case mark `is_update: true`.
- URL or topic already in history? Discard — unless there's a new development
  (`is_update: true`).

**4. Score and write analysis**
For each surviving article assign `hsbc_relevancy` (0–10), `adam_rel` (0–10),
`noise_level` (1–5), and `category`. Write the summary in three beats:
the new fact → context (link to prior coverage or competitive landscape) → why it
matters to Adam. For `is_update` articles, the summary must open by anchoring the
prior coverage ("Following X we covered on {date}, …").

**5. Write 3 talking points**
The 3 most strategically significant NEW stories. Each needs:
- A sharp headline (max 120 chars)
- `context_html`: 2–3 sentences of genuine analysis answering "so what for Adam?" —
  wrap person names in `<strong>Name, Title</strong>` tags
- 1–3 supporting source links

Do not repeat talking points from the last 7 days unless flagged as an update.

**6. Build via the pipeline (never hand-write briefing_data.json)**
Write the input file per `briefing_input.example.json`, then:
```bash
python src/build_briefing.py /tmp/briefing_input.json
python src/update_history.py /tmp/briefing_input.json
```
The build step enforces the 48h freshness gate, the history dedup gate, the combined
score ≥ 6 filter, and the 3-per-category cap. If it drops articles you expected,
that is the system working — do not bypass it.

**7. Render HTML and archive**
```bash
bash bin/briefing-render
```
Then archive today's page and refresh the nav index:
```bash
cp docs/adam/index.html docs/adam/{date_str}.html
python3 -c "
import os, json
files = sorted(f.replace('.html','') for f in os.listdir('docs/adam')
               if f.endswith('.html') and f != 'index.html' and len(f) == 15)
open('docs/adam/nav.json','w').write(json.dumps(files, indent=2))
"
```

**8. Publish to Notion**
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

**9. Commit and push directly to `main`**
```bash
bash bin/briefing-publish
```
This commits docs/ + history and pushes straight to `main` (no PR, no review).

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
