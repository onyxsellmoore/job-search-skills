# Cover letter rules
Loaded by: the draft agent, only when the role's form has a cover-letter field. Also load `rules/voice.md`, `profile/profile.md`, `profile/resume.json`, the role's `brief_<slug>.json`, and the JD.

## When
- Write a letter only if `rolectx.form.cover_letter_field` is true (a file upload or a dedicated cover-letter text field, required or optional).
- An "Additional information" or generic free-text box is not a cover-letter field. Never paste a letter there.
- Exception: if `prefs.cover_letter.policy` is `always`, write one for every packet, saved the same way.
- If you cannot write a letter that clears the checklist from true material, skip it when the field is optional and flag it when required. Never ship a generic one.

## Never fabricate (traceability)
- Every claim, number, project, tool, title, and date must trace to `profile/resume.json` or `profile/profile.md`. Before writing a sentence that makes a claim, name its source line in your head; if you cannot, cut it.
- No hooks about work that is not in those files. Hooks come from the brief's `lead_evidence` and `profile.md` strengths.
- Do not claim use of a product, attendance at an event, or a relationship with a person unless the profile says so. Public facts about the company from the JD are fine.
- A figure the profile marks as an estimate keeps its hedge.

## Length and shape
- 250 to 400 words, 4 or 5 short paragraphs, one page. Cut before you pad.
- Greeting: "Dear <Company> Hiring Team," unless a confirmed hiring-manager contact exists and the name reads naturally. Never guess a name, never "To Whom It May Concern".
- Paragraph 1, hook: one concrete, true idea from the candidate's real work that proves what this team values. No hollow opener ("I am writing to", "I am excited to apply", "thrilled", "passionate"). No restating the job title.
- Paragraph 2, through-line: the relevant spine of the career with one real, verifiable metric. Pick the two or three facts that map to this role.
- Paragraph 3, this team: one specific, true detail from the JD about what the team does, tied to a real project from the lead evidence. Show fit; do not assert enthusiasm.
- Optional paragraph, career-shape note: only if the profile has a transition note and the JD or background would otherwise read as unexplained (a gap, a function switch, a recent move from management to IC). One forward-facing sentence, no justification.
- Close: one or two forward-looking sentences, no groveling. Then the signoff (`Sincerely,` unless `prefs.cover_letter.signoff` is set); the script adds the full name.

## Function-aware tone
- Software and technical roles: plain, specific, named systems and numbers; ownership verbs.
- Sales roles: lead with a result (pipeline, quota, demos booked, replies) and the method behind it; show you understand the buyer.
- Marketing roles: lead with a campaign outcome and how it was measured; a letter is often expected, so make it a sample of the candidate's writing.
- Early-career: draw evidence from internships, projects, coursework, leadership; be honest that these are early experiences and let the numbers speak.
- Match the voice of the resume summary. Mirror the JD's phrasing where true.

## Location line
- Honest everywhere. A header or body location uses the candidate's current location. Mention relocation (one plain sentence, no apology, never implying they already live there) only when the role is in `prefs.locations.relocating_to`'s metro. For other roles, usually say nothing. Use the same `location_line` as the brief.
- Never request relocation support unless the profile says to.

## Voice
Follow `rules/voice.md` in full. Read the letter back; any sentence that could sit in a thousand other letters gets rewritten or deleted.

## Render
Write the letter as JSON in the run dir (never in `tailored/`) and render it with the script; it owns layout (Helvetica, letter, centered name and contact header like the resume) and the one-page check.
```
python3 <skill>/scripts/render_cover_letter.py <run>/cover_<slug>.json <ws>/tailored/cover_letter_<company-slug>_<role-slug>_<date>.pdf
```
Input: `{"name","contact":[...],"date","recipient_lines":[...],"salutation","paragraphs":[...],"signoff"}`. `name` and `contact` come from `profile/resume.json`, with contact item 0 replaced by `brief.location_line`; `date` is today written out (for example `October 13, 2026`); `recipient_lines` is the company or hiring-team lines, may be empty; `salutation` is the greeting; `signoff` is the closing phrase only (`Sincerely,` or `prefs.cover_letter.signoff`), the script prints the name under it. Text must have no em-dash and no spaced hyphen.
- Exit 0: one page, done. Exit 2: over one page, cut words and rerun (never shrink margins). Exit 3: fix the listed content errors.
- Take `<company-slug>`, `<role-slug>` and `<date>` from `brief.resume_path` (replace the `resume_` prefix with `cover_letter_`).
- For a text-field form, the paragraphs (salutation through signoff, no letterhead) are pasted later by the pre-fill agent; the PDF is still saved. Record the relative path as `cover_letter_path` in `report_<slug>.json` (null if none).

## Checklist
- [ ] Form field exists (or policy is always).
- [ ] One page, 250 to 400 words.
- [ ] Opens with a concrete true idea; no hollow opener or buzzwords.
- [ ] Every claim traces to resume.json or profile.md; estimates hedged.
- [ ] One specific, true detail about this team or company.
- [ ] Hook and framing match the resume variant's lead evidence.
- [ ] Greeting invents no name; location line honest.
- [ ] No em-dash, no spaced hyphen, no `--`; voice checklist passed.
<!-- skill-version: 2026-10-13 -->
