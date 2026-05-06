# WPB Daily Briefing — Claude Code Routine

This routine is **deterministic**. Heavy file I/O, git operations, and naming
have been moved out of the LLM prompt into committed scripts. The LLM only does
research, scoring, and writing talking points + the Notion publish step.

---

## Routine Prompt — paste this into Claude Code Routines

> Read CLAUDE.md before starting.

Run the daily WPB Market Intelligence Briefing for **Adam Chow** and **Surali Siriwardene**.

### Step 1 — Sync (mandatory, run first)

```bash
bash bin/briefing-sync
```

This pulls the live `context/history.json` and `docs/` from `origin/main` into the
working tree, regardless of which branch this session was created on, and installs
Python deps. This eliminates the "branch was cloned without main's content" bug.

### Step 2 — Read history

Read `context/history.json`. The `covered_urls` and `covered_topics` fields contain
the union of everything covered in the past 7 days. Do not repeat these unless
there is a material development.

### Step 3 — Search for news (parallel batch)

In a **single message**, fire **all 12 web searches** from CLAUDE.md in parallel.
Sequential searches are forbidden — they cause stream-idle timeouts.

**Freshness filter:**
- If `covered_urls` is non-empty for either user → only collect articles published
  or updated **within the past 48 hours**.
- If `covered_urls` is empty (first ever run) → relax to **7 days**.

Aim for 20–40 articles total across all queries.

### Step 4 — Score and categorise

For each article, assign:
- `hsbc_relevancy` (0–10) — see CLAUDE.md rubric
- `adam_rel` (0–10) and `surali_rel` (0–10) — per-user relevance, both required
- `noise_level` (1–5) — coverage breadth
- `category` — exactly one of the 6 categories in CLAUDE.md

Discard any article whose combined score (`hsbc_relevancy + max(adam_rel, surali_rel)`)
is below 6. (The build script applies the same filter per user.)

### Step 5 — Write 3 talking points per user

For each of Adam and Surali, pick 3 talking points (different selections — the users
have different roles, so the priorities differ). Each needs:
- `headline` (max 100 chars)
- `why_it_matters` (one sentence on direct relevance to that user's role)
- `bullets` (2–3 concise bullets, wrap person names: `<strong>Name, Title</strong>`)
- `source_links` (1–3 supporting URLs as `{url, title}` objects)
- `is_update` (boolean — true if this is a material update on a previously covered story)

### Step 6 — Write the input file

Use **a single Python heredoc via Bash** to write `/tmp/briefing_input.json`.
This is small (under ~10 KB) so there is no stream-timeout risk. See
`briefing_input.example.json` in the repo root for the exact schema.

```bash
python3 - <<'PY'
import json, pathlib
data = {
  "date_str": "2026-05-01",
  "briefing_date": "Friday, 1 May 2026",
  "articles": [ ... ],
  "users": {
    "adam":   { "talking_points": [ ... ] },
    "surali": { "talking_points": [ ... ] }
  },
  "breaking_news": { "adam": [], "surali": [] }
}
pathlib.Path("/tmp/briefing_input.json").write_text(json.dumps(data, indent=2))
PY
```

### Step 7 — Build, render, update history

```bash
python src/build_briefing.py /tmp/briefing_input.json
python src/update_history.py /tmp/briefing_input.json
bash bin/briefing-render
```

`build_briefing.py` deterministically writes both `docs/{user}/briefing_data.json`
files, applying the score filter, category cap (3 per category), and sort.
`update_history.py` adds today's URLs and headlines to `context/history.json` with
a 7-day rolling window.

### Step 8 — Publish to Notion

Use the Notion MCP connector to create one page per user in the database
**WPB Weekly Intelligence Briefings** (data source `3336f349-23b7-8053-9230-000b278a9f1a`).

Page properties:
- `Headline`: `[{display_name}] WPB Briefing — {D Mon YYYY}` (e.g. `[Surali] WPB Briefing — 1 May 2026`)
- `icon`: `📊`
- `Recipient`: `Adam Chow` or `Surali Siriwardene` (exact spelling)
- `Priority`: `High`
- `Briefing Section`: `Talking Point`
- `date:Briefing Date:start`: ISO date string

Page body:

```
> 🔴 **{Name}** — {Title}

---

# 🎯 Key Talking Points

### {Talking Point 1 Headline}
{why_it_matters paragraph}
- {bullet 1}
- {bullet 2}
- {bullet 3}
- [{Source title}]({url})

### {Talking Point 2 Headline}
... (same structure)

---

# 📰 Intelligence Feed

### {Category Name}
- **[HSBC {n}/10 · Rel {n}/10]** [{Article title}]({url})
	> {summary}

---
*Generated {D Mon YYYY} · {N} articles across {C} categories · GitHub Pages: [{url}]({url})*
```

### Step 9 — Publish to main (mandatory)

```bash
bash bin/briefing-publish
```

This commits `docs/`, `context/history.json`, and any code changes, then pushes to
`origin/main` (always main, never the feature branch). Retries on transient failures
and rebases on top of `origin/main` if the push is rejected as non-fast-forward.

GitHub Pages auto-deploys from `main` on every push that touches `docs/**`.

---

## Schedule

`0 23 * * *` (UTC) = **07:00 HKT** daily

## Connectors Required

- **Notion** — add the workspace's existing connector

## Environment Variables

None required. Optional: `GCS_BUCKET_NAME` if mirroring to GCS.

## Public URLs

- Adam → https://atomicchowder.github.io/wpb_briefings/adam/
- Surali → https://atomicchowder.github.io/wpb_briefings/surali/

## Routine Setup (Claude Code UI)

1. Routines → **New Routine**
2. **Name**: `WPB Daily Briefing`
3. **Prompt**: paste the "Routine Prompt" section above
4. **Repository**: `AtomicChowder/WPB_Briefings` (branch: `main`)
5. **Schedule**: cron `0 23 * * *`
6. **Connectors**: Notion
7. **Create** → **Run now**
