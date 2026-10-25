Loaded by: pre-fill agent (browser), strictly sequential, one role at a time in rank order, never overlapping another browser agent. Orchestrator spawns it with model prefs.models.prefill (default sonnet).
Reads: this file; rules/forms.md; <ws>/profile/eeo.json (if present); <run>/prefs.json (identity block); <run>/brief_<slug>.json; <run>/rolectx_<slug>.json; <run>/report_<slug>.json; <run>/essays_<slug>.md.
Writes: rewrites <run>/report_<slug>.json in place (never a second file). Chat digest <= 10 lines. Never submits.
Params: date, skill, ws, run, role slug; `mode` and `ws_device` come from `<run>/orient.json`.
Decide only from the files you are given (tracker, profile, prefs, run files). Anything you know from other context (memory, past chats) may go into flags, never into drops, scores or text.

Drafts no new prose. Typing and selecting, not deciding.

## Preflight
- FIRST load the Chrome tools with one ToolSearch (`select:` the claude-in-chrome tabs, navigate, find, form_input, file_upload, javascript_tool tools you need). Only if it finds none or Chrome is unreachable: change nothing, return the single flag `browser_not_connected` (the orchestrator stops the run), and say pre-fill did not happen.
- Use the user's Chrome only (rules/forms.md). Never the in-app browser pane; work there is lost when it closes.
- Role skipped by the orchestrator (disqualifying or heavy, so no `report_<slug>.json`): do nothing.

## Steps
1. Create your own tab with `tabs_create_mcp` and open the apply URL in it. Work only in that tab and never touch any other tab. Re-locate every field with `find`; nothing from recon survives. Check for a Greenhouse iframe first (rules/forms.md). Never `read_page` a Workday form.
2. Direct-map fields from `prefs.identity` and prefs: full_name, phone, linkedin_url, current_employer, current_title, years_experience (a number, or "less than 1" for early-career), how-did-you-hear (a true source). An empty identity value: leave the field blank and list it in `review_notes`.
3. Email: prefs.application_email only. Never any other account, including the Claude login or system email.
4. Resume: upload `brief.resume_path` using the file_upload path rule in rules/forms.md. Confirm the filename shows on the page.
5. Cover letter: if `form.cover_letter_field` is true, upload or paste from `report.cover_letter_path`. If the live form shows a cover-letter field recon missed, or lacks one recon found, flag the mismatch and do not improvise.
6. Essays: for each live prompt, paste the answer under the matching `### <field_label>` in essays_<slug>.md. A live prompt with no match, or an answer marked `NEEDS USER`: leave it empty and flag it. Check character limits before pasting; if an answer exceeds one, flag it and paste nothing.
7. Location (honest, every field): prefs.locations.current_city. If only metros are offered, pick the metro containing it. Never enter the relocation target as the current city. Relocation or work-location questions: answer per prefs (relocating on own, no assistance requested, if that is what prefs say). Street address demanded and not in the profile: leave blank and flag.
8. Work authorization and sponsorship: from prefs.work_authorization.
9. Desired salary: leave blank if allowed. If a number is required, use the market band for that company and level, never prefs.comp_floor. Free text: "targeting market rate for this level".
10. EEO and voluntary self-ID: answer accurately from <ws>/profile/eeo.json; never choose decline unless the file says so. No eeo.json, a missing key, or an unlisted question: leave it unanswered if allowed and list it in `review_notes`.
11. Dropdowns (react-select on Greenhouse especially): use the coordinate-click method and the javascript_tool verification pass in rules/forms.md; never trust `form_input` success on a dropdown.
12. Stop on the review step. Do not click Submit, and do not click "Review" or "Next" if it might submit. Leave your own tab open for the user's review (the one exception to closing your tab). If the tab will not open or fill, record the failure; the apply URL is the fallback.

## Report: update <run>/report_<slug>.json in place
Read it, merge, rewrite whole. Add:
```
"prefill":{"status":"filled|partial|failed","tab_note":""},
"tracker":{"status":"drafted|packet_ready","drafted_date":"YYYY-MM-DD","cover_letter":"<keep>",
           "review_notes":"<what the user must check>","tab_info":"<how to find the tab, plus apply URL>"}
```
`tracker.status` is `drafted` only when `prefill.status` is `filled` or `partial`; when `failed` keep `packet_ready` and put the apply URL in `tab_info`. Append new flags to the existing array.

`review_notes` lists exactly: fields left blank (and why), unanswered EEO items, dropdown choices worth a second look, salary handling, any recon-versus-live mismatch, anything needing a street address or login. Terse and specific.

## Digest (chat, <= 10 lines)
status, prefill status, count of items in review_notes, flags, report path. No form dumps.
<!-- skill-version: 2026-10-13 -->
