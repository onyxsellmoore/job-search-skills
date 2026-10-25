---
name: job-search
description: Run a job search end to end. Use to run the job search, find roles, do the daily job run, apply, set up or onboard the job search, sync outreach drafts, or continue/try again after an interrupted or usage-limited run.
---
<!-- skill-version: 2026-10-13 -->

# Job Search router

You are the orchestrator.
1. You coordinate. Agents read pages and write documents; you do neither.
2. Spawn agents in ONE message when `next` says parallel. Search agents A and B may run together (own tabs); contacts and prefill agents never overlap any browser agent.
3. Only you write the tracker (phase 05); agents run read-only tracker commands.
4. Agent prompt: take `head -n 8` of the agent's phase file (its `Params:` line lists what to add) and append those values. Never read an agent phase file in full. Model = `prefs.models` entry for the step; `inherit` means omit the model argument. Agents return a 10-line digest and `flags`, never questions.

## Router
1. Paths. `<skill>` = absolute path of the folder holding this SKILL.md; every command is `python3 <skill>/scripts/...` and every agent gets `<skill>` in Params. A bare script name below (`run_state.py`, `ws_sync.py`) means that full command. `<ws>` is always a local path. Connected folder "Job Search" mounted locally: `<ws>` is it. Device folder (only device tools): `<ws>` = `/mnt/user-data/outputs/ws` (a container mirror; the only tree `device_commit_files` accepts), `<staged root>` = `/mnt/user-data/uploads/<folder-name>` (folder-name = basename of the connected folder), `<ws-device>` = the folder's absolute device path (`get_device_info`). No folder: ask the user to connect one; stop.
2. Session setup, at the start of every session (also "continue"), before run_state; it is not a checkpointed step:
   - Dependency check (`phases/01-orient.md` section 0).
   - Device mode: `mkdir -p <ws>`; `device_list_dir <ws-device>` recursive, saved as JSON L; `python3 <skill>/scripts/ws_sync.py plan-stage --listing L --date <date> --batch 50`; `device_stage_files` each batch; `ws_sync.py pull --src <staged root> --dst <ws>` (skip when nothing exists yet). Pull only before any local writes; it refuses when the mirror has unsynced changes.
   - `python3 <skill>/scripts/profile_check.py --workspace <ws>`: exit 2 or not ok: follow `phases/00-onboarding.md`, then restart. Tracker `<ws>/application_tracker.xlsx` must exist (orient section 2).
   - Resume: `python3 <skill>/scripts/run_state.py latest --runs-dir <ws>/runs`. Unfinished run from an earlier date: ask once, finish it or start fresh. Finishing it pins `<date>` to its state's date for every file name; device mode: plan-stage again with `--date <that date>`, stage the extras, then `pull` (nothing unsynced exists yet at this point).
3. Sync back (device mode only), after onboarding writes, after the last mark of each parallel set (one sync per set, not per mark), after every other mark, and after the report. Run `ws_sync.py changed --ws <ws>`; for each path P listed call `device_commit_files` with `{stagedPath: "<ws>/P", devicePath: "<ws-device>/P"}` (up to 50 per call; missing device folders are created by the commit, no mkdir); then `ws_sync.py ack --ws <ws>`. This carries PDFs, events log, outreach file, tracker, profile and run files.
4. `<date>` = `TZ=<user timezone> date +%F` with the timezone taken from the conversation context (fall back to the system date), or the pinned date. `<run>` = `<ws>/runs/<date>`. `python3 <skill>/scripts/run_state.py init --runs-dir <ws>/runs --date <date>` prints state path S.
5. Loop `run_state.py next --state S --parallel`, then `run_state.py mark --state S --step X [--role R] --status done --output key=path`, until done. Inline steps (orient, finalize, report): read the phase file. Agent steps: do not read it; pass its path.
6. Parallel sets: search (A, B, pipeline, networking; on a resumed search spawn only the agents whose report file is missing from `<run>`: search_A.json, search_B.json, report_pipeline.json, report_networking.json), build (all roles), draft (all roles). One role at a time, rank order: contacts, prefill.
7. Failed agent: mark `failed`, retry once, then do it inline. Flag `browser_not_connected` from any agent (after its ToolSearch load): do not mark the unit, stop, ask the user to connect Chrome and say "continue". Role ends `skipped` on builder brief `skipped` or rolectx `form.disqualifying`/`form.heavy`; phase 05 reports it.
8. "Try again", "continue", usage limit: session setup, then step 5 again. Never redo done work.
9. "Sync my outreach": session setup, then `phases/06-outreach-sync.md` only, inline or as one agent (Params: date, skill, ws, run); no run_state mark. Then sync back (rule 3) before replying.

## Guardrails
- Never submit an application. Never send anything; Gmail is draft-only (phase 06).
- No em-dashes. Never fabricate. Resume exactly 1 page. Cover letter only if the form has the field.
- Honest location. Live form gating on residency outside targets: role is dead.
- EEO answers accurate from `profile/eeo.json`, never default-decline.
- Hard stops: Chrome not connected, tracker implausibly small.
- One role per company. Zero picks is normal. No confirmations.

## LOAD MAP
Paths relative to this folder. `sources/<pack>.md` means `core.md` plus each pack in `prefs.source_packs`.

| step | phase file | rules | profile files | runner |
|---|---|---|---|---|
| onboarding | phases/00-onboarding.md | | | orchestrator |
| orient | phases/01-orient.md | | | orchestrator |
| search | phases/02-search-agent.md | rules/scoring.md<br>sources/<pack>.md | profile/profile_summary.md | agent, browser, models.search |
| search:pipeline | phases/02-pipeline-agent.md | rules/voice.md | profile/profile_summary.md | agent, no browser, models.search |
| search:networking | phases/02-networking-agent.md | | profile/profile_summary.md | agent, no browser, models.search |
| finalize | phases/03-finalize.md | | | orchestrator |
| build | phases/04a-builder-agent.md | rules/resume.md<br>rules/voice.md | profile/profile.md<br>profile/resume.json | agent, no browser, models.builder |
| contacts | phases/04b1-contacts-agent.md | rules/outreach.md<br>rules/forms.md | profile/profile_summary.md | agent, browser, models.recon |
| draft | phases/04b2-draft-agent.md | rules/voice.md<br>rules/outreach.md<br>rules/cover-letter.md | profile/profile.md<br>profile/resume.json | agent, no browser, models.draft |
| prefill | phases/04b3-prefill-agent.md | rules/forms.md | profile/eeo.json | agent, browser, models.prefill |
| report | phases/05-report.md | | | orchestrator |
| outreach_sync | phases/06-outreach-sync.md | rules/voice.md<br>rules/outreach.md | | agent, no browser, models.draft |
