# WPB Daily Briefing — Claude Code Routine

## Routine Prompt

> Read CLAUDE.md first — it contains all user profiles, scoring rubrics, the JSON schema,
> and context awareness instructions.

Run the daily WPB Market Intelligence Briefing for **Adam Chow** and **Sirali Siriwardene**.

### Step 1 — Check history

Read `context/history.json`. Note covered URLs and topics for the last 7 days.

### Step 2 — Parallel research (spawn 5 Haiku agents simultaneously)

Spawn the following 5 sub-agents **in a single message** using `model: "haiku"`.
Each agent searches for recent articles and returns a JSON array. Collect all results before proceeding.

**Agent A** — queries:
1. `HSBC WPB wealth management Asia Pacific strategy 2026`
2. `HSBC competitor analysis wealth management April 2026`

**Agent B** — queries:
1. `DBS Standard Chartered Citibank private banking technology 2026`
2. `HASE Hang Seng PayMe digital banking Hong Kong 2026`

**Agent C** — queries:
1. `UBS JP Morgan Deutsche Bank wealth management Asia 2026`
2. `Hong Kong Singapore wealth management fintech April 2026`

**Agent D** — queries:
1. `AI artificial intelligence private banking wealth advisory April 2026`
2. `AI large language models banking finance enterprise 2026`

**Agent E** — queries:
1. `Banking change execution agile transformation financial services April 2026`
2. `Wealth management regulatory Asia Pacific 2026`

Each agent must return a JSON array:
```json
[
  {
    "title": "Article title",
    "url": "https://...",
    "source": "Publication name",
    "published_at": "2026-04-27",
    "summary": "2-3 sentence summary of article content.",
    "category_hint": "AI & Technology"
  }
]
```

### Step 3 — Score, select and write Adam's briefing

From the aggregated article pool:
- Assign `hsbc_relevancy`, `user_relevance`, `noise_level`, `category` per CLAUDE.md rubrics for **Adam**
- Discard combined score < 6; max 5 per category; sort descending
- Select 3 talking points
- Write `docs/adam/briefing_data.json` per the schema in CLAUDE.md
- Run: `pip install -r requirements.txt -q && python src/render.py adam`

### Step 4 — Score, select and write Sirali's briefing

Repeat Step 3 for **Sirali** with her role-specific scoring.
- Write `docs/sirali/briefing_data.json`
- Run: `python src/render.py sirali`

### Step 5 — Publish both to Notion

For each user, create a page in **"WPB Weekly Intelligence Briefings"**:
- Title: `[{display_name}] WPB Briefing — {date}`
- Red callout with user name and title
- Divider
- Heading: "🎯 Key Talking Points" → each as Heading 3 + paragraph + bullet links
- Divider
- Heading: "📰 Intelligence Feed" → articles grouped by category as Heading 3 + bulleted links
  with scores: `[HSBC 7/10 · Rel 9/10] Article title` linked to URL, followed by grey summary paragraph

### Step 6 — Update history and publish

```bash
# Update context/history.json with today's covered URLs and talking point headlines
# (keep only last 7 days per user)

git add docs/ context/history.json
git commit -m "briefing: $(date +%Y-%m-%d) daily intelligence update"
git push -u origin claude/nifty-hawking-APWMo
```

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

- Adam → `https://atomicchowder.github.io/wpb_briefings/adam/`
- Sirali → `https://atomicchowder.github.io/wpb_briefings/sirali/`

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
