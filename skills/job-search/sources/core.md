# Core search sources (all functions)

You get the resolved preferences JSON. Read from it: target_titles, title_exclude_keywords, levels, locations, freshness_days, comp_floor, excluded_companies, dealbreaker_keywords, direct_career_pages, extra_sources. Never hardcode a title, city or company. Use the user's real Chrome session, pace slowly, and stop a source if it shows a CAPTCHA or login wall (note it in your report, move on).

## Run order
Must-run every run: LinkedIn, Hiring.cafe, Google Jobs plus ATS site: search, direct_career_pages (if any). Then ONE rotating source (below). Also run any extra_sources the user listed.

## Time window (gap-aware)
Default window is 3 days (LinkedIn `f_TPR=r259200`), never 24h, so weekends and skipped days are not lost. If the last logged run (daily_runs) was more than 1 day ago, widen to 7 days (`f_TPR=r604800`). Tracker dedupe makes a wider window nearly free. On sources with other date controls, pick the closest option. Drop any posting older than freshness_days.

## Card-level location filter
Targets are locations.metros (plus metro_aliases) and, if locations.remote is "us", fully remote US.
- Hybrid or On-site tag in a non-target metro: drop at collection. A "remote-friendly" label never overrides that tag.
- Remote tag next to a non-target HQ city: keep for scoring; confirm on click-through. A false drop is invisible, a false keep gets caught at scoring.
- Target metro on the company's own careers page: keep, no extra check.
- Target metro on an aggregator card: keep for scoring, but the real ATS listing must confirm location and arrangement before the role becomes a final pick. Aggregator cards can show a location option the real posting lacks.
- Multi-office postings that include a target metro ("NYC, SF, or Austin") pass as normal keeps.
- Hidden metro preference: a posting labeled Remote or Remote-US whose own text narrows it to a non-target metro or short list of metros ("candidates based in or near X", residency requirement, stated hiring preference) is dropped at collection, not passed to scoring. Read the listing text, not just the label, and re-check the live ATS form when it asks a residency question.
- Also drop at collection: excluded_companies, title_exclude_keywords hits, dealbreaker_keywords in title or visible text, titles clearly outside levels.

## Cross-source dedupe (before scoring and the one-role-per-company cap)
Normalize: lowercase, strip punctuation and parentheticals, collapse "software engineer"/"swe"/"engineer" style synonyms to one token, move seniority words (taken from levels) into a separate level field. Match on (company, core title, level). Keep the best URL, list the others as alt_urls.
Canonical URL priority: 1 company careers page; 2 ATS direct-apply link (Greenhouse, Ashby, Lever, Workday, via Hiring.cafe or search); 3 Wellfound or YC; 4 LinkedIn (last resort, downrank risk). If a role is found only on an aggregator, spend a minute looking for the company ATS link before queuing the aggregator one.

## 1. LinkedIn Jobs (must-run)
Biggest pool. Prefer applying on the company page when both exist.
Base: `https://www.linkedin.com/jobs/search/?keywords=<title>&location=<place>&f_TPR=r<seconds>&sortBy=R`
- URL-encode spaces as %20 and commas as %2C. Location examples: `United%20States`, `Columbus%2C%20Ohio%2C%20United%20States`.
- Use `sortBy=R` (relevance); `sortBy=DD` returned irrelevant results (seen Sep 2026). Freshness comes from the posted-date filter (`f_TPR`). LinkedIn announced the retirement of classic job search starting Sep 2026: on the first run verify the URL still behaves, else use the Filters panel and copy its URL.
- Remote pass: location=United States plus `&f_WT=2`. Only when locations.remote is "us".
- Metro pass, one per entry in locations.metros: do NOT add f_WT, so hybrid and onsite roles in the target metro stay in. Never put f_WT=2 on a metro search.
- Metro results can include neighboring towns: keep only places matching metros or metro_aliases.
- One search per target title (and per synonym or level-coded variant that omits the level word, since titles differ by company). Page one or two of results is enough.
- Experience-level and other filters: use the Filters panel in the UI; copy the resulting URL params rather than guessing them.
- Scan the results list (title, company, location, posted, salary if shown); open a card only if it passes the filters above.

## 2. Hiring.cafe (must-run)
Open, no login to browse. Indexes company ATS boards, so fewer ghost posts and usually a direct-apply link. `https://hiringcafe.com/` (hiring.cafe redirects there). Filter by department/title and level from preferences, location from locations, and the Date Posted filter to the time window. Do NOT apply a comp filter (many feeds carry no comp and it silently drops roles scoring would keep). Open the job and use the company ATS link as canonical (verify on first run that the link goes out to the employer).

## 3. Google Jobs plus ATS site: search (must-run)
Search `<title> jobs <location>` and open the jobs panel; use its date filter. It surfaces direct employer links. For direct ATS boards, search Google with `site:jobs.ashbyhq.com`, `site:boards.greenhouse.io` (also `job-boards.greenhouse.io`), `site:jobs.lever.co` plus the title and a location word. Expect CAPTCHA risk; if hit, skip.

## 4. Direct career pages (must-run when listed)
For each entry in direct_career_pages: open url, search each target title, keep only results matching location rules. Batch through them; this bypasses ATS downranking. If the list is empty, skip.

## 5. Rotating sources (one per run)
Pick ONE, the least recently used. Least recently used = the oldest (or never) `rotating_source_used` in `<ws>/runs/*/search_B.json`. Record the pick as `rotating_source_used` in your search file. Pool:
- Indeed: `https://www.indeed.com`; filters for date posted, remote, experience, pay; reCAPTCHA risk.
- Built In (national or city site, e.g. builtin.com/jobs): tech-company roles, filters for Remote/Hybrid, category, experience; no date filter, use "New Jobs".
- The Muse: `https://www.themuse.com/search`; Date Posted (7/14/30 days), Experience Level, Remote/Flexible, Category; "Apply On Company Site".
- Wellfound: `https://wellfound.com/jobs`; startup-heavy, title plus location; full search may need login (verify on first run).
Add function-specific rotating sources from the function pack.

## Time budget
Per source about 3 minutes (LinkedIn, Hiring.cafe), 4 for career pages, 2 for Google/ATS and the rotating source. Whole search phase 10 to 15 minutes. Stop a source at budget even if more pages remain.

## Output
For every kept card: title, company, location text, arrangement, posted date, salary if shown, canonical URL, alt_urls, source. Note sources skipped and why.
<!-- skill-version: 2026-10-13 -->
