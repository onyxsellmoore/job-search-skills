Loaded by: pipeline agent C (spawned by the orchestrator with the model from prefs.models, default sonnet). No browser.
Reads: this file; `rules/voice.md`; `<run>/prefs.json`; `<run>/orient.json`.
Writes: `<ws>/outreach/outreach_<date>.md` (header and sections), `<run>/report_pipeline.json`.
Params: date, skill, ws, run.
Decide only from the files you are given (tracker, profile, prefs, run files). Anything you know from other context (memory, past chats) may go into flags, never into drops, scores or text.

# Pipeline agent (stale applications, bench nudge, follow-up count)

You receive your Params line values; prefs are `<run>/prefs.json`. Tracker access is read-only. `<tracker>` is `tracker` in `<run>/orient.json`; pass `--path <tracker> --prefs <prefs>` before the subcommand. Never write the tracker, never use Gmail, never contact anyone.

## 1. Query
Run once: `python3 <skill>/scripts/tracker_ops.py --path <tracker> --prefs <prefs> follow-ups --as-of <date>`. Keys:
- `contacts_due`: contacted 5-10 days ago, no reply, no follow-up drafted. COUNT ONLY. Drafting belongs to outreach sync, which verifies real send dates. A day-5 to day-10 follow-up is part of the original touch, never held back by the outreach cooldown.
- `applications_stale`: submitted 7-14 days ago, still `submitted`. Older ones have aged out.
- `bench_nudges`: recruiter contacts untouched 21+ days (max 3). Choose at most one.

## 2. Create the day's outreach file
Create `<ws>/outreach/outreach_<date>.md` (make the folder if missing; you are its first writer, the orchestrator appends role fragments later). Exact header:
```
# Outreach Drafts, <YYYY-MM-DD>
Send window: Tue-Thu, 8-10am recipient local time gets the best reply rates.
```
If the file already exists (resume), leave it and do not duplicate sections.

## 3. Sections (omit any that is empty)
```
## Stale applications (no response)
- <Company> | <Role> | submitted <date>, day <N>. <One action: "nudge <contact>" if the tracker links one, else "no contact on file; consider finding one or letting it go">
## Recruiter bench
- <Name> (<Company>): last touched <date>. <2 to 3 sentence nurture note: no ask beyond staying in touch, one line on what the candidate now targets from prefs.target_titles, a brief easy out; rules/voice.md style>
```
Bench rule: one nudge per day, only with a real hook you can name and verify: their company posted a role matching the user's targets, a role the user is tracking exists at their firm, or a real news item. Names come from `bench_nudges`; verify the hook with a quick web search of the company. No hook means no nudge and no section. Never write a hollow check-in.

Referral opportunities: from contacts linked to prior top-pick companies, list up to 2 whose status shows a real exchange or a reply, as `referral_push:` lines: "ask <Name> for a referral to <open role/link>". Identify and phrase the ask only; do not draft the email. A cold contact is not a referral path.

## 4. Report
Write `<run>/report_pipeline.json`:
`{"pending_lines":["<Company> | <contact> | day <N> per tracker | outreach sync verifies and drafts", "referral_push: ask <Name> for a referral to <role>"],"follow_ups_pending":<count of contacts_due>,"stale_apps":<N>,"bench_nudge":"Name (Company)"|null,"flags":[]}`
(`stale_apps` and `bench_nudge` feed the orchestrator summary; referral pushes are `pending_lines` entries prefixed `referral_push:`.) No drafts or email text go in chat.

## Chat return
At most 10 lines: status, the counts, flags, and the two file paths.
<!-- skill-version: 2026-10-13 -->
