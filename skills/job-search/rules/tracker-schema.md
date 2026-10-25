# Tracker schema (fallback for hand-editing)
Loaded by: orchestrator, only when `<skill>/scripts/tracker_ops.py` fails twice and the xlsx must be edited by hand.
Reads: nothing else. Writes: `application_tracker.xlsx` (minimal edits), then flag it to the user.

Before touching the file: copy it to `application_tracker.backup.<YYYY-MM-DD>.xlsx`. Never delete rows (mark `withdrawn` or `rejected`). Dates are ISO `YYYY-MM-DD`. Append new columns only at the end of a sheet. Edit with openpyxl, never recreate the workbook, and never save a jobs sheet with fewer rows than it had.

## Sheet `jobs` (header order, 24 columns)
`id`, `first_seen`, `last_updated`, `company`, `role_title`, `level`, `location`, `source`, `url`, `alt_urls`, `comp_posted`, `fit_score`, `score_rationale`, `resume_variant`, `status`, `drafted_date`, `submitted_date`, `referral_contact`, `referral_sent_date`, `referral_response`, `review_notes`, `tab_info`, `cover_letter_file`, `cancellation_reason`

- `id`: integer, max existing plus 1.
- `url`: canonical apply URL (fragment, tracking params and trailing slash removed). `alt_urls`: semicolon-separated.
- `fit_score`: number 0-10. `comp_posted`: text, `unknown` if none.
- `resume_variant` / `cover_letter_file`: path relative to the workspace (`tailored/...pdf`); cover letter blank when the form had no field.
- `drafted_date`: when a packet was pre-filled. It does NOT mean the user applied. `submitted_date`: set only when the user actually applied.
- Match an existing role by canonical URL first, then company plus title. Update `alt_urls` instead of adding a duplicate row.

## Sheet `contacts` (18 columns)
`id`, `first_contacted`, `contact_name`, `contact_title`, `company`, `connection_degree` (1st/2nd/cold), `connection_path`, `linkedin_url`, `message_template` (leave blank), `message_draft` (a `draft_ref` like `outreach/outreach_<date>.md#<company-slug>`, never the email text), `status`, `response_summary`, `linked_job_ids` (comma-separated `jobs.id`), `sent_date`, `gmail_draft_id`, `gmail_thread_id`, `followup_draft_id`, `cancellation_note_draft_id`, `email` (address, empty when unknown; older trackers gain this column automatically)

- Contact `status`: drafted, sent, accepted, replied, ghosted, rejected. The Gmail columns are written only by outreach sync.

## Sheet `daily_runs` (7 columns)
`run_date`, `roles_surfaced`, `top_picks_count`, `drafted_count`, `contacts_drafted`, `slow_day` (true when `top_picks_count` is below `picks_per_day`), `notes`. One row per run.

## Job statuses and what they do
| status | exact posting | company |
|---|---|---|
| `surfaced`, `top_pick` | may resurface (reuse its `id`) | not blocked |
| `drafted`, `packet_ready` | suppressed | not blocked |
| `submitted` (alias `applied`), `referral_sent`, `interview`, `interview_scheduled` | suppressed | blocked for the cooldown |
| `rejected`, `no_response`, `withdrawn` (alias `dead`), `interview_cancelled` | suppressed | not blocked |

- Drafting a packet is not applying. Only the blocked row group starts a cooldown.
- Cooldown clock starts at the first set date among `submitted_date`, `referral_sent_date`, `drafted_date`, `first_seen`, `last_updated`. Company is free again on start date plus cooldown days.
- Cooldown days: `prefs.cooldown_days` (default 7). `prefs.cooldown_overrides` gives a company and its aliases one shared clock with its own day count: an application to any member blocks all members.
- `prefs.excluded_companies` are always blocked.
- The `suppress` boolean returned by `seen`, `seen-batch` and `dup-check` is the single source of truth; do not re-derive it from status names.
- Outreach cooldown (`prefs.outreach_cooldown_days`, default 90, `company-cooldown`) gates cold email only. It never blocks an application and is separate from the above.

## Bulk write format
`run.json` = `{"jobs":[...],"contacts":[...],"run_log":{"surfaced","top_picks","drafted","contacts","notes"}}`. A job with `id` updates in place; without `id` it needs `company`, `role`, `url`. Job keys: `status`, `fit`, `rationale`, `resume`, `cover_letter`, `drafted_date`, `submitted_date`, `review_notes`, `tab_info`, `level`, `location`, `source`, `comp_posted`, `alt_urls`. Contact keys mirror the contacts columns (`name`, `company`, `degree`, `job_id`, `draft_ref`, `email`).

## Script quick reference
Every call: `python3 <skill>/scripts/tracker_ops.py --path <tracker> [--prefs <prefs.json>] <command>`.
`init`, `summary`, `seen --url`, `seen-batch`, `dup-check --file`, `blocked-companies`, `company-cooldown --company`, `add-job`, `update-job --id`, `add-contact`, `update-contact --id`, `contacts-pending`, `log-run`, `import-run --file`, `merge-reports --base --dir --out`, `follow-ups`, `funnel`.
Exit codes: 0 ok, 1 item failure, 2 usage or missing file, 3 shrink guard refused a save (stop and tell the user; do not force).
<!-- skill-version: 2026-10-13 -->
