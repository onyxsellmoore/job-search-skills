# Phase 05: Report (orchestrator, inline)
Loaded by: router, step `report`; the last section is used again after step `outreach_sync` finishes.
Reads: `<run>/picks.json`, `<run>/base.json`, `<run>/orient.json`, `<run>/search_*.json`, `<run>/brief_<slug>.json`, `<run>/rolectx_<slug>.json`, `<run>/report_*.json`, `<run>/outreach_<slug>.md`, `run_state.py show` output.
Writes: `<ws>/outreach/outreach_<date>.md` (appended), `<run>/run.json`, tracker, `<run>/outreach_expected.json`.

`S` = state path; `<tracker>`, `<ws>`, `<date>` from `orient.json`. Every `tracker_ops.py` call gets `--path <tracker> --prefs <run>/prefs.json`.

## 1. Pull skipped roles
Classify each pick from `brief_<slug>.json` and `rolectx_<slug>.json` (missing = step never ran):
| Cause | Role is | base.json entry | Chat |
|---|---|---|---|
| `form.disqualifying` true | dead | `status: "dead"`, `review_notes` = `form.disqualifying_reason`, `resume` empty | pulled, with the reason |
| `brief.skipped` = `location_conflict` | dead | `status: "dead"`, `review_notes` = the brief's first flag, `resume` empty | pulled, with the reason |
| `form.heavy` true, not disqualifying | heavy | status stays `top_pick`, `review_notes` = `form.notes`, resume kept | "needs your call": apply URL, resume link, `form.notes`; no outreach or pre-fill done |
Dead and heavy roles have no draft or prefill report and are not live picks. If live picks fall below `prefs.picks_per_day` and an `others` role has `fit >= prefs.min_score`, flag an offer to build it; never restart the run yourself.

## 2. Resume paths
Live and heavy picks: base.json `resume` = `resume_path` from `brief_<slug>.json` (relative to `<ws>`).

## 3. Assemble the outreach file
- The pipeline agent normally created `<ws>/outreach/outreach_<date>.md`. If it is missing (resumed run), create it first with exactly this header, then append:
```
# Outreach Drafts, <YYYY-MM-DD>
Send window: Tue-Thu, 8-10am recipient local time gets the best reply rates.
```
- In rank order, append each existing `<run>/outreach_<slug>.md` fragment. A missing fragment is skipped silently.
- Write `<run>/outreach_expected.json`: `{"companies":[...]}` for every company appended whose `report_<slug>.json` lists at least one contact and has `outreach_skipped_cooldown` false (a cooldown-skip line is not a contact).

## 4. Tracker (one shot)
1. `python3 <skill>/scripts/tracker_ops.py --path <tracker> --prefs <run>/prefs.json merge-reports --base <run>/base.json --dir <run> --out <run>/run.json`
2. `python3 <skill>/scripts/tracker_ops.py --path <tracker> --prefs <run>/prefs.json import-run --file <run>/run.json`
- Exit 1 (item errors): fix the named report or base entry, rerun only that item (`add-job` / `update-job`). Exit 2 or 3 (shrink guard): STOP and tell the user.
- Then `tracker_ops.py ... summary`: `total_jobs` must be at least the pre-run count.
- Contacts carry `draft_ref` only, never email text.

## 5. Chat response
No summary document. Send, in this order, skipping empty sections:
1. One line per live pick: `Company | Title | score | apply URL` (`[comp unknown]` when so). Then heavy roles, then `others` one line each (with `note`; ask which they want packets for), then dead roles with reasons.
2. Resume links: one `computer://` link per live or heavy pick's `resume_path`, under `orient.json` `ws_device` (device mode) or `ws`. Never link a dead role's PDF.
3. Cover letter links (only roles that have one) and the outreach file link (same base) `<ws>/outreach/outreach_<date>.md`.
4. Pipeline: `report_pipeline.json` `pending_lines`; `referral_push:` lines as a short "Referral asks" list; `stale_apps` and `bench_nudge` if set.
5. Events: `report_networking.json` `events`, one line each: `name | when | virtual or in person | url`.
6. Flags: every `flags` entry from `search_*.json`, `brief_*.json`, `rolectx_*.json`, `report_*.json` (including pipeline and networking) and `base.json` `run_log.notes`, one line each.
7. Monday only (weekday from `orient.json`): `tracker_ops.py ... funnel`, 4 to 6 lines: surfaced and applied counts, response and interview conversion, top source.
- Zero picks: say so, list `others`, suggest one move (outreach to contacts at recent applications). Always give apply URLs, even if pre-fill failed.

## 6. Mark and hand off
`run_state.py mark --state S --step report --status done --output run=run.json --output expected=outreach_expected.json`, then sync back per SKILL.md (tracker, outreach file, PDFs, events log). The router then runs step `outreach_sync`; no Gmail tool is used before it. No Gmail connector: say so in one line and point at the outreach file.

## 7. After outreach_sync (cross-check)
Relay `<run>/report_outreach_sync.json` as its own section, with its `flags`.
- Every company in `outreach_expected.json` must appear in `drafts_created`, `already_existed`, or `stale_needs_ok`. Each missing one: "`<Company>` was drafted today but is not confirmed synced; run outreach sync again." Never claim a draft the report does not list.
<!-- skill-version: 2026-10-13 -->
