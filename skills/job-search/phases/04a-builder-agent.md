# Phase 04a: Builder agent (one role, no browser)
Loaded by: the orchestrator spawns one builder per role (model from prefs.models.builder, default inherit).
Reads: this file; `rules/resume.md`; `rules/voice.md`; `<ws>/profile/profile.md`; `<ws>/profile/resume.json` (+ the chosen variant under `<ws>/profile/resume_variants/`); `<run>/prefs.json`; the role's JD file (`jd_path` resolved relative to `<run>`).
Writes: `<run>/resume_<slug>.json`; `<ws>/tailored/resume_<company-slug>_<role-slug>_<date>.pdf`; `<run>/brief_<slug>.json`. Never touches the tracker.
Params: date, skill, ws, run, and the role's row from `<run>/picks.json` (slug, company, title, url, base_hint, jd_path).
Decide only from the files you are given (tracker, profile, prefs, run files). Anything you know from other context (memory, past chats) may go into flags, never into drops, scores or text.

## Run params (given by the orchestrator)
Your Params line values; prefs are `<run>/prefs.json`. Slugs follow the slug rule: `<company-slug>` is the role slug given to you; `<role-slug>` is the title lowercased, non-alphanumerics collapsed to `-`, cut to about 30 characters at a `-`.
Scripts live at `<skill>/scripts/`. Work files go in `<run>`, never in `<ws>/tailored/`.

## Steps
1. Read the rule files and profile files above, then the JD at `<run>/<jd_path>`. If that file is under 1500 bytes it is an excerpt: fetch the posting `url` with WebFetch, append the full text to the same jd file, and tailor from the full text; if it is still under 1500 bytes, add a flag. Re-check the location from the JD text itself (no browser here). If it contradicts the location that scored the role (for example onsite-only in a city outside prefs.locations), stop and build nothing: write `<run>/brief_<slug>.json` with `"skipped":"location_conflict"`, empty `resume_path`, and the conflict in `flags`; return the digest with empty `resume_path`. The orchestrator marks the role skipped and dead.
2. Pick the base. Read the company and team from the JD. Compare against each `prefs.resume_variants[].use_when`; the best match wins, else `<ws>/profile/resume.json`. Honor `base_hint` unless the JD clearly contradicts it (then say so in `flags`). A team's culture beats its parent company's. Record the choice as `variant`.
3. Run the ATS keyword pass from `rules/resume.md` on the JD. Keep the top 10 phrases for `jd_keywords`.
4. Copy the chosen base to `<run>/resume_<slug>.json` and edit the copy only: summary, bullet order and selection within each role, skills order and wording, directional word swaps. Do not touch name, other contact items, employers, titles, dates, or section order.
5. Location item (first contact item that looks like a city): start from the base value. If `prefs.locations.relocating_to` is set, the rule is `target_metro_only`, and this role is in that metro (or an alias), set it to `<current city> (relocating to <relocating_to>)`. Otherwise leave it plain. Save the resulting string as `location_line`.
6. Guard: `python3 <skill>/scripts/resume_guard.py --base <ws>/profile/resume.json --tailored <run>/resume_<slug>.json --variants-dir <ws>/profile/resume_variants`. Exit 1 prints violations: fix each (usually revert the offending bullet, number, or skill to the base wording) and rerun until `"ok": true`. Read the warnings too; heavy rewording means soften your edit.
7. Render: `python3 <skill>/scripts/render_resume.py <run>/resume_<slug>.json <ws>/tailored/resume_<company-slug>_<role-slug>_<date>.pdf`. Exit 0 is done. Exit 2 (over one page): prune the least relevant bullet or tighten wording, rerun the guard, render again. Never shrink type or margins. Exit 3: fix the listed content errors. After pruning, `remaining_pt` on a passing render tells you whether a pruned bullet would fit back; add it back only if it fits and it is relevant. End with guard ok and exactly 1 page.
8. Voice pass per `rules/voice.md` on the summary and every edited bullet.
9. Write `<run>/brief_<slug>.json`: `{"company","title","url","variant","lead_evidence":[],"jd_keywords":[],"why_fit","location_line","resume_path","skipped":null,"flags":[]}` (`resume_path` is relative to `<ws>`). `lead_evidence` = the 1 to 3 profile items this resume leads with (they drive the cover letter, essays, and outreach). `why_fit` = two plain sentences. `resume_path` = the PDF path relative to ws (`tailored/...`).
10. If the JD is too generic to tailor (no concrete requirements), render the chosen base unchanged through steps 6 and 7 and flag it. That is the only valid skip. Never skip because of a low fit score.

## Return (chat, 5 fields only)
```
{"company": "", "resume_path": "tailored/...pdf", "variant": "", "brief_path": "<run>/brief_<slug>.json", "flags": []}
```
Flags carry anything you could not ask the user: base override, location conflict, generic JD, pruned lead evidence, a skill the JD wants that the candidate lacks.
<!-- skill-version: 2026-10-13 -->
