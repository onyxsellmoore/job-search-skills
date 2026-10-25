# Rule: Outreach
Loaded by: pipeline agent, contact discovery agent (channel priority and cooldown only), draft agent, outreach-sync (reply, follow-up, cancellation). Voice and AI-tell checks live in `rules/voice.md`; load it too before writing any email.

Outreach is email. Per company: one email (To, Subject, Body) plus one follow-up. No confidence tags or research notes inside the email.

## Channel priority
Pick the single best contact per company, in the order of `prefs.outreach.contact_targets` if set, otherwise:
1. Warm referral: someone the candidate has confirmed they know, or a credible intro. Exhaust first.
2. Recruiter or talent contact. Log them in the tracker contacts sheet; keep a small bench and nurture it with a brief, specific check-in.
3. Team peer or leader on the specific team.
4. Hiring manager, last, only when no warmer path exists. Exception: for early-career sales and marketing candidates and at small companies the hiring manager is often the right first cold target; then put them second, after any referral.
At most one person per company per role. Never email two people at one company about the same role.

## Outreach cooldown
- After cold outreach is drafted to anyone at a company, no new cold outreach to anyone there for `prefs.outreach_cooldown_days` (default 90), even for a new role, even with no reply.
- Exempt: the single follow-up to the same person; recruiter-bench nurture; a referral ask to an already-warm contact.
- A reply from anyone at the company clears the cooldown. A live thread is answered as a reply.
- Check before drafting: `tracker_ops.py --path <tracker> --prefs <run>/prefs.json company-cooldown --company "<Company>"`.
- A company in outreach cooldown never blocks the application. Skip only the email and write one line in the day's outreach file: `Outreach skipped, <Company> in cooldown until <YYYY-MM-DD> (last contacted <YYYY-MM-DD>, <Name>).`
- This is separate from the application cooldown (`blocked-companies`).

## Mutual connections
Never mention a shared connection unless the candidate has explicitly confirmed they know that person. A "2nd-degree via" badge is not confirmation. Default: omit it and open with another specific reason.

## Email address
Find the company pattern from one real example (press releases, public commit emails, papers or speaker pages, blog bios, signatures), then apply it. If unconfirmed, still give the best guess, keep the saved block clean, and list every unconfirmed address in the chat summary.

## Subject line
One rule: 3 to 8 words and at most 50 characters. Name the role plus one concrete hook. Vary the shape across emails: do not open every one with "Your ...", and never use an "N years of X" cadence.
- `Failover work and your platform role` (6 words, 36 characters)
- `Pipeline builder, your AI Eng role` (6 words, 34 characters)
- `Inbound sales intern, your SDR opening` (6 words, 38 characters)
- `Your launch post and the content role` (7 words, 37 characters)
Never: "Quick question", "Following up on my resume", "Exploring opportunities", anything with synergy, leverage, or passionate, or any line that fits any person at any company.

## Body
Order: greeting line `Hi <First name>,`, blank line, body, blank line, signature block. The signature is `Best,` then the full name then the literal full LinkedIn URL, each on its own line, taken from `profile/profile.md` Identity. Never a bare slug, link text, or a search URL. Every email and every follow-up has both; a draft without them is not done.

Body is 3 to 5 sentences; shorter is better. Parts (the easy out and close may share a sentence):
1. Opening: a true, specific reason for contacting this person (their team, post, project, role). Never "I came across your profile."
2. Credibility: one concrete fact from `resume.json` evidence whose archetype tag matches the role; a second item only in the follow-up. Never a resume summary.
3. Ask, softened: one specific, low-pressure ask ("if you have 15 minutes sometime", "happy to send a resume instead"). One ask only.
4. Easy out (required): one sentence that makes "no" free ("If this is not your area, no need to reply").
5. Close: one human sentence.
Cold outreach leads with the work; mention relocation only if relevant and natural.

## Templates by function
Rewrite fresh every time from the candidate's own facts. Never copy these lines.
- Engineering (mid and senior): own, build, and architect verbs over lead, manage, drive when the candidate is pitching hands-on ownership. Lead with the evidence matching the team (reliability metric for platform teams, a shipped system for product or AI teams).
- Sales: lead with a measurable result or a specific account or quota fact, then one sentence on why this company's motion fits. Ask for a short chat about how the team ramps new reps.
- Marketing: lead with a campaign or content result with its number, plus one honest observation about the company's current work. Ask what the team looks for in a first hire.
- Early-career (any function): no seniority claims. Lean on curiosity and evidence: a specific thing about the company's product or work, one project, internship, or result with its number, and a question that shows they did the reading. Ask for advice or a short conversation, not a job.

Example, sales early-career, recruiter:
```
Subject: Inbound sales intern, your SDR opening
Hi Priya,

I saw the SDR opening on your team. During my internship I booked 41 qualified meetings in 10 weeks from cold outbound, and I would like to learn how your team ramps new reps. If you have 15 minutes sometime I would love to hear what the first 90 days look like, or I can just send my resume. No need to reply if this is not your desk.

Best,
Jordan Ellis
https://www.linkedin.com/in/example
```

## Recruiter bench nurture
Two to three sentences, no ask beyond staying in touch, one line on what the candidate now targets (from `prefs.target_titles`), a brief easy out. Only when a genuine hook exists; no hook, no nudge. At most one per day.

## Follow-up (one per contact ever)
Sent day 5 to 10 after the actual send date (the window `tracker_ops.py follow-ups` uses). Two sentences, references the original without repeating it, opens with the greeting, carries an easy out and the signature block. Either add one new specific hook or be a light one-liner with a graceful out. Unconfirmed guessed address with no reply: try LinkedIn or another pattern instead of re-sending.

## Reply draft
Answer their actual message in 2 to 5 sentences, propose one low-pressure next step, accept no specific time, deadline, or request in the candidate's name, and flag any question needing the candidate.

## Interview cancellation recovery (one note per cancellation)
Threaded on the interview thread, 2 to 3 sentences, never a follow-up as well. Use the recorded `cancellation_reason` in one clause if there is one; never guess a reason.
```
Subject: Re: <original interview thread subject>
Hi <First name>,

Sorry to hear the <Role> loop got paused, I know timing is not always in your hands. If it reopens I would still love the chance to talk, and I can work around whatever schedule makes sense. Wishing you and the team well in the meantime.

Best,
<full name>
<LinkedIn URL>
```

## Send timing
Put one line at the top of each outreach file: replies peak Tuesday to Thursday, 8 to 10am recipient local time. Answer a recruiter reply within 24 hours.
<!-- skill-version: 2026-10-13 -->
