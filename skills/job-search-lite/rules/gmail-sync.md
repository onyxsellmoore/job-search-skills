# Gmail sync (only when the Gmail connector is on)
Loaded by: daily run, step 1 (automatic), and "check my email". Drafts only: never call a send, reply, or forward tool. Budget: at most 5 Gmail searches per sync. Never quote more than one line of anyone's email in the chat.

Every tracker call below: `python3 <skill>/scripts/tracker_ops.py --path <tracker> --prefs <ws>/prefs.json <command>`. Read the contacts and jobs sheets with openpyxl to get ids, emails, `gmail_draft_id`, `sent_date`, status.

## 1. What got sent
For contacts at status `drafted` that have an email: one Gmail search of sent mail to those addresses in the last 21 days (combine addresses with OR). Each one found: `update-contact --id <id> --status sent --sent-date <date it was sent> --gmail-thread-id <thread id>`. A draft that is still unsent after 7 days: mention it once ("Your email to Priya at Acme is still in drafts").

## 2. Bounces and "no longer here" replies
One search over the last 21 days covering both kinds: delivery failures (from mailer-daemon or postmaster; subjects like "Delivery Status Notification", "Undeliverable", "Address not found") and automatic replies saying the person left ("no longer with", "no longer at", "has left", "no longer employed", "is no longer"). Match each to a contact by address. Then:
- **Person left** (an automatic reply from the company's domain saying they are gone, or a bounce whose text says so): the address format worked; the person is out of date.
  1. `update-contact --id <id> --response-summary "left company"` (stops follow-ups to them).
  2. Save the format as confirmed in `<ws>/profile/email_patterns.json`: `{"<domain>": {"pattern": "first.last", "evidence": "confirmed by auto-reply <date>"}}`.
  3. Find one replacement person at the same company with `rules/contacts.md` (skip anyone already in the contacts sheet), build their address with the confirmed format, draft the same email adapted to them, and record them as a new contact the same way as `phases/daily-run.md` step 8, item 5. If no replacement turns up, say so and suggest the company's LinkedIn page instead.
- **Address not found** (a bounce that does not say the person left): the format may be wrong. If `<ws>/profile/bounces.json` has a `fallback` for this contact not yet in `tried`, and the domain has no confirmed format in `email_patterns.json`: draft the same email to the fallback, then `update-contact --id <id> --email <fallback> --status drafted --gmail-draft-id <new draft id>` and add it to `tried`. Otherwise `update-contact --id <id> --response-summary "bounced: <address>"` and suggest a LinkedIn message.
- One retry per person, one replacement per company per sync.

## 3. Replies, rejections, interviews
Up to 2 searches over the last 14 days: messages from tracked contacts' addresses or names, and messages from tracked companies' domains or applicant systems (greenhouse, lever, ashby, workday, smartrecruiters) containing words such as "unfortunately", "not moving forward", "other candidates", "interview", "schedule", "next steps".
- A contact replied: `update-contact --id <id> --status replied --response-summary "<one line>"`; write a reply draft (`rules/outreach.md`, "Reply"), threaded with `replyToMessageId`.
- Rejection (automatic, this is the rejection tracker): match the email to a tracked job by company (sender domain, company name, or applicant-system sender naming the company) and, when the company has more than one tracked job, by the role title in the email. A clear match at status applied, interview, or packet_ready: `update-job --id <id> --status rejected --review-notes "rejection email <date>"`. Also put the email in a Gmail label `Job Search/Rejected` when label tools exist (create the label once if missing). Skip jobs already at rejected. No clear job match: list it and ask.
- Interview request: `update-job --id <id> --status interview`. Never accept a time for the user; say they need to answer it.
- Interview cancelled or paused: `update-job --id <id> --status interview_cancelled --cancellation-reason "<their reason, if stated>"`, then one short recovery note as a reply draft (2 or 3 sentences: sorry it paused, still interested if it reopens, easy close), and `update-contact --id <contact id> --cancellation-note-draft-id <draft id>` when there is a contact.
- Unclear messages: list them and ask; change nothing.
Report every tracker change in one line each so the user can say "that's wrong" and you undo it.

## 4. Follow-ups due
`follow-ups` lists contacts 5 to 10 days after sending with no reply. For each: write the follow-up (`rules/outreach.md`), create it as a reply draft on the original thread (`replyToMessageId` = the sent message), then `update-contact --id <id> --followup-draft-id <draft id>`. Tell the user the follow-ups are in their drafts.
<!-- skill-version: 2026-10-15 -->
