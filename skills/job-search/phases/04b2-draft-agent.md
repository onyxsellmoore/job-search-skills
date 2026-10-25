Loaded by: draft agent (no browser, no Chrome tools). All roles run in parallel. Orchestrator spawns it with model prefs.models.draft (default inherit).
Reads: this file; rules/voice.md; rules/outreach.md; rules/cover-letter.md ONLY if form.cover_letter_field is true; <ws>/profile/profile.md; <ws>/profile/resume.json (cover letter only); <run>/prefs.json; <run>/orient.json; <run>/brief_<slug>.json; <run>/rolectx_<slug>.json; the role's jd file.
Writes: <run>/outreach_<slug>.md (own fragment), <run>/essays_<slug>.md (only if prompts exist), cover letter PDF in <ws>/tailored/ (only if the field exists), <run>/report_<slug>.json. Chat digest <= 10 lines.
Params: date, skill, ws, run, role slug (company and title come from `<run>/brief_<slug>.json`).
Decide only from the files you are given (tracker, profile, prefs, run files). Anything you know from other context (memory, past chats) may go into flags, never into drops, scores or text.

Never touch the shared outreach file, the tracker, or any browser tool. Public sources only, by web search and fetch.

## Step 1: gate
- The orchestrator skips draft for roles with rolectx `form.heavy` or `form.disqualifying` true. If you are run for one anyway: copy `form.notes` into `flags`, write a minimal report (step 7), stop. Draft nothing.

## Step 2: company cooldown (before any cold outreach)
Run `python3 <skill>/scripts/tracker_ops.py --path <tracker> --prefs <run>/prefs.json company-cooldown --company "<Company>"` (`<tracker>` = `tracker` in `<run>/orient.json`; the output is one JSON object per line, one line for a single `--company`).
- `in_cooldown` true: no outreach for any contact here. Write one line to the fragment: `Outreach skipped, <Company> in cooldown until <free_on> (last contacted <last_cold_outreach>, <last_contact_name>).` Set `outreach_skipped_cooldown` true in the report. Still do essays and cover letter.
- Otherwise draft. At most one person per company per touch; never email two people about the same role.

## Step 3: contact and email
- Pick the top contact by `priority`. Never use anyone in `flags` as a 1st-degree question, and never mention a mutual connection unless the profile or the user's brief states the user knows them. Otherwise put the idea in `flags` as a question and omit it.
- Email: infer the company pattern from public sources only (press releases, public commit emails, speaker or paper pages, bios). A confirmed general channel (careers@, recruiting@, a named recruiter) beats a guessed personal address. Record `confidence`: "confirmed" or "guess". No pattern found: leave email empty, note it in `flags`.
- Recruiter channel: use the recruiter templates in rules/outreach.md.

## Step 4: outreach fragment
Write <run>/outreach_<slug>.md with a heading `## <Company>`: To, Subject, Body, then "Follow-up (send day 5-10 if no reply)".
- Follow rules/outreach.md for subject length, body length, the easy out, greeting line and signature block (signature from `<ws>/profile/profile.md`). Voice per rules/voice.md.
- Exactly one email and one follow-up. The follow-up adds a new hook, has its own easy out, and carries greeting and signature. No sequence.
- Lead with the evidence in the brief's `lead_evidence`. Every claim traces to `<ws>/profile/profile.md` or resume.json. Never fabricate.

## Step 5: essays
For each `form.essay_prompts` entry, answer the verbatim `prompt_text`, honoring its `limit`; default 100-150 words.
- Shape: a hook proving the JD was read, 2-3 sentences of fit with one concrete achievement from `lead_evidence`, 1-2 sentences on what the candidate wants to do in the role. Vary phrasing across prompts; do not repeat sentences.
- Write <run>/essays_<slug>.md with one `### <field_label>` heading per prompt (label exactly as in rolectx) followed by the answer text only.
- Can't answer a prompt truthfully from the profile: leave that heading with `NEEDS USER` and add a flag.

## Step 6: cover letter (conditional)
- `form.cover_letter_field` false: write none, `cover_letter_path` null. Do not guess.
- True: read rules/cover-letter.md, write it, render it with `python3 <skill>/scripts/render_cover_letter.py` to <ws>/tailored/cover_letter_<company-slug>_<role-slug>_<date>.pdf (take slugs and date from `brief.resume_path`, replacing the `resume_` prefix). Cannot write a strong, true letter from the profile: flag it instead of shipping a generic one.

## Step 7: report
Write <run>/report_<slug>.json:
```
{"company","tracker":{"status":"packet_ready","cover_letter":"<pdf path or empty>"},
 "contacts":[{"name","title","channel","email","confidence","relationship","linkedin_url","draft_ref"}],
 "outreach_skipped_cooldown":false,"outreach_fragment_path":"","essays_path":"","cover_letter_path":null,
 "flags":[]}
```
Each contact row carries `email` (empty string when unknown; never omit the key), which import-run stores in the tracker. `draft_ref` = `outreach/outreach_<date>.md#<company>` with `<date>` from `<run>/orient.json` (the run's date, never today's). Never put email bodies or essay text in the report or digest.

## Digest (chat, <= 10 lines)
status, contact count, outreach drafted or skipped-cooldown, essay count, cover letter yes/no, flags, report and fragment paths.
<!-- skill-version: 2026-10-13 -->
