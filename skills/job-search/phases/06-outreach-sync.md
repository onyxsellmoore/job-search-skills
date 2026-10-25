# Phase 06: Outreach sync (Gmail drafts, draft-only)
Loaded by: the orchestrator's last step as a subagent (model prefs.models.draft), or directly when the user asks to sync outreach or check replies.
Reads: `<run>/prefs.json` (identity block), `rules/voice.md` and `rules/outreach.md` (only before writing a reply, follow-up, or cancellation note), `<ws>/outreach/outreach_<date>.md` files named by `draft_ref`. Skill files are relative to `<skill>`.
Writes: Gmail drafts, tracker updates via `tracker_ops.py`, `<run>/report_outreach_sync.json`. Never marks run_state.
Params: date, skill, ws, run (local paths; you never call device tools, the orchestrator syncs).
Decide only from the files you are given (tracker, profile, prefs, run files). Anything you know from other context (memory, past chats) may go into flags, never into drops, scores or text.

## Guardrails (read first)
1. Never send, delete, trash, or spam-mark anything. If asked to send, say this phase is draft-only and the user sends from Gmail.
2. Gmail tools allowed: create_draft, get_draft, list_drafts, get_thread, search_threads, list_labels, create_label, label_thread, and update_draft only per Draft hazards. Nothing else.
3. Account: `prefs.gmail_account` is the only mailbox. If empty, stop and flag. Never fall back to any other account.
4. Scope: only threads with tracked contact addresses or drafts this phase created. Never read other mail. Quote at most one line of a reply.
5. Never mark a contact `sent` or `replied` without thread evidence from search_threads or get_thread.
6. Reply and follow-up drafts commit the user to nothing (no time slot, deadline, or accepted request). If a reply asks them to pick a time or answer a substantive question, draft around it and flag it.
7. Every email has a greeting line (`Hi <First name>,`) and a signature block (`Best,`, `prefs.identity.full_name`, literal full `prefs.identity.linkedin_url`). Text carried from an outreach file is synced verbatim; never reconstruct a draft from memory.
8. As a subagent, never ask the user anything; put questions in `flags`.

## Step 0: Preconditions
1. The tracker is `<tracker>` = `<ws>/application_tracker.xlsx`. If `<run>/prefs.json` is missing (direct run), `mkdir -p <run>` with `<run>` = `<ws>/runs/<date>`, then `python3 <skill>/scripts/profile_check.py --workspace <ws> --print-prefs > <run>/prefs.json`. The outreach files named by `draft_ref` are under `<ws>/outreach/`.
2. Every tracker call: `python3 <skill>/scripts/tracker_ops.py --path <tracker> --prefs <run>/prefs.json <command> ...`. Never omit `--path`; never glob for a workspace. Writes go through `update-contact` and `update-job` only, never by hand. Two failures: stop and report.
3. Load the Gmail tools (ToolSearch "gmail draft thread"). If absent or unauthenticated, go to Fallback.
4. Account check: `search_threads` with `from:<prefs.gmail_account> in:sent`, 1 result; judge from the result metadata only (account, sender), never open a message body. If the mailbox is not that account, STOP, write the report with a flag, do nothing else.
5. Signature values: `prefs.identity.full_name` and `prefs.identity.linkedin_url`. Either empty: use the name alone, flag it.
6. `tracker_ops.py ... contacts-pending` once (read-only): every contact at drafted/sent with email, draft_ref, Gmail ids, day counts.

## Step 1: Sync pending outreach into drafts
Work every contact with status `drafted` and empty `gmail_draft_id`, with no date filter. First route out two kinds:
- `draft_ref` empty, inline text, or pointing at a missing file or anchor: count `legacy_unresolvable`, flag "legacy_unresolvable: <name>, no usable draft_ref", skip.
- No address (tracker `email` empty and no To in the block): leave it in the outreach file, count `no_email`, flag "send via LinkedIn", create no draft.

Age the rest from `first_contacted`:

| Age | Action |
|---|---|
| 0-14 days | Sync. |
| 15-30 days | Sync and list under drafts_created with "synced N days late". |
| 31+ days | Do not sync. Add to `stale_needs_ok` with the draft_ref; the user says "sync it" or "drop it" next time. |

For each synced contact:
1. Open the block via `draft_ref`; take To (the tracker `email` wins if they differ; flag it), Subject, and Body (greeting through signature), not the follow-up section.
2. Dedupe: a `gmail_draft_id` on the row means it exists. Also check list_drafts or search_threads for the same address and subject; if found, record that id and do not create.
3. create_draft with exactly that To, Subject, Body. Pass BOTH `body` (plain text) and an explicit `htmlBody` where the signature URL is a real `<a href>` anchor. Gmail may rewrite that href into a google.com/url redirect (visible text stays clean; not fixable): add one flag line saying so.
4. `update-contact --id N --gmail-draft-id <id>`. Status stays `drafted`.
5. Guessed address: still draft, flag as unconfirmed.

