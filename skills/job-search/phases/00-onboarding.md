# Phase 00: Onboarding (orchestrator, inline)
Loaded by: router, when `profile_check.py` exits 2 or lists missing pieces (orchestrator, inline).
Reads: the user's answers and resume; `assets/preferences.example.json`, `assets/eeo.example.json`, and only the sample resume matching the career stage (`assets/sample_resume_early_career.json` or `assets/sample_resume_experienced.json`).
Writes: `<ws>/profile/` (profile.md, profile_summary.md, preferences.json incl. identity, resume.json, base_resume.pdf, optional eeo.json, resume_variants/), `<ws>/application_tracker.xlsx`; then syncs back per SKILL.md.

Redo only the missing parts; never overwrite approved files. Ask in chat, keep messages short, never invent facts about the user.

`<ws>` is the local workspace path from SKILL.md (a container mirror in device mode). `<scratch>` = `<ws>/runs/onboarding/` (work files; sync-back skips `runs/onboarding/`). `<skill>` is the absolute path of the folder holding SKILL.md. Run every script in the container on `<ws>`.

## A. Environment check (do first, report in 4 lines)

1. **Workspace folder.** A folder the user has connected to this session. If none: tell the user to create a folder named "Job Search" on their computer and connect it with the app's "Add folder" button, then say "done". Nothing can be saved without it; stop until it exists.
2. **Chrome extension.** Check that browser tools respond. Required for finding contacts and for pre-filling applications. Without it, daily runs hard stop; onboarding may continue. Ask the user to install and connect it before the first run.
3. **Gmail connector** (optional). Only needed for outreach-sync, which creates Gmail drafts and never sends. Without it, outreach is saved as text files in `<ws>/outreach/`.

Device mode: a resume the user dropped into their folder is not mirrored yet; `device_list_dir` the folder and `device_stage_files` that one file, then read it from the staged path.

## B. Resume intake

Ask the user to drop their current resume (PDF or DOCX) into the folder, or paste their LinkedIn text or resume text. Read it fully (PDF: `pdfplumber`; DOCX: `python-docx`).

**No resume.** Run a structured interview instead, in one batched round: education (school, degree, dates, honors), every job or internship (employer, exact title, city, dates, 2-4 things done with any real numbers), projects, leadership and volunteering, skills and tools, certifications. Write only what the user states; ask again rather than guess; put estimates in the user's own words. Build `<ws>/profile/resume.json` from the answers with the same rules below, and tell the user it is a first draft to edit.

Parse into `<ws>/profile/resume.json` using the schema in the docstring of `<skill>/scripts/render_resume.py` (see `assets/sample_resume_early_career.json` and `assets/sample_resume_experienced.json`). Rules:
- Never invent, upgrade, or infer anything. Names, titles, company names, dates, locations, and numbers are copied exactly as written.
- Several titles at one employer become separate role blocks under one employer, each with its own title, dates, and bullets. There is no pooled bullet list under stacked titles. If the source pools bullets, ask the user which bullets belong to which title.
- No em-dashes, no spaced hyphens used as punctuation, no `--` as a dash. Date ranges use `Mon YYYY-Mon YYYY` (no spaces around the hyphen). If the source has dashes in prose, rewrite with a comma, colon, or period without changing facts.
- Contact line: city and state, phone, application email, LinkedIn. Use the user's real city; do not add a relocation clause here (the renderer step in tailoring adds it only for roles in the target metro).
- Section order by career stage. Early career (student, recent grad, under about 3 years): Education first, then Experience, then Projects or Leadership as `entries` sections, then Skills. Experienced: Summary, Skills, Experience, Education, then extras such as Publications.

**One batched question round.** List every ambiguity (unclear dates, pooled bullets, missing location, unreadable lines, whether to keep old or unrelated jobs, which email and phone to show) and ask them together. Use AskUserQuestion when available (max 4 questions per call; group them into as few calls as possible); otherwise one numbered message. Do not ask one question at a time.

Render: `python3 <skill>/scripts/render_resume.py <ws>/profile/resume.json <scratch>/base.pdf`. Exit 2 means longer than one page: prune content (drop the weakest or oldest bullets, merge nothing across roles, shorten the least important sections). Never shrink fonts or margins. Repeat until exit 0 with exactly 1 page. Tell the user what you pruned.

Show the PDF to the user. Get explicit approval ("yes, use this") before saving it as the base: copy it to `<ws>/profile/base_resume.pdf`. If they request changes, edit `resume.json`, re-render, show again.

## C. Preferences interview

Ask in up to three batched rounds (AskUserQuestion takes 4 questions per call; or numbered lists). Offer a sensible default for each, chosen by function and stage, and let the user answer "defaults".

