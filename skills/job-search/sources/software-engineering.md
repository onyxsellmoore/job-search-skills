# Software engineering sources

Read together with core.md (time window, location filter, dedupe, URL priority all apply). Values come from the resolved preferences JSON: target_titles, levels, locations, comp_floor, excluded_companies, dealbreaker_keywords, direct_career_pages, extra_sources.

## Level mapping (use preferences.levels)
Search and filter by the user's levels, and also by the level-coded titles that omit the obvious word. Common ladders:
- Junior: Software Engineer I, Associate Software Engineer, New Grad, Entry Level, Engineer 1, L3/E3/IC1.
- Mid: Software Engineer, Software Engineer II, Engineer 2, L4/E4/IC2.
- Senior: Senior Software Engineer, Software Engineer III, L5/E5/IC3.
- Staff: Staff Engineer, Senior Staff, Tech Lead, L6/E6/IC5, and at AI labs and some startups "Member of Technical Staff".
- Principal: Principal Engineer, Distinguished Engineer, Fellow, L7+/IC6+.
Company ladders differ; when a title is ambiguous (Founding Engineer, Applied or Platform Engineer, Lead Engineer, Engineer II at a large company), judge by the responsibilities and posted comp, and keep it for scoring rather than dropping. Drop titles outside the user's levels and any matching title_exclude_keywords (typically management titles when the user wants IC).

## Must-run extras
- Levels.fyi Jobs `https://www.levels.fyi/jobs`: open without login. Filters seen: Location, Title, Level, Total Comp, Remote, Date Posted. Use the posted comp band to fill comp fields instead of guessing, and compare to comp_floor. The Apply button was seen pointing at a LinkedIn posting (verify on first run); look for the company link before queuing it.

## Rotating (one per run, per core.md rotation rule)
- YC Work at a Startup `https://www.workatastartup.com/jobs`: filter by role (engineering) and location; apply may need a YC profile (verify on first run). Good for early and growth-stage startups.
- Hacker News "Who is hiring?": monthly thread by user whoishiring, posted near the 1st. Scan comments for tags matching the user's metros and remote terms ((Remote), (US), (NYC), etc.) plus target titles. Low volume, high signal, apply by email or company page. Only worth running in the first weeks of the month; the site may block automated fetchers, use the browser.
- Lenny's Jobs (TrueUp-powered) `https://lenny.trueup.io`: product, growth and AI-leaning tech roles at Series A+ companies; browse without account (verify filters on first run). Best when the user targets AI startups.
- VC portfolio job boards: many funds publish a Getro or Consider powered board (for example a16z at portfolio.a16z.com/jobs, others found by searching "<fund> portfolio jobs"). Concentrates well-funded companies; filter to remote or target metros. Per-board status unverified (verify on first run).
- Built In NYC tech `https://www.builtinnyc.com/jobs` (or the user's city site): use the Job Category engineering filters, Remote/Hybrid, Experience; no date filter, rely on "New Jobs". Use the city site that matches locations.metros.
- Ashby and Greenhouse boards via Google site: search is in core.md; in this pack use it with level words, e.g. `site:jobs.ashbyhq.com "<level> engineer" <location word>`.

## Tactics
- Many startups post on Ashby or Greenhouse before cross-posting, so ATS site: searches find roles early.
- Comp: if comp_floor is set and no comp is posted, keep as [comp unknown] for scoring; do not drop. Use Levels.fyi bands when available.
- Respect dealbreaker_keywords (specific tech, domains) at collection time using title and visible card text.
- Prefer well-funded or established employers when the user's comp_floor is high; very early seed-stage postings often fail comp gates.
- Remote-first postings often hide a metro preference in the body; apply the hidden metro preference rule from core.md.

## Skip
Remote OK and We Work Remotely: live but low yield for location-targeted searches; only add if the user is remote-only. Welcome to the Jungle (formerly Otta): no US listings seen in research. Glassdoor: merged into Indeed, use for company research only.
<!-- skill-version: 2026-10-13 -->