## Step 2: Reconcile sent vs drafted
Reconcile only contacts that have a `gmail_draft_id` or `gmail_thread_id` or an `email`, whatever their age; count the rest (no address, no Gmail id) under `no_email` or `legacy_unresolvable`. search_threads by `to:`/`from:` the address (prefer the subject match; ambiguous means flag).
- Sent found: `update-contact --id N --status sent --sent-date <date of the thread's sent message> --gmail-thread-id <id>`. A `sent` row with empty `sent_date`: fill it the same way when a thread id exists, else flag "sent_date unknown". Never invent a date.
- Still unsent after 7+ days: flag "original never sent, draft still in Gmail". Never draft a follow-up for an unsent original.
- Reply from the contact: first read it for decline language (Step 4). Otherwise `update-contact --id N --status replied --response-summary "<one line>"`, then create a reply draft in the same thread: 2-5 sentences answering their message, one low-pressure next step, per `rules/outreach.md` and `rules/voice.md`.
- User already sent a follow-up manually: record `sent` and set `--followup-draft-id manual`.

## Step 3: Threaded follow-ups (one per contact ever)
Due when status is `sent`, no reply, `followup_draft_id` empty, and day 5-10 since `sent_date`. Day counts follow `sent_date`. Before day 5 wait; day 11-14 age out silently; past day 14, no reply: `update-contact --id N --status ghosted`.
1. Take the follow-up text from the original outreach block; carry it verbatim unless a real, already-known hook exists. Never invent news.
2. Original went to an unconfirmed guessed address with no reply: do not re-hit it; flag "try LinkedIn or another address pattern".
3. Create it as a reply draft on the sent thread (subject `Re: <original>`) with body and htmlBody, then `update-contact --id N --followup-draft-id <id>`.
4. No follow-up for rejected contacts or for an interview that was cancelled (Step 5 covers that).

## Step 4: Verified rejection detection
Channels: a contact reply with clear decline language ("position filled", "moving forward with other candidates"), and ATS mail. For ATS, search `from:` greenhouse.io, lever.co, ashbyhq.com, myworkday.com, icims.com, smartrecruiters.com, and use a result only if its company matches a tracked job row (case-insensitive; newest row if several; flag if ambiguous). If the rejection names a role title that differs from that row's title, do not apply it: flag "confirm: rejection for <title> vs tracked <title>". Unmatched ATS mail is never read or logged. Receipts, invites, and "we will keep your resume on file" are not rejections; flag ambiguous ones, status unchanged.
On clear evidence only:
1. `update-job --id <job id> --status rejected`.
2. If a contact is involved: `update-contact --id N --status rejected --response-summary "<one line>"`.
3. Draft no follow-up. If a follow-up or outreach draft already exists, it is void: list its id under `rejections` so the user does not send it.
4. Label the rejection thread and the original outreach thread `Job Search/Rejected` (create_label if missing, then label_thread). If labeling fails, list it for manual handling.
5. Warm human recruiter rejection: flag "consider moving <name> to the recruiter bench".

## Step 5: Cancelled interviews
For each job row at `interview_cancelled` whose contact has an empty `cancellation_note_draft_id`: find the scheduling contact via `linked_job_ids` and the interview thread via search_threads, then create ONE threaded note using the cancellation template in `rules/outreach.md`, using the row's `cancellation_reason` only if recorded (never guess one). Then `update-contact --id N --cancellation-note-draft-id <id>`. No contact row: flag, do not guess.

## Draft hazards
- Created drafts belong to the user after creation. Re-read (get_draft) immediately before any update; if it differs from what this phase created, the user edited it: never update it.
- update_draft can detach a draft from its thread and cannot clear cc. Prefer creating a fresh threaded draft and flagging the old one. A `gmail_draft_id` that no longer lists means the user handled it: do not recreate.

## Output
Write `<run>/report_outreach_sync.json`: `{"drafts_created":[],"already_existed":[],"stale_needs_ok":[],"follow_ups":[],"replies":[],"rejections":[],"flags":[],"coverage":{"pending":N,"synced":N,"aged":N,"stale":N,"no_email":N,"legacy_unresolvable":N}}`. Entries are one-line strings `Company | Contact | detail`. Chat digest (under 15 lines, empty sections omitted, no thread text): first `Coverage: Pending at start N | Synced N (M aged) | Stale, needs your OK N | No email N | Legacy unresolvable N` (ALWAYS printed), then each section (for `stale_needs_ok` give the count and the 5 oldest; the full list stays in the report file), then: everything above is a draft in <gmail_account>; nothing was sent. Drafts: https://mail.google.com/mail/#drafts.

## Fallback (Gmail unavailable)
Run `tracker_ops.py ... follow-ups` (read-only). Copy each due follow-up from its outreach block into `<ws>/outreach/outreach_<today>.md` under `## Follow-ups due today` (one per contact; note guessed addresses). Never mark `sent` or `replied`. Skip Steps 4 and 5; say so in one line with the reason.

## Edge cases
Nothing pending: say so briefly. Several contacts at one company: act only on the one in the outreach file.
<!-- skill-version: 2026-10-13 -->
