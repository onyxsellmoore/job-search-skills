# Cover letter rules
Loaded by: daily run, step 6, only when a letter is due. Also uses `rules/voice.md`, `<ws>/profile/profile.md`, `<ws>/profile/resume.json`, and the posting text in `<run>/jd_<slug>.txt`.

## When
- `prefs.cover_letter.policy` "always": write one for every pick.
- "field_only": write one only when the posting text asks for a cover letter (you cannot see the application form). If unsure, skip it and tell the user in one line that you can write one if the form has a cover letter field.
- If you cannot write a letter that passes the checklist from true material, skip it and say so. Never ship a generic one.

## Never fabricate
- Every claim, number, project, tool, title, and date traces to `resume.json` or `profile.md`. If you cannot name the source line, cut the sentence.
- Do not claim the user has used the product, attended an event, or knows anyone unless the profile says so. Public facts about the company taken from the posting are fine.
- An estimate stays an estimate.

## Length and shape
- 250 to 350 words, 4 short paragraphs, one page.
- Greeting: "Dear <Company> Hiring Team,". Never guess a name; never "To Whom It May Concern".
- Paragraph 1, hook: one concrete, true result from the user's work that matches what this team needs. No "I am writing to", "I am excited to apply", "thrilled", or "passionate".
- Paragraph 2: the two or three facts that map to this role, with one real number.
- Paragraph 3: one specific, true detail from the posting about the team or company, tied to a real piece of the user's evidence. Show fit; do not gush.
- Close: one or two forward-looking sentences. Signoff `Sincerely,` (or `prefs.cover_letter.signoff`); the script prints the name.

## Tone
- Sales: lead with a result (meetings booked, replies, money raised, sales ranking) and the method behind it.
- Marketing: lead with a campaign or content result and how it was measured; the letter doubles as a writing sample, so make it clean and specific.
- Early career: draw on internships, campus jobs, projects, and leadership; let the numbers speak and make no seniority claims.

## Location
Use `location_line` from the resume step. Mention a move (one plain sentence) only when the role is in `prefs.locations.relocating_to`; otherwise say nothing about location. Never ask for relocation help unless the profile says to.

## Render
Write `<run>/cover_<slug>.json`:
`{"name","contact":[...],"date","recipient_lines":[...],"salutation","paragraphs":[...],"signoff"}`. `name` and `contact` come from `resume.json`, with contact item 0 replaced by `location_line`; `date` written out (for example `October 15, 2026`); `recipient_lines` may be `["<Company> Hiring Team"]`.
`python3 <skill>/scripts/render_cover_letter.py <run>/cover_<slug>.json <out>/cover_letter_<slug>_<role-slug>_<date>.pdf`
Exit 0 done; 2 over one page, cut words and rerun; 3 fix the listed errors (em-dashes, spaced hyphens, schema).

## Checklist
- [ ] Policy says a letter is due.
- [ ] One page, 250 to 350 words.
- [ ] Concrete true opening; no hollow opener or buzzwords.
- [ ] Every claim traceable; estimates hedged.
- [ ] One specific, true detail about this company.
- [ ] No invented name; honest location.
- [ ] No em-dash, no spaced hyphen, no `--`; `rules/voice.md` passed.
<!-- skill-version: 2026-10-15 -->