1. Function: software engineering, sales, marketing, other (if other, ask for a short description; source packs fall back to `core`).
2. Target titles (list), career stage (early, mid, senior), `levels` and title keywords to exclude (e.g. "manager", "director", "intern" for experienced users; "senior", "staff", "director" for early career).
3. Locations: metros (and aliases), remote US yes or no, current city, relocating_to if any. Explain in one line: a relocation clause is added to the resume header only for roles located in the target metro.
4. Pay floor: onsite or hybrid floor, remote floor, total comp or base. Early-career users may skip. Skipping means no pay filter.
5. Companies to exclude. Suggest the current employer. Aliases and subsidiaries go in the same list.
6. Dealbreaker keywords or role types (technologies, industries, flavors of role they will not take).
7. Companies that need a longer cooldown than the default 7 days (optional; name, aliases, days).
8. Application email: the address that goes on every application and signature. It must not be a work email, and must not be a throwaway login. Gmail account for outreach drafts (may be the same).
9. Networking home city, and whether virtual events are fine.
10. Work authorization sentence (for example "US citizen, no sponsorship needed"). Ask for the exact wording; do not guess.

11. Identity for application forms, stored in `<ws>/profile/preferences.json` `identity`: full name, phone, LinkedIn as a full https URL (empty only if the user has none), current employer and title ("none" or "student" is fine), years of experience as a number ("less than 1" for early career), pronouns optional.

`levels` uses only this vocabulary: intern, entry, associate, mid, senior, staff, principal, manager, director. Suggest by stage: early gives `entry`, `associate` (add `intern` only if asked); mid gives `mid`, `senior`; senior gives `senior`, `staff`, `principal`. `profile_check.py` warns on any other value.

Anything unanswered stays at schema defaults (`picks_per_day` 3, `min_score` 6.5 when career_stage is early and 7.0 otherwise, `freshness_days` 14).

## D. Write the profile files

All of these are written from the resume and the user's own statements only.

1. `<ws>/profile/profile.md` with these sections, in order:
   - **Identity**: name, city, phone, application email, LinkedIn (full https URL), work authorization.
   - **Exact titles held**: a verbatim list of every title string from `<ws>/profile/resume.json` with employer and dates, plus the rule: "Use these strings exactly. Never infer, upgrade, shorten, or rename a title."
   - **Target role**: function, titles, level, locations, pay floors, what to avoid.
   - **Strengths with evidence**: each strength paired with the resume bullet or user statement that proves it. Numbers copied exactly; flag estimates as estimates.
   - **Positioning**: one-line pitch, a short career arc, and why they are looking (ask once if not known; for outreach, lead with the work, not the motive).
   - **Red-flag questions and honest answers**: gaps, career switches, short tenures, long tenure at one company, a pivot between tracks. Draft from facts; the user edits.
   - **Skills they will defend in an interview**: ask the user to confirm which listed skills they could discuss in depth; only those may be emphasized in tailored resumes and essays.
2. `<ws>/profile/profile_summary.md`, at most 2 KB: targets and titles, level, filters (excluded companies, title excludes), location rules, pay floors, dealbreakers, and the top 5 strengths in one line each. This is what search and recon agents read, so no filler.
3. `<ws>/profile/preferences.json` per the schema in `assets/preferences.example.json`, including the `identity` block from C11. Set `source_packs` from function: software_engineering gives `["core","software-engineering"]`; sales or marketing gives `["core","sales-marketing"]`; other gives `["core"]`. Leave `models` at defaults.
4. `<ws>/profile/eeo.json` is optional and only if the user volunteers answers (voluntary self-ID fields). Ask every key present in `assets/eeo.example.json` (each optional; the user may decline any), keeping accurate answers only. Standing rule: answer accurately, never default to "decline", flag any field not listed and leave it for the user. Never print or repeat these answers in chat afterwards. If the user declines, skip the file; pre-fill then leaves those fields for them.

Regenerate `<ws>/profile/profile_summary.md` whenever `<ws>/profile/profile.md` or `<ws>/profile/preferences.json` changes.

## E. Resume variants (offer once, do not push)

If the experience supports two clearly different positionings (for example AI-forward versus reliability-forward, or sales-forward versus marketing-forward), offer a second variant. Same facts, same titles, dates, and bullets; only the summary, skills order, and bullet order change. Do not add facts. Render and get approval the same way as the base. Save as `<ws>/profile/resume_variants/<name>.json` and add to `preferences.json`: `"resume_variants": [{"file": "resume_variants/<name>.json", "use_when": "<one line>"}]`. If the user declines, set nothing.

## F. Create the tracker

`python3 <skill>/scripts/tracker_ops.py --path <ws>/application_tracker.xlsx init`

Never overwrite an existing tracker.

## G. Validate and hand off

Run `python3 <skill>/scripts/profile_check.py --workspace <ws>` and fix whatever it reports (missing, errors) until `ok` is true. Warnings can be shown but need not block.

Sync back per SKILL.md now: the whole of `<ws>/profile/` (including `base_resume.pdf` and `resume_variants/`) and `<ws>/application_tracker.xlsx` must reach the user's folder before the first run.

Then show a 5-line summary: function and titles; locations and remote; pay floor; excluded companies and dealbreakers; application email and resume status. Ask: "Start the first run now?" If yes, return to the router (the run stops if Chrome is not connected).
<!-- skill-version: 2026-10-13 -->
