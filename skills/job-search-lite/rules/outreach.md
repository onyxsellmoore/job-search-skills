# Outreach (the user finds the person and sends; you write)
Loaded by: daily run, step 8, and tracker updates (follow-ups and replies). Run `rules/voice.md` on every message.

You cannot browse LinkedIn. `rules/contacts.md` finds a likely person and email from search results (best effort); always tell the user to confirm the person on LinkedIn before sending. When no person is found, hand them search links and write the messages with `[First name]`.

## Who to look for (one person per company per role)
1. Someone the user already knows there (ask once if they know anyone at the company).
2. The likely hiring manager: for sales roles a Sales Development Manager or SDR/BDR Manager; for marketing roles the Marketing Manager or the head of the team named in the posting. At small companies and for early-career roles this is often the best first contact.
3. A recruiter or talent partner at the company.
4. Someone currently in the same role (a peer), for a short advice ask.
Never suggest messaging two people at one company about the same role.

## Search links (2 or 3 per pick)
`https://www.linkedin.com/search/results/people/?keywords=<URL-encoded "Company role words">`, for example keywords `Acme sales development manager`, `Acme recruiter`, `Acme sales development representative`. Spaces become `%20`.

## Cooldown
Before writing, run `company-cooldown --company "<Company>"`. If the user already messaged someone there in the last `prefs.outreach_cooldown_days` days, skip new outreach and write one line: "Skip outreach to <Company>: you messaged <name> on <date>." The application still goes ahead.

## LinkedIn connection note
Under 200 characters. One specific reason (the role or the team), one fact with its number, and a soft close. No "I came across your profile". LinkedIn may limit notes on free accounts; if the note box is unavailable, the user sends the request without a note and messages after they accept.
Example shape (rewrite fresh every time, never reuse these words): "Hi [First name], I'm applying for the SDR role on your team. I booked 18 demos in a 10-week internship and would value 10 minutes on what makes new reps succeed there."

## Email or LinkedIn message (after they connect, or if an email is known)
- Subject: 3 to 8 words, at most 50 characters, the role plus one concrete hook. Never "Quick question" or "Exploring opportunities".
- `Hi [First name],`, a blank line, then 3 to 5 sentences:
  1. A true, specific reason for writing to this person (their team, the role).
  2. One concrete fact from `resume.json` with its number.
  3. One low-pressure ask: 15 minutes of advice, or "happy to send my resume instead". Ask for advice, not a job.
  4. An easy out ("If this isn't your area, no need to reply.").
- Signature: `Best,`, then the full name, then the full LinkedIn URL from `profile.md` (omit the URL line if they have none).
- Sales version: lead with a measurable result and one line on why this company's product or market interests them. Marketing version: lead with a campaign or content result and one honest observation about the company's current marketing.
- Never mention a mutual connection unless the user confirmed they know that person.

## Gmail drafts (only when the Gmail connector is on)
- Create a draft, never send. Subject from above. `to` = the address from `rules/contacts.md` (or one the user gave you).
- Pass the email as `htmlBody` (simple `<p>` paragraphs, the LinkedIn URL as a link) plus the same text in `body`. Plain-text-only drafts can turn the LinkedIn link into a long Google redirect link.
- Use the found person's first name and address. Only when no person was found, keep `[First name]` and an empty `to`, and tell the user to fill both in before hitting Send. Say in the chat whether the address is confirmed, likely, or a guess.
- A follow-up or reply to a thread the user already has: find the original with one Gmail search and pass its message id as `replyToMessageId`.
- One draft per person. Before creating, search drafts for the same subject so a "continue" does not make a duplicate.

## Follow-up (one per person, ever)
Due 5 to 10 days after the user sent the first message (the tracker's `follow-ups` lists who). Two sentences with the greeting, a light reference to the first note, one new detail or a graceful one-liner, an easy out, and the signature. After writing it, record it (see `phases/updates.md`).

## Reply to someone who answered
Answer what they actually said in 2 to 5 sentences, offer one simple next step, and never accept a time, deadline, or commitment for the user. Flag anything only the user can answer.

## Timing line
End the outreach block with: "Best send time: Tuesday to Thursday, 8 to 10am their time."
<!-- skill-version: 2026-10-15 -->
