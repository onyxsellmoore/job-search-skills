# Finding the person and their email (best effort, no browser)
Loaded by: daily run, step 8. Budget: at most 3 searches and 2 fetches per pick. Never fetch linkedin.com pages; read names and titles from search result titles and snippets only.

## 1. Who (pick one person per company, in the order of `rules/outreach.md`)
Searches, stopping as soon as you have a good name:
1. `site:linkedin.com/in "<Company>" ("sales development manager" OR "SDR manager" OR "BDR manager")` for sales roles; `site:linkedin.com/in "<Company>" ("marketing manager" OR "head of marketing" OR "director of marketing")` for marketing roles. Use the team or manager named in the posting when there is one.
2. `site:linkedin.com/in "<Company>" (recruiter OR "talent acquisition" OR "talent partner")`
3. The company's own team, about, or leadership page, or a recent press release naming the right person.
Is the person still there? Search results go stale, and people who have left are the usual reason outreach bounces. Keep a person only if the result shows them at this company now (title text like "<title> at <Company>" or "<Company> | <title>"), and drop anyone whose snippet says "former", "ex-", "previously", shows a date range that ended, or names a different current employer. Prefer, in order: the company's own team page or a press release from the last 12 months ("company page"), then a search snippet that shows a recent date or a recent post ("snippet, recent"), then any other matching snippet ("snippet"). Two candidates: take the fresher one. Record: full name, title, the result URL, and that `confidence` value.
No good name after the budget: say so and fall back to the search links in `rules/outreach.md`; still write the LinkedIn note and email with `[First name]`.

## 2. Email address
1. The domain: the company's main website domain (from the posting or careers page), not the applicant system's domain.
   Check `<ws>/profile/email_patterns.json` first: a format confirmed there for this domain is used as `confirmed` with no search.
2. Pattern, from one real example: one search like `"@<domain>" <Company>` or `"<Company>" email format`. A real address on a company page, press release, or blog bio (for example `jane.doe@<domain>`) reveals the pattern. Pattern-listing sites in search results count as weaker evidence.
3. Build the address from the pattern. Patterns in order of how common they are when there is no evidence: `first.last@`, `first@`, `firstlast@`, `flast@`.
4. Label it `confirmed` (seen a real example on the company's own pages), `likely` (pattern site or one indirect example), or `guess` (no evidence; use `first.last@`). Always give one address; never leave it blank because you are unsure.
5. Keep the next most likely pattern as `fallback_email` for a bounce (`rules/gmail-sync.md`).

## 3. Hand-off
Save `<run>/contact_<slug>.json`: `{"name","first_name","title","company","linkedin_url_or_result_url","confidence","email","email_label","fallback_email"}`. Tell the user in one line who it is and how sure you are, for example: "Priya Shah, SDR Manager (found in a search result; check her LinkedIn shows Acme as her current job before sending). Email is a guess: priya.shah@acme.com."
<!-- skill-version: 2026-10-15 -->
