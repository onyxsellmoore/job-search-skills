# Resume tailoring rules (generic)
Owner of: what a tailored resume may change, the ATS pass, page and structure rules, the verification checklist. Mechanics live in scripts: `render_resume.py` (layout) and `resume_guard.py` (fabrication check). Do not hand-build PDFs.

## 1. Never fabricate
Tailoring is wording, emphasis, order, and selection of facts already in `profile/resume.json` or `profile/profile.md`. It never adds a fact.
- Metrics: no new number, percentage, dollar figure, team size, or duration. A figure the profile marks as an estimate keeps its hedge every time it appears.
- Scope verbs: keep the source verb's weight. Contributed is not led, helped is not owned, supported is not architected, assisted is not managed.
- Titles, employers, dates, locations of employers: copy exactly. Never infer, upgrade, shorten, or rename a title.
- Skills: only tools and skills in the base skills section, or in the profile's defend-in-interview list. If the JD wants one the candidate lacks, leave it out and mention it to the user in one line.
- Projects, patents, publications, certifications, coursework, education: only as listed.
- When in doubt, leave it alone. A less-tailored resume beats a false claim.

## 2. ATS keyword pass (before any other edit)
1. Extract exact phrases from the JD in this order: required qualifications, responsibilities, job title as written, any term repeated 3 or more times.
2. Build two lists: multi-word phrases to mirror verbatim, and single keywords (tools, methods, channels, platforms).
3. Directional substitution: when the resume and JD name the same thing differently, use the JD's term. Only when the meaning is truly the same and the candidate really did it. Never swap toward a term the JD does not use.
4. Skills alignment: move what the JD names to the front of its group; demote or drop noise. Cap the list at what the candidate would defend in an interview. Respect `prefs.resume.skills_cap` if set.
5. Title echo: use the JD's exact title wording in the summary only, and only if the candidate's real level or title supports it. Never in a title line.
6. Target: at least 3 to 5 JD phrases appear verbatim, each in a sentence that is true.

## 3. Techniques
- Bullets: keep, drop, and reorder within a role; lead each role with the bullets whose subject matches the JD's top responsibilities. Never move a bullet to another role. Never add a bullet.
- The base's strongest proof point for this archetype stays and goes first in its role. Do not prune the lead evidence.
- Vary bullet openings and length. Prefer ownership verbs the source already uses.
- Summary: 2 to 4 sentences. Lead with the identity and evidence that maps to the JD's emphasis, using exact JD phrases where true. Every claim must be backed by a bullet or profile fact elsewhere in the document. No tricolon filler, no adjectives without proof.

## 4. Structure
- Per-title blocks: each title at one employer keeps its own dated section and its own bullets. Never stack titles over one pooled list. Far-past titles may be combined only if the base already combines them; recent titles never.
- Section order is the base's order. Do not add, rename, or drop sections.
- Early-career resumes: Education usually leads, and coursework, projects, leadership, and internships carry the evidence. GPA appears only if the base has it. Keep what the base calls leadership as leadership, not employment.
- Exactly 1 page (or `prefs.resume.max_pages` if set). Fit by pruning bullets or tightening wording. The template enforces an 8pt minimum body and 0.38in margins; never try to get around it.
- Do not alter the layout.

## 5. Whole-packet consistency
The resume's lead evidence (the 1 to 3 strongest facts you chose for this role) also drives the cover letter, short answers, and outreach for that role.

## 6. Verification checklist (all must pass)
- [ ] `resume_guard.py` returned ok and its warnings were read.
- [ ] `render_resume.py` exit 0, one page. Type and margins untouched (template minimums: 8pt body, 0.38in margins).
- [ ] 3 to 5 exact JD phrases present; each backed by a source bullet.
- [ ] Spot-check 3 to 5 numbers against the base. No new skill. Titles, employers, and dates identical.
- [ ] No scope verb upgraded. Summary claims all traceable.
- [ ] Per-title blocks intact; no bullet moved between roles.
- [ ] Location item follows the relocation rule (clause only for roles in the target metro).
- [ ] No em-dash and no spaced hyphen used as punctuation in any text (the renderer rejects them; source files may carry them, so scan edited text anyway). Voice checklist in `rules/voice.md` passed.
- [ ] Only the final PDF is in `<out>`; working JSON stays in `<run>`.
If any check fails and cannot be fixed, ship the unmodified chosen base (guard and render still must pass) and flag it. Never ship a broken or fabricated resume.
<!-- skill-version: 2026-10-15 -->
