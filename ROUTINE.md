# WPB Daily Briefing — Claude Code Routine

## Routine Prompt

> Read CLAUDE.md first — it contains all user profiles, scoring rubrics, the JSON schema,
> and context awareness instructions.

Run the daily WPB Market Intelligence Briefing for **Adam Chow** and **Sirali Siriwardene**.

### For each user (run adam first, then sirali):

**1. Check history**
Read `context/history.json`. Note the URLs and topics covered in the last 7 days so you
don't repeat them unless there's a material update.

**2. Search for news**
Use your web search tool to run each of the search queries listed in CLAUDE.md. Collect
all articles published in the last 48 hours. Aim for 20–40 articles across all queries.

**3. Score and categorise**
For each article, assign:
- `hsbc_relevancy` (0–10) — per the rubric in CLAUDE.md
- `user_relevance` (0–10) — based on this specific user's role and interests
- `noise_level` (1–5) — breadth of coverage
- `category` — one of the 6 categories in CLAUDE.md

Discard articles with combined score (hsbc + relevance) below 6.
Keep a maximum of 5 articles per category, sorted by combined score descending.

**4. Write 3 talking points**
Select the 3 most strategically significant stories for this user. Each talking point needs:
- A sharp headline (max 120 chars)
- 2–3 sentences of context explaining why it matters *specifically* to this user's role
- Wrap person names in `<strong>Name, Title</strong>` HTML tags
- 1–3 supporting article URLs

Do not repeat talking points covered in the last 7 days unless there's a material update.

**5. Write `docs/{user_id}/briefing_data.json`**
Write the complete JSON file following the exact schema in CLAUDE.md.
Include `briefing_date` as a formatted string (e.g. "Saturday, 26 April 2026").
Include `generated_at` as UTC time.

**6. Render HTML**
```bash
pip install -r requirements.txt -q
python src/render.py {user_id}
```
This reads the JSON and writes `docs/{user_id}/index.html`.

**7. Publish to Notion**
Using the Notion MCP connector, create a new page in the database
**"WPB Weekly Intelligence Briefings"** with:
- Title: `[{display_name}] WPB Briefing — {date}` (e.g. `[Adam] WPB Briefing — 26 Apr 2026`)
- A red callout with the user's name and title
- A divider
- Heading: "🎯 Key Talking Points" — then each talking point as Heading 3 + paragraph + bullet links
- A divider
- Heading: "📰 Intelligence Feed" — articles grouped by category as Heading 3 + bulleted links
  with scores: `[HSBC 7/10 · Rel 9/10] Article title` linked to article URL,
  followed by a grey paragraph for the summary

### After both users are done:

**8. Update history**
Merge today's covered URLs and talking point headlines into `context/history.json`.
Keep only the last 7 days of data per user.

**9. Commit and push to main**
```bash
git add docs/ context/history.json
git commit -m "briefing: YYYY-MM-DD daily intelligence update"
git push origin main
```
This triggers GitHub Pages to publish the updated briefings automatically.

**10. Publish to GCS**
```bash
gsutil -m rsync -r -d docs/ gs://${GCS_BUCKET_NAME}/
```
This syncs the `docs/` folder to the GCS bucket for web hosting.
Set `Cache-Control` headers so browsers pick up updates immediately:
```bash
gsutil -m setmeta -h "Cache-Control:no-cache, max-age=0" \
  "gs://${GCS_BUCKET_NAME}/adam/index.html" \
  "gs://${GCS_BUCKET_NAME}/sirali/index.html"
```

---

## Schedule

`0 23 * * *` (UTC) = **07:00 HKT** daily

---

## Connectors Required

- **Notion** — add your existing Notion connector in Routine settings

## Environment Variables

Set these in the Claude Code Routine environment settings:

| Variable | Description |
|---|---|
| `GCS_BUCKET_NAME` | GCS bucket name (e.g. `wpb-briefings-static`) |
| `GOOGLE_CLOUD_PROJECT` | GCP project ID |
| `GOOGLE_APPLICATION_CREDENTIALS` | Path to service account JSON key file, OR leave unset if using Workload Identity / Cloud Run default credentials |

The `gcloud` CLI must be installed and authenticated in the runtime environment.
To set up: `gcloud auth activate-service-account --key-file=$GOOGLE_APPLICATION_CREDENTIALS`

---

## Public URLs

**GitHub Pages** (enable on `main` branch, source: `/docs` folder):
- Adam → `https://atomicchowder.github.io/wpb_briefings/adam/`
- Sirali → `https://atomicchowder.github.io/wpb_briefings/sirali/`

**GCS static hosting** (enable on bucket with `allUsers` Storage Object Viewer):
- Adam → `https://storage.googleapis.com/${GCS_BUCKET_NAME}/adam/index.html`
- Sirali → `https://storage.googleapis.com/${GCS_BUCKET_NAME}/sirali/index.html`

If using a custom domain with Cloud CDN or Firebase Hosting, point the CDN origin at the GCS bucket.

---

## Routine Setup (Claude Code UI)

1. Claude Code → Routines → **New Routine**
2. **Name**: `WPB Daily Briefing`
3. **Prompt**: paste everything in the "Routine Prompt" section above
4. **Repository**: `AtomicChowder/WPB_Briefings` (branch: `main`)
5. **Schedule**: custom cron `0 23 * * *`
6. **Connectors**: add your Notion connector
7. **Environment variables**: set `GCS_BUCKET_NAME`, `GOOGLE_CLOUD_PROJECT`, and `GOOGLE_APPLICATION_CREDENTIALS` (or ensure the runtime has default GCP credentials)
8. **Create** → **Run now** to generate the first briefing
