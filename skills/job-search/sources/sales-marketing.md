# Sales and marketing sources (early career)

Read together with core.md (time window, location filter, dedupe, URL priority all apply). Values come from the resolved preferences JSON: target_titles, title_exclude_keywords, levels, career_stage, locations, comp_floor, excluded_companies, dealbreaker_keywords, extra_sources. Treat the user's title list as the primary search terms; the mapping below only adds synonyms.

## Must-run extras
- LinkedIn entry-level pass: in core.md's LinkedIn searches, use the Filters panel to set Experience level to Entry level (and Associate if the user's levels allow), then copy the URL params. Run the metro pass (no f_WT) and the remote pass.
- Built In city site, category paths: `https://www.builtinnyc.com/jobs/sales/entry-level` (verified pattern; also seen: `builtinnyc.com/jobs/remote/sales/sales-developement/entry-level`). Example only, US cities: swap the city site to match locations.metros (outside the US, use the site's own filters or skip it), and the category segment (sales, marketing) to the user's function. Filters: Remote/Hybrid, New Jobs, Experience. If a path 404s, set the same filters in the UI and copy the URL.
- The Muse `https://www.themuse.com/search`: Experience Level = Entry (or Internship only if asked), Date Posted 7 or 14 days, Category = Sales or Marketing, Remote/Flexible as needed; "Apply On Company Site" gives the direct link.

## Rotating (one per run, per core.md rotation rule)
- Indeed: filters for date posted, remote, experience; reCAPTCHA risk. Use title plus location.
- ZipRecruiter `https://www.ziprecruiter.com`: date posted, remote, experience; heavy duplication of Indeed and staffing agencies, dedupe hard.
- Mediabistro `https://www.mediabistro.com/jobs/`: media, marketing, content, social roles; age shown per listing; filter options unverified (verify on first run). Use for marketing users.
- Wellfound `https://wellfound.com/jobs`: Sales and Marketing categories, startups, fewer entry-level roles.
- Hiring.cafe is already core must-run; here set the Departments/Titles filters to sales or marketing.
- Handshake and WayUp: only when the user says they already have an account; both need login. Otherwise skip.

## Early-career title mapping
Sales: SDR, BDR, Sales Development Representative, Business Development Representative, Account Development Representative, Sales Associate, Inside Sales Representative, Associate Account Executive, Customer Success Associate. Marketing: Marketing Coordinator, Marketing Associate, Content Coordinator, Social Media Coordinator, Community Coordinator, Growth Marketing Associate, Email/Lifecycle Coordinator, Marketing Assistant, Junior Copywriter. Search the user's target_titles first, then these where they match the function.

## Exclude at collection
- Commission-only or "100% commission" roles; roles with no base pay stated alongside "unlimited earning potential".
- MLM, network marketing, "independent business owner", "be your own boss", pay-to-start or buy-inventory schemes.
- Door-to-door, canvassing, "field marketing" that is really street sales.
- Unpaid internships (unless the user asked), and "internship" roles when career_stage is not early.
- Roles requiring 3+ years of experience when career_stage is early (read the requirements, not just the title); Senior, Lead, Manager and Director levels outside levels.
- Staffing-agency reposts with no named employer; keep only if the employer is named.
- Anything matching excluded_companies, title_exclude_keywords or dealbreaker_keywords.
Pay: early sales is OTE-based, so note base and OTE separately; compare to comp_floor.basis when set. Keep [comp unknown] roles for scoring.

## Boards not recommended
- Pavilion: paid membership, not automatable.
- RepVue: use to vet company comp and culture, no confirmed job board.
- Bravado: recruiter intermediary, low value versus direct ATS links.
- Superpath: board status unclear, skews senior and freelance.
- Glassdoor: merged into Indeed, redundant for discovery.
- Welcome to the Jungle (Otta): no US listings seen.
- Idealist and Dribbble: only for nonprofit or design targets.
- AMA, MarketingHire, SalesHive, CMI, GrowthHackers: freshness and login unconfirmed; add via extra_sources only after the user checks them.
<!-- skill-version: 2026-10-13 -->
