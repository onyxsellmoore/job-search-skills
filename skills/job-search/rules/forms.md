# Forms: ATS notes, uploads, flagging, EEO, location
Loaded by: contacts agent (04b1) and pre-fill agent (04b3). Recon maps only; pre-fill fills. Neither submits.

## Browser rules
- Use the user's Chrome tools (load via ToolSearch if deferred): navigate, tabs_create_mcp, find, form_input, file_upload, get_page_text, javascript_tool. Avoid `computer` pixel clicking.
- Never use the in-app browser pane for pre-fill. Work there is lost when the pane closes. Not connected: hard stop, ask the orchestrator to have the user connect it.
- Map with `find` first; `get_page_text` or `read_page` only when `find` cannot resolve the form. Never `read_page` a Workday form.
- Browser agents never overlap. One role at a time.
- Never click Submit. Never click "Review" or "Next" if it might submit.
- Chrome unreachable during pre-fill: stop, record the intended field values in `review_notes`, and say plainly that pre-fill did not happen.

## ATS platforms
| Platform | Notes |
|---|---|
| Greenhouse (boards.greenhouse.io, job-boards.greenhouse.io) | Top-level job-boards.greenhouse.io forms pre-fill fine; click Apply first, because fields are absent from the accessibility tree until then. A form embedded in a cross-origin iframe on the company's own domain cannot be filled (keystrokes do not land): flag it and give the user the direct apply URL. react-select dropdowns: see Dropdowns below. Textarea essays, "Submit Application" button. |
| Lever (jobs.lever.co) | Single page, similar to Greenhouse. Custom questions appear under "Additional information". Resume upload is a plain file input. |
| Ashby (jobs.ashbyhq.com) | Modern single page. Video intro questions are common: record `heavy` true and stop. Location can be a restricted typeahead, which is a residency-gating check. |
| Workday | Multi-page, per-company account walls. Never `read_page`; use `find` per section. If account creation or sign-in is required, prefer the "Apply Manually" path if offered; do not create accounts or enter passwords. Recon records `ats: workday` and `notes: account wall` and stops. Pre-fill that cannot finish in one session fills what it can, notes the URL and the page reached, and flags. |
| SmartRecruiters | Single page with a profile-style section; resume upload can auto-parse and overwrite fields, so re-check every field after upload. |
| iCIMS | Often an account wall or multi-step with a resume parser. Same handling as Workday: no account creation, flag, record the URL. |
| Company-specific | Custom forms: read carefully, use `find`, flag oddities. |
| LinkedIn Easy Apply | Prefer the company careers URL when one exists. |

## Dropdowns (react-select)
- They silently reject `form_input`, and `form_input` still reports success. What works: screenshot, coordinate click on the dropdown box, coordinate click on the option (the only allowed use of the pixel `computer` tool).
- After filling any Greenhouse form, verify with a `javascript_tool` read of every input value and every react-select `singleValue` div. Never trust `form_input`'s success message on a dropdown.

## File upload mechanics
- `file_upload` needs a path the extension can read, not a path on the user's computer. Use a container path under `/mnt/user-data/uploads/`. Local-mount mode: the local `<ws>/tailored/...` path works if it is under that tree; otherwise stage it. Stage only when the PDF is not already under `/mnt/user-data/uploads/`. Device mode: sync-back commits the PDF to `<ws-device>/tailored/` first, then `device_stage_files` it from there and pass the returned `/mnt/user-data/uploads/...` path.
- After upload, confirm the filename appears on the page. Auto-parsing ATSs may overwrite fields: re-check them.
- Upload only the tailored resume and, when the field exists, the cover letter. Nothing else.

## When to flag instead of draft
Record `heavy` true in recon and stop the role's packet (the orchestrator flags it to the user, who decides) when the form needs any of:
- a video intro
- 6 or more long-form essays
- a take-home required to apply
- 3 or more references
Also flag, rather than ship a generic version, when a required cover letter cannot be written truthfully from the profile.

## Cover letter field
Real only if there is a dedicated upload or text field (required or optional). An "Additional information" or "Anything else" box does not count.

## Location and residency
- Honest at every stage: application location fields, address, background-check and verification fields use prefs.locations.current_city. If only metros are offered, pick the metro containing it. Never enter the relocation target as the current city.
- Relocation or work-location questions: answer per prefs. Never request relocation assistance unless prefs say so.
- Street address required and not in the profile: leave for the user and flag.
- Recon gating rule: a live form that asks a residency question or restricts a location field to places outside prefs.locations (metros, aliases, accepted remote) is a hard disqualifier (`form.disqualifying` true with the exact field text). The form overrides the JD and aggregator text. This is not a judgment call for the user. A multi-office form that includes a target metro is fine.

## Standing answers
- Work authorization and sponsorship: prefs.work_authorization.
- Desired salary: leave blank if allowed. If required, the market band for that company and level, never comp_floor. Free text: "targeting market rate for this level".
- Years of experience: profile number, or "less than 1".
- How did you hear: a true source ("LinkedIn", the real board).
- Email: prefs.application_email only, never the Claude login or any other account.

## EEO and voluntary self-ID
- Source of truth is profile/eeo.json. Select the stored answer for each matching field (race or ethnicity, gender, veteran, disability, Hispanic or Latino, sexual orientation, transgender, pronouns, other_fields).
- Never default to "decline" or "prefer not to say". Choose it only when the file's value is itself a decline.
- Choose the dropdown option that matches the stored meaning, even when worded differently. If no option matches, leave it and flag.
- No eeo.json, a key missing, or a question the file does not cover: leave it unanswered if the form allows, list it in `review_notes`, and never guess.
- Never print EEO values in chat, flags, digests or review_notes; name only the field ("transgender status left blank").
<!-- skill-version: 2026-10-13 -->
