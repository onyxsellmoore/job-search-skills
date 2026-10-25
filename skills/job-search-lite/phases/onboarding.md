# Onboarding (first time, or to fill missing parts)
Reads: the user's resume or answers; `<skill>/assets/preferences.example.json`, `<skill>/assets/profile.example.md`, `<skill>/assets/sample_resume_early_career.json`.
Writes: `<ws>/profile/` (resume.json, profile.md, profile_summary.md, preferences.json), `<tracker>`, then the workbook in `<out>`.

Redo only missing parts; never overwrite files the user already approved. Keep messages short and ask in batches (AskUserQuestion when available, max 4 questions per call; otherwise one numbered message). Never invent a fact about the user.

## A. Say how this works (3 lines)
"I'll turn your resume into a clean one-page version, ask about the jobs you want, and save everything in one Excel file. Each day you start a new chat, attach that file, and say 'run job search'. At the end of each chat you download the updated file."

## B. Resume
Ask the user to attach their resume in any format (PDF, Word .docx, text, a photo or screenshot) or paste its text. Read it fully (PDF: `pdfplumber`; .docx: `python-docx`; images: read them directly). An old Word `.doc` file cannot be read: ask them to save it as .docx or PDF, or paste the text. Whatever comes in, everything that goes out is PDF.

No resume: run one batched interview: education (school, degree, dates, GPA only if they want it, honors), every job, internship, or campus role (employer, exact title, city, dates, 2 to 4 things they did with any real numbers), projects, clubs and volunteering, skills and tools, certifications. Write only what they say; put estimates in their words.

Build `<ws>/profile/resume.json` following the schema in the docstring of `<skill>/scripts/render_resume.py` and the shape of `<skill>/assets/sample_resume_early_career.json`:
- Copy names, titles, companies, dates, places, and numbers exactly. Never upgrade or infer.
- Several titles at one employer become separate role blocks with their own bullets.
- No em-dashes, no spaced hyphens, no `--`. Date ranges like `Jun 2025-Aug 2025`.
- Contact line: city and state, phone, application email, LinkedIn (no relocation note here).
- Section order: Education, Experience, then Projects or Leadership as `entries` sections, then Skills. A short summary at the top is optional; include one only if the user's material supports it.

List every ambiguity (unclear dates, missing city, which email and phone to show, whether to keep an unrelated job) and ask them in ONE batch.

Render: `python3 <skill>/scripts/render_resume.py <ws>/profile/resume.json <out>/base_resume.pdf`. Exit 2 = over one page: drop the weakest or oldest bullets, never shrink type or margins, render again. Exit 3 = fix the listed errors. Share the PDF and ask for an explicit OK. Changes requested: edit resume.json, re-render, show again.

## C. Preferences (up to 2 batched rounds; offer defaults, accept "defaults")
1. Function: sales, marketing, or both. If both, ask which comes first; that one is `function` and the other's titles still go in `target_titles`.
2. Target titles. Suggest from this list and let them edit: Sales: Sales Development Representative, Business Development Representative, Account Development Representative, Inside Sales Representative, Associate Account Executive, Customer Success Associate. Marketing: Marketing Coordinator, Marketing Associate, Social Media Coordinator, Content Coordinator, Growth Marketing Associate, Marketing Assistant.
3. Locations: cities they would work in (in person or hybrid), whether remote US is fine, the city they live in now, and whether they are moving somewhere (a relocation note then appears on the resume only for jobs in that city).
4. Lowest acceptable pay (base salary), or skip for no filter.
5. Companies to skip (a current or past employer, for example).
6. Deal-breakers. Default: commission only, 100% commission, unpaid, door to door, multi-level marketing.
7. Application email (personal, not a school address that will expire), phone, LinkedIn URL (full https link, or none).
8. Work authorization sentence in their words (for example "US citizen, no sponsorship needed"). Never guess it.
9. How many roles per day: 1 (default, best for free usage limits) or 2.
10. Gmail (optional): "Want your outreach emails waiting in your Gmail drafts, ready to send? Connect Gmail in Customize > Connectors (or the + button in the chat box, then Connectors), then tell me." If the Gmail tools appear, note their address as `gmail_account`. If they skip it, everything still works with copy-paste.

## D. Write the profile
1. `<ws>/profile/preferences.json` shaped like `<skill>/assets/preferences.example.json`: `career_stage` "early", `levels` ["entry","associate"] (add "intern" only if asked), `title_exclude_keywords` default ["senior","manager","director","vp","head of","lead","principal"], `picks_per_day` from C9, `min_score` 6.5, `freshness_days` 14, `cover_letter.policy` "always" for marketing-first users and "field_only" for sales-first users, `networking.enabled` false, `gmail_account` from C10 (empty if skipped), `identity` filled from B and C (current_employer and current_title may be "student" or "none"; years_experience "less than 1" if so). Remove nothing the schema expects.
2. `<ws>/profile/profile.md` with these sections, shaped like `<skill>/assets/profile.example.md`: Identity; Exact titles held (verbatim from resume.json, with the rule "Use these strings exactly"); Target role; Strengths with evidence (each tied to a bullet, numbers exact); Positioning (one-liner, short arc, why looking: ask once if unknown); Red-flag questions and honest answers (draft from facts, the user edits); Skills they will defend in an interview (ask them to confirm which).
3. `<ws>/profile/profile_summary.md`, at most 2 KB: titles, level, locations, pay floor, skips, deal-breakers, top 5 strengths one line each.

## E. Tracker and check
- `python3 <skill>/scripts/tracker_ops.py --path <tracker> init` (only when `<tracker>` does not exist).
- `python3 <skill>/scripts/profile_check.py --workspace <ws>`; fix everything under `missing` and `errors` until `"ok": true`.
- `python3 <skill>/scripts/profile_check.py --workspace <ws> --print-prefs > <ws>/prefs.json`.

## F. Save and hand off
Pack the workbook (SKILL.md, "End of every chat"), with `--owner "<full name>"`. Then a 5-line summary: titles; locations and remote; pay floor; skips and deal-breakers; email. Close with: "Setup is done. To save your daily usage, start a NEW chat, attach the workbook, and say 'run job search'."
<!-- skill-version: 2026-10-15 -->
