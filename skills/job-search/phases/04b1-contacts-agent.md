Loaded by: contacts/recon agent (browser), one role at a time in rank order. Orchestrator spawns it with model prefs.models.recon (default sonnet). Never overlaps another browser agent.
Reads: this file; rules/outreach.md (channel priority section ONLY, skip the rest); rules/forms.md; <ws>/profile/profile_summary.md; <run>/prefs.json; the role's jd file at `<run>/<jd_path>` (team/company context).
Writes: <run>/rolectx_<slug>.json. Chat digest <= 10 lines. Never writes the tracker, outreach file or report_*.json. Never fills, uploads or submits.
Params: date, skill, ws, run, and the role's row from `<run>/picks.json` (slug, company, title, url, jd_path).
Decide only from the files you are given (tracker, profile, prefs, run files). Anything you know from other context (memory, past chats) may go into flags, never into drops, scores or text.

Inputs: your Params line values. Tracker path is `tracker` in `<run>/orient.json` (read-only use).

## Preflight
FIRST load the Chrome tools with one ToolSearch (`select:` the claude-in-chrome tabs, navigate, find, read_page, get_page_text, javascript_tool tools you need). Only if it finds none or no browser is connected: write nothing, return the single flag `browser_not_connected` (hard stop; the orchestrator stops the run). Never fall back to web search for LinkedIn work and report success.
Tabs: create your own tab first with `tabs_create_mcp`, work only in it (open every page in that tab), close only that tab at the end, never touch other tabs.

## Step 1: referral check (mandatory, every role, before any cold search)
1. In your own LinkedIn tab (the one you created), list the company's current employees filtered to 1st-degree connections. Execute the search; a mental check does not count.
2. Each 1st-degree person goes in `flags` only, as a named question: "You are 1st-degree with <Name> (<title>) at <Company>. Want me to loop them in?" Do not add them to `contacts` and never draft to them.
3. Then continue finding channel contacts. Do not wait on any answer.

## Step 2: contacts (2-3)
- Order comes from rules/outreach.md channel priority and prefs.outreach.contact_targets if set. Referral path first, then the order given there.
- Record identity only: name, title, linkedin_url, channel, relationship ("1st"|"2nd"|"none"), priority (1 = best). No email field; the draft agent finds patterns.
- `mutual`: always null. A 2nd-degree badge is not confirmation the user knows anyone. If a mutual looks like a strong hook, put it in `flags` as a question and leave `mutual` null.
- LinkedIn gated or rate-limited: fall back to the company team page, GitHub org members, conference or speaker bios. Nobody found: empty `contacts` plus flag "contacts not found, LinkedIn gated". This never blocks the packet.

## Step 3: form recon (read only)
1. Open the apply URL in your own tab. If it is a LinkedIn Easy Apply and a company careers URL exists, use the careers URL.
2. Map with `find` first (rules/forms.md has platform traps: Greenhouse iframes, Workday never `read_page`). Fall back to `get_page_text` only when `find` cannot resolve the form.
3. Record:
   - `ats` (greenhouse, lever, ashby, workday, smartrecruiters, icims, custom, other)
   - `cover_letter_field`: true only for a dedicated upload or text field (required or optional). An "Additional information" box is not one.
   - `essay_prompts`: every free-text prompt, VERBATIM, as objects `{"field_label","prompt_text","limit"}` (limit null if none shown). `field_label` is the exact on-page label, unique per prompt.
   - `heavy`: true when the form needs 6+ essays, a video intro, a take-home to apply, or 3+ references. Say which in `notes`. Stop mapping further. The orchestrator marks the role skipped (no draft, no pre-fill), keeps its tracker status, and flags it to the user with `notes`.
4. Do not type into, select in, upload to or click Submit on anything. Close your tab when done.

## Step 4: residency and location gating (hard stop)
While mapping, check for a residency or location question, or a location field whose options are restricted to places outside prefs.locations (metros, metro_aliases, and "remote" if the user accepts it). The live form overrides the JD and any aggregator text, including listings marketed as remote.
- Gating found: set `form.disqualifying` true and `form.disqualifying_reason` to the exact field text and the offered options. Stop mapping, write the file, return `disqualifying: true`. The orchestrator marks the role skipped for steps 04b2 and 04b3 and `dead` in the tracker; you do nothing else.
- Multi-office listings that include a target metro are fine. Only gating that excludes every target location counts.
- Not gating: write `disqualifying` false and an empty reason.

## Output: <run>/rolectx_<slug>.json
```
{"contacts":[{"name","title","linkedin_url","channel","relationship","mutual":null,"priority":1}],
 "form":{"ats","apply_url","cover_letter_field":false,"essay_prompts":[],"disqualifying":false,
         "disqualifying_reason":"","heavy":false,"notes":""},
 "flags":[]}
```
Every JSON artifact carries `flags` for questions you could not ask. Never ask the user directly.

## Digest (chat, <= 10 lines)
company, contacts count, referral flags (names only), cover_letter_field yes/no, essay prompt count, heavy yes/no, `disqualifying` true/false, rolectx path. No page text.
<!-- skill-version: 2026-10-13 -->
