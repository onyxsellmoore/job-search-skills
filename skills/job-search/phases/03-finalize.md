# Phase 03: Finalize picks (orchestrator, inline, no confirmation)
Loaded by: router, step `finalize`.
Reads: `<run>/search_A.json`, `<run>/search_B.json`, `<run>/prefs.json`.
Writes: `<run>/picks.json`, `<run>/jd_<slug>.txt` (copy of each pick's winning JD), `<run>/base.json`, then `run_state.py set-roles`.

Open no listing or JD; use only the two search files. One missing or unreadable: use the other and flag it.
Either file flagged `browser_not_connected`: mark `search` failed, stop, ask the user to connect Chrome (router rule 7).

## 1. Merge
- Concatenate both `roles` arrays; collect `flags` and `dropped`.
- Same URL (also compare `alt_urls`): keep the higher `fit`. Same company and title from different sources: keep one, prefer the company's careers page as `url`, other URL to `alt_urls`.
- Drop any role with `fit` below `prefs.min_score` (safety check; search agents already filter).

## 2. One role per company (mandatory)
- Compare companies case-insensitively, ignoring Inc/LLC/Ltd suffixes. Keep the highest `fit` per company (tie: better rank by step 3).
- Each loser goes to `others` with `"note": "same company as <Company>"`; the report offers it as an alternative.

## 3. Rank
Sort by: 1. `fit` descending. 2. Location in `prefs.locations.metros` or `metro_aliases` (case-insensitive match on `location`) before remote-only. 3. Newer `posted_date` first (missing last).

## 4. Pick
- Take the top `prefs.picks_per_day` roles with `fit >= prefs.min_score`. No confirmation question, ever.
- The rest that cleared `min_score` go to `others`.
- Zero or one pick is a normal day. Never pad or lower the bar. Still write both files (empty `picks` is valid) and mark the step done.

## 5. Slugs
`slug` = the company slug from the slug rule: lowercase company name, non-alphanumerics collapsed to a single `-`, trimmed (example `acme-corp`). Unique within the run (append `-2` on a clash).

## 6. Write `<run>/picks.json`
```
{"picks":[{"slug","company","title","url","fit","base_hint","jd_path","id":null}],
 "others":[{"company","title","url","fit","note"}]}
```
`id` = the role's `resurfaced_id` or null. Picks are in rank order.
JD files: for each pick copy its winning search file (`<run>/<jd_path from the search json>`, named `jd_<company-slug>_<A|B>.txt`) to `<run>/jd_<slug>.txt` and set the pick's `jd_path` to `jd_<slug>.txt` (relative to `<run>`). If the source file is missing, set `jd_path` to "" and flag it.

## 7. Write `<run>/base.json`
One entry per surfaced role (picks and `others`) so later runs dedupe. Every entry has `company` (the merge key).
```json
{"jobs":[
 {"id":42,"company":"","resume":""},
 {"company":"","role":"","url":"","alt_urls":"a;b","level":"","location":"","source":"","comp_posted":"","fit":0,"rationale":"","resume":"","status":"top_pick"}],
 "run_log":{"surfaced":0,"top_picks":0,"notes":""}}
```
- Resurfaced role (`resurfaced_id` set): a short entry with `id`, `company`, and fields to update (`status`, `fit`, `rationale`). Without `id`: a full entry (`role` is the title).
- `status`: `top_pick` for picks, `surfaced` for others. `comp_posted` as given, `unknown` if empty.
- `run_log.surfaced` = number of entries; `top_picks` = number of picks; `notes` = `rotating: <rotating_source_used>`, skipped sources and search flags in one line.

## 8. Roles and mark
- `python3 <skill>/scripts/run_state.py set-roles --state S --roles slug1,slug2,slug3` (rank order; zero picks: `--roles ""`).
- `run_state.py mark --state S --step finalize --status done --output picks=picks.json --output base=base.json`.
- Zero picks: `next` moves to `report`.
<!-- skill-version: 2026-10-13 -->
