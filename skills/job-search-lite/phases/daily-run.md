# Daily run
Reads: `<ws>/prefs.json`, `<ws>/profile/*`, `rules/sources.md`, `rules/scoring.md`, then for the build `rules/resume.md`, `rules/voice.md`, `rules/cover-letter.md`, `rules/outreach.md`, `rules/contacts.md`, and `rules/gmail-sync.md` when the Gmail connector is on.
Writes: `<ws>/runs/<date>/` work files, `<tracker>`, PDFs in `<out>`, the workbook in `<out>`.

`<run>` = `<ws>/runs/<date>`. Keep `<run>/state.json` as `{"done": ["orient", ...]}` and add each step's name when it finishes, so "continue" in this chat resumes at the first step not listed. Load each rule file only at the step that needs it.

## 1. orient
- `mkdir -p <run>`. Tracker `summary` gives `total_jobs` and `last_run_date`.
- `blocked-companies > <run>/blocked.json` (companies the user applied to recently; skip them today).
- `follow-ups > <run>/followups.json` (people due a follow-up, applications gone quiet). Keep for step 10; do nothing with it now.
- Days since last run (null = first run) sets the search window in `rules/sources.md`.
- Gmail connector on: run `rules/gmail-sync.md` now (sent, bounces, replies and rejections, follow-up drafts). Keep its one-line results for step 10.

## 2. search
Follow `rules/sources.md`. Write one JSON line per kept posting to `<run>/candidates.jsonl`: `{"company","role","url","location","arrangement","posted","comp","source","jd_excerpt"}`. Never paste postings into the chat.

## 3. score
- Duplicates: `dup-check --file <run>/candidates.jsonl > <run>/dups.jsonl`. Drop every line with `"suppress": true`. Drop companies in `blocked.json`.
- One role per company: keep that company's best match.
- Score the rest with `rules/scoring.md`. Fetch the full posting (web fetch) only for the top 3 to 5 by your first read, and re-check location, level, and pay from the full text. Save `<run>/scored.json` (score, one-line rationale, comp note, url).

## 4. pick
- Picks = the top `prefs.picks_per_day` roles scoring at least `prefs.min_score`. Others at or above `min_score` are listed but not built.
- Zero picks: normal. Record the others, skip to step 9, and say so plainly.
- Record now, so "continue" later in this chat does not redo the search: for each pick `add-job --company --role --url --location --source --comp-posted --fit --rationale --level --status top_pick --alt-urls` (note the `id` it prints; step 9 needs it); for each other `add-job ... --status surfaced`. Save the full posting text of each pick to `<run>/jd_<slug>.txt` (`<slug>` = company lowercased, non-alphanumerics to `-`).

## 5. build the resume (per pick)
Follow `rules/resume.md`. Copy `<ws>/profile/resume.json` to `<run>/resume_<slug>.json` and edit only the copy.
- Location: if `prefs.locations.relocating_to` is set and this role is in that metro, the first contact item becomes `<current city> (relocating to <relocating_to>)`; otherwise it stays as in the base. Remember this as `location_line`.
- Guard: `python3 <skill>/scripts/resume_guard.py --base <ws>/profile/resume.json --tailored <run>/resume_<slug>.json`. Fix every violation (usually revert to the base wording) until ok.
- Render: `python3 <skill>/scripts/render_resume.py <run>/resume_<slug>.json <out>/resume_<slug>_<role-slug>_<date>.pdf` (`<role-slug>` = title lowercased, non-alphanumerics to `-`, about 30 characters). Exit 2: prune a bullet and re-render. End with guard ok and one page.

## 6. cover letter (per pick, when the policy says so)
`prefs.cover_letter.policy` "always": write one. "field_only": write one only when the posting text asks for a cover letter. Follow `rules/cover-letter.md`; output `<out>/cover_letter_<slug>_<role-slug>_<date>.pdf`.

## 7. application packet (per pick, goes in the chat)
A copy-paste block, in this order:
- **Apply here:** the apply URL, and what to upload (resume PDF name; cover letter PDF name if made).
- **Form answers:** full name, email (`prefs.application_email`), phone, LinkedIn, city (`prefs.locations.current_city`, never the relocation target), work authorization (`prefs.work_authorization`, word for word), "How did you hear about us": the true source (the job board or site where you found it), desired salary: "Leave blank if allowed; otherwise say you are flexible and targeting market rate for the role." Never put the user's pay floor in a form.
- **Short answers,** 60 to 120 words each, for "Why are you interested in this role?" and "Tell us about yourself", plus any question the posting itself names. Use only profile facts and one specific true detail from the posting. Run `rules/voice.md` on them.
- Voluntary self-identification (gender, race, veteran, disability): one line saying these are optional and theirs to answer; never answer for them.

## 8. outreach (per pick, goes in the chat)
1. Cooldown check (`rules/outreach.md`). In cooldown: one line, skip the rest of this step.
2. Find the person and their email with `rules/contacts.md` (best effort).
3. Write the LinkedIn connection note and the email per `rules/outreach.md`, using their real first name when you found one.
4. Gmail connector on: save the email as a draft to the found address (`rules/outreach.md`, "Gmail drafts") and say "It's in your Gmail drafts" instead of repeating the email. Off: put the email in the chat.
5. Record the person: `add-contact --name "<name>" --title "<title>" --company "<Company>" --degree cold --linkedin "<result URL>" --email "<email>" --status drafted --job-id <job id>` (prints the contact `id`), then with a Gmail draft `update-contact --id <contact id> --gmail-draft-id <draft id>`. Add the fallback address to `<ws>/profile/bounces.json` as `{"<contact id>": {"fallback": "<fallback_email>", "tried": ["<email>"]}}`. Before adding, check the contacts sheet so a "continue" never records the same person twice. No person found: record nothing.

## 9. save
- Each built pick: `update-job --id <id> --status packet_ready --drafted-date <date> --cover-letter <cover file name or omit>`.
- `log-run --surfaced <candidates kept> --top-picks <picks> --drafted <packets built> --contacts <people recorded in step 8> --notes "<sources skipped, if any>"`.
- Pack the workbook (SKILL.md, "End of every chat").

## 10. reply (short, in this order)
1. One line per pick: `Company | Title | score | apply URL`, then its packet (step 7) and outreach (step 8).
2. Others worth a look, one line each with the URL. Offer to build one if they want.
3. Inbox news from the Gmail sync, one line each: rejections marked, replies (with reply drafts waiting), interview requests, bounces and retries, follow-ups drafted. Without Gmail: from `followups.json`, people due a follow-up (offer to draft each) and applications quiet for 7 to 14 days.
4. Earlier `packet_ready` jobs that are 2 or more days old: ask in one line whether they applied, so the tracker stays right.
5. The workbook reminder from SKILL.md.
<!-- skill-version: 2026-10-15 -->
