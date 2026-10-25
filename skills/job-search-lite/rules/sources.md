# Finding roles with web search (no browser)
Reads: `<ws>/prefs.json` (target_titles, title_exclude_keywords, levels, locations, freshness_days, comp_floor, excluded_companies, dealbreaker_keywords, direct_career_pages, extra_sources).

You have web search and web fetch, not a browser. LinkedIn and most job boards block reading, so aim searches at pages that can be read: company application pages (Greenhouse, Lever, Ashby, Workable, SmartRecruiters), company career pages, and boards that serve plain pages (Built In, The Muse).

## Budget per run
At most 8 searches and 8 fetches in total. Stop early once you have 3 to 5 strong candidates. A source that refuses or shows a login wall: note it, move on, never retry it this run.

## Window
Prefer postings from the last 7 days; widen to `prefs.freshness_days` (default 14) when the last run was more than 3 days ago or this is the first run. A posting with no visible date may be kept only if its page loads with an active apply button; tag it `[date unknown]`.

## Searches (in this order, until the budget or enough candidates)
Use the first 2 or 3 `target_titles`, quoted. `<place>` = each entry in `locations.metros`; add one remote pass when `locations.remote` is "us".
1. Application pages: `"<title>" <place> site:job-boards.greenhouse.io OR site:boards.greenhouse.io OR site:jobs.lever.co OR site:jobs.ashbyhq.com`
2. Remote pass (only if remote is allowed): `"<title>" remote United States entry level site:jobs.lever.co OR site:job-boards.greenhouse.io OR site:jobs.ashbyhq.com`
3. Built In: `"<title>" entry level <place> site:builtin.com` (city sites such as builtinnyc.com or builtinchicago.org also count)
4. General: `"<title>" entry level jobs <place> posted this week`
5. Each URL in `direct_career_pages`, then each entry in `extra_sources`.
Sales users can add "SDR" or "BDR" as the title term; marketing users "marketing coordinator". Search the user's own titles first.

## Reading a result
- Fetch only URLs that came from a search result or that the user gave. If a fetch of a URL you built is refused, do not retry it.
- Prefer the company's own application page as the canonical URL. A result on a board: spend at most one search looking for the company's application page; otherwise keep the board URL.
- Save a short excerpt (requirements and location lines, under 1,500 characters) as `jd_excerpt`; fetch the full text later only for finalists.

## Drop at collection
- Location: in-person or hybrid outside `locations.metros` (and aliases). "Remote" that the text narrows to a non-target city or state ("must be based in", "residents of"). Remote when `locations.remote` is not "us".
- Level: titles with a `title_exclude_keywords` word; postings asking for 3 or more years of experience.
- Pay and scams: commission-only, "100% commission", "unlimited earning potential" with no base, unpaid, pay-to-start, multi-level marketing, door to door, canvassing, "be your own boss".
- Staffing-agency posts that do not name the employer.
- `excluded_companies`, `dealbreaker_keywords`.
- Older than the window.

Pay note: early sales jobs pay base plus commission (OTE). Record base and OTE separately in `comp`. Compare to `comp_floor` using base when `comp_floor.basis` is "base". Unknown pay is kept for scoring with `[comp unknown]`.
<!-- skill-version: 2026-10-15 -->
