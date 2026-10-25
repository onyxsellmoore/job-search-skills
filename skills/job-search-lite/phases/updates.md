# Tracker updates
Reads: `<tracker>`, `<ws>/prefs.json`. Writes: `<tracker>`, then the workbook in `<out>`.

Find the job first: tracker `summary` and, if needed, open the jobs sheet with openpyxl and match company and title. More than one match: ask which. No match for an application the user made outside the skill: `add-job` it with the URL they give (ask for it), then update.

| The user says | Command |
|---|---|
| I applied to X | `update-job --id <id> --status applied --submitted-date <date they applied, default today>` |
| X rejected me | `update-job --id <id> --status rejected` |
| Interview with X | `update-job --id <id> --status interview` (add their notes with `--review-notes`) |
| I am not applying to X / it closed | `update-job --id <id> --status withdrawn` |
| I messaged <name>, <title> at X | `add-contact --name "<name>" --title "<title>" --company "<X>" --degree cold --linkedin "<url if given>" --status sent --job-id <id>` (it prints the new contact `id`), then `update-contact --id <that id> --sent-date <date sent>`. Use `--degree 1st` and status as given if they already know the person. |
| <name> replied | `update-contact --id <id> --status replied --response-summary "<one line>"`; offer a reply draft per `rules/outreach.md` |
| Draft my follow-up to <name> | Write it per `rules/outreach.md` (follow-up section); with the Gmail connector, save it as a draft ("Gmail drafts" in `rules/outreach.md`). Then `update-contact --id <id> --followup-draft-id "chat-<date>"` so it is not offered again |
| Show my tracker | `summary` and `funnel`, as 4 to 6 plain lines; no tables of every row |

## Check email (Gmail connector only)
Run `rules/gmail-sync.md` and report its one-line results. No Gmail tools: say how to connect Gmail (Customize > Connectors) in one line.

After any change, pack the workbook (SKILL.md, "End of every chat") and tell the user what changed in one line.
<!-- skill-version: 2026-10-15 -->
