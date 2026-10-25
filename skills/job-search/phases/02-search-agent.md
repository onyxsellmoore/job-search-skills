Loaded by: search agents A and B (spawned by the orchestrator with the model from prefs.models.search, default sonnet).
Reads: this file; `sources/<pack>.md` for each pack in prefs.source_packs (`core.md` always); `rules/scoring.md`; `<ws>/profile/profile_summary.md`; `<run>/prefs.json`.
Writes: `<run>/search_<A|B>.json`, `<run>/candidates_<A|B>.jsonl`, `<run>/jd_<company-slug>_<A|B>.txt` (one per kept role, your own letter).
Params: letter (A or B), date, skill, ws, run, days_since_last_run (the orchestrator copies it from `<run>/orient.json`).
Decide only from the files you are given (tracker, profile, prefs, run files). Anything you know from other context (memory, past chats) may go into flags, never into drops, scores or text.

# Search agent (A or B)

## Run parameters you receive
Your Params line values. Fixed paths: prefs `<run>/prefs.json`, blocked list `<run>/blocked.json` (output of `blocked-companies`). Tracker path is `tracker` in `<run>/orient.json`; pass `--path <tracker>` and `--prefs <prefs>` BEFORE the subcommand.

## Assignments
- A: the core must-run aggregator sources (LinkedIn excluded) plus every entry in prefs.direct_career_pages.
- B: LinkedIn plus ONE rotating source from the user's packs: the least recently used, read from `rotating_source_used` in `<ws>/runs/*/search_B.json` (newest first; a never-used source wins). Also run prefs.extra_sources. A and B run in parallel in separate tabs (read-only), so never touch a tab you did not open.
- Work only your assigned sources. If a source fails, shows a CAPTCHA or login wall, or returns nothing, skip it, add it to `flags`, move on.
- Browser: FIRST load the Chrome tools with one ToolSearch (`select:mcp__claude-in-chrome__tabs_context_mcp,mcp__claude-in-chrome__navigate,mcp__claude-in-chrome__read_page,mcp__claude-in-chrome__get_page_text,mcp__claude-in-chrome__find,mcp__claude-in-chrome__tabs_create_mcp,mcp__claude-in-chrome__tabs_close_mcp`). Create your own tab with `tabs_create_mcp` before anything else (do not reuse an existing tab), pass explicit tab IDs, never use the pixel `computer` tool, work only in those tabs, close only the tabs you opened when done, never touch any other tab (not even to close it). Only if that ToolSearch finds no Chrome tools or no browser is connected, stop, write `search_<A|B>.json` with empty `roles` and the single flag `browser_not_connected`, and return it; do not search by other means (the orchestrator stops the run).

## Steps
1. Search. Follow the source pack files for URLs, filters and time budgets. Pass days-since-last-run into the core gap-aware time window. Build keywords from prefs.target_titles and the level-coded variants in the pack, never from memory.
2. Hard filters at collection (silent drops, add each to `dropped` with a short reason, never surface them as "interesting"):
   - title outside target family or levels, or hits prefs.title_exclude_keywords;
   - location fails the card-level filter in `core.md`, including the hidden metro preference rule;
   - older than prefs.freshness_days;
   - company in prefs.excluded_companies, on the blocked list, or text hits prefs.dealbreaker_keywords.
3. Verify. For any role from an aggregator, open the real ATS or company listing before scoring: confirm location, arrangement and any residency wording. Drop if the real page contradicts the target location. Prefer the company or ATS URL as canonical; put the others in `alt_urls`.
4. Dedupe. Collapse cross-source duplicates per `core.md`. Write survivors to `<run>/candidates_<A|B>.jsonl`, one `{"url","company","role"}` per line, and run once: `python3 <skill>/scripts/tracker_ops.py --path <tracker> --prefs <prefs> dup-check --file <that file>`. Drop rows with `suppress` true; if `matched_by` is "title", note "repost suppressed: <company>" in `flags`. A row already at surfaced or top_pick stays: record its `id` as `resurfaced_id`. Never run a tracker write command.
   - Dup-check returning every row unseen (nothing matched, nothing suppressed) is normal, not a sign of an empty tracker; carry on. A tracker command that exits non-zero is a flag: add it to `flags` with the error text, stop searching, and return what you have. Never pretend dedupe ran.
5. Score each survivor 0-10 with `rules/scoring.md`. Be strict; padding wastes the user's review time.
6. Keep every role with fit >= prefs.min_score (the rest are not returned). Save the FULL posting text (`get_page_text` of the posting page, not a summary or excerpt) to `<run>/jd_<company-slug>_<A|B>.txt` (`<company-slug>` per the slug rule: lowercase, non-alphanumerics collapsed to `-`; the suffix is your letter so A and B never overwrite each other). Set `jd_path` to that file name relative to `<run>` (for example `jd_acme-corp_A.txt`), never an absolute path. At most one role per company: keep the highest fit, list the other in `alt_urls`.
7. Comp: use posted comp; if hidden, keep tagged `comp unknown` when the stage plausibly clears the floor (see scoring), drop clear sub-floor roles.
8. `base_hint`: the resume variant name from prefs.resume_variants whose `use_when` matches the role, else "base".

## Volume
Target 15-25 raw listings across A and B together (yours roughly half) before filters. Do not pad with weak matches to hit a number. A thin day is fine; say so in `flags`.

## Output file `<run>/search_<A|B>.json`
```
{"roles":[{"company","title","url","alt_urls":[],"location","level","source","posted_date","comp_posted","fit":0-10,"rationale":"<=15 words","jd_path","resurfaced_id":null,"base_hint":""}],
 "rotating_source_used":"","dropped":[{"company","title","reason"}],"flags":[]}
```
`rotating_source_used` is "" for agent A. Put questions for the user in `flags`; never ask in chat.

## Chat return
A digest of at most 10 lines: status, listings scanned, roles kept, top 3 by fit (company, title, fit), sources skipped, flags, and the file path. No page text, no listings, no JSON dumps.
<!-- skill-version: 2026-10-13 -->
