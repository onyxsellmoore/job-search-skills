# Phase 01: Orient (orchestrator, inline)
Loaded by: router, step `orient`.
Reads: `profile_check.py` output, tracker via `tracker_ops.py`.
Writes: `<run>/prefs.json`, `<run>/blocked.json`, `<run>/orient.json`.

`<skill>` = absolute path of the folder holding SKILL.md (given in Params). `<ws>` = workspace. `<tracker>` = the path every tracker command gets as `--path`.

## 0. Python dependencies (session setup, before anything else)
```
python3 -c "import reportlab, openpyxl, pdfplumber" 2>/dev/null || pip install --break-system-packages reportlab openpyxl pdfplumber
python3 -c "import reportlab, openpyxl, pdfplumber"
```
Still failing after the install: STOP and tell the user which package failed.

## 1. Date and run directory
- `<date>` is the date the router gives (today, or the pinned date of a resumed run); weekday from it.
- `<run>` = `<ws>/runs/<date>/` and `<tracker>` = `<ws>/application_tracker.xlsx` in both modes (`<ws>` is always a local path, see SKILL.md).
- Always pass `--path <tracker>`; never guess paths.

## 2. Tracker
- Missing on the first run (no `<ws>/runs/` history): `python3 <skill>/scripts/tracker_ops.py --path <tracker> init`, the only case a blank tracker is correct. Missing otherwise: STOP and ask.
- Any `tracker_ops.py` exit 3 (shrink guard) or "refusing" error: STOP, report plainly, never force.

## 3. Tracker health (hard stop)
`tracker_ops.py --path <tracker> summary` gives `total_jobs` and `last_run_date`.
- Compare `total_jobs` with the newest `<ws>/application_tracker.autobak.*.xlsx` beside the tracker (`summary` on it via its own `--path`); no backup present: skip the comparison.
- Zero rows, or under about 70% of the backup, with prior runs logged: do NOT continue. Report row count, file date, newest backup; ask how to proceed. Write nothing.
- Days since last run = today minus `last_run_date` (null: 0).

## 4. Preferences and blocklist
- `python3 <skill>/scripts/profile_check.py --workspace <ws> --print-prefs > <run>/prefs.json`. Non-zero: go to onboarding.
- `python3 <skill>/scripts/tracker_ops.py --path <tracker> --prefs <run>/prefs.json blocked-companies > <run>/blocked.json`. It applies excluded companies, cooldowns and overrides; never recompute. Search agents run `dup-check` themselves.
- Write `<run>/orient.json`: `{"date","weekday","ws","ws_device","run","tracker","mode":"local|device","days_since_last_run"}` (`ws_device` is "" in local mode). Agents take the tracker path, mode and `ws_device` from it.

## 5. Browser (hard stop)
- Load the tools in one call: ToolSearch `select:mcp__claude-in-chrome__tabs_context_mcp,mcp__claude-in-chrome__list_connected_browsers,mcp__claude-in-chrome__navigate,mcp__claude-in-chrome__read_page,mcp__claude-in-chrome__get_page_text,mcp__claude-in-chrome__find,mcp__claude-in-chrome__form_input,mcp__claude-in-chrome__file_upload,mcp__claude-in-chrome__tabs_create_mcp,mcp__claude-in-chrome__tabs_close_mcp`. Then `list_connected_browsers`.
- None connected: stop. Tell the user contact finding and pre-fill need the Chrome extension; ask them to open Chrome, enable it, approve the connection, and say "done". Re-check, then continue.
- Never fall back to pixel-level computer use or a fetch-only run.
- Pre-fill happens in the user's Chrome only, never the in-app browser pane (work there is lost when it closes).

## 6. Mark
`run_state.py mark --state S --step orient --status done --output prefs=prefs.json --output blocked=blocked.json --output orient=orient.json`
<!-- skill-version: 2026-10-13 -->
