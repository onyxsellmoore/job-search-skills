Loaded by: daily run, step 3.
Reads: `<ws>/prefs.json`, `<ws>/profile/profile_summary.md`.
Writes: nothing.

# Scoring rubric

Score every surviving listing 0-10. Be strict. Optimism wastes the user's time. All thresholds come from prefs; nothing below names a person, city or company.

## Gates (binary; any failed gate caps the score at 3 and the role is dropped silently)
1. Title and level: title is in the target family (prefs.target_titles and close synonyms), level is in prefs.levels, no prefs.title_exclude_keywords. Early-career users: entry or associate is good, Senior and above fails. Experienced users: levels below target fail; ambiguous titles (Founding, Lead, Applied) are judged by scope and posted comp.
2. Location: the real listing is in prefs.locations.metros (any arrangement, aliases included) or fully remote when locations.remote allows it. A multi-office posting that lists a target metro as a real option passes. A "Remote" posting whose own text narrows to a non-target metro (hiring preference, "based in or near X", residency requirement, offices listed without the target) fails.
3. Not in prefs.excluded_companies, not on the blocked list.
4. No prefs.dealbreaker_keywords in title or text.
5. Pay: if comp is posted and clearly all-in below the applicable prefs.comp_floor (onsite_or_hybrid or remote; basis per comp_floor.basis), fail. A base-only range below floor does not fail when variable pay or equity plausibly closes the gap: tag `[comp unknown, base-only posted]` and score on fit. If comp is unknown, pass when the stage and employer type plausibly clear the floor (established, public, or well-funded growth stage); fail for pre-seed, nonprofit-without-signal or similar. A floor of 0 always passes. Sales roles: judge OTE, not base alone.

## Dimensions (sum to 10)
| Dimension | Pts | Scoring |
|---|---|---|
| Role archetype fit vs the profile's strengths | 0-4 | 4 dead-center on the strongest archetype and the JD names the user's proven skills; 3 second archetype or strong-but-imperfect; 2 adjacent, meaningful overlap; 1 nominal title, narrow or weak overlap; 0 wrong archetype |
| Company quality, by criteria not brand | 0-2 | 2 well-funded or established, and strong in the function (engineering-led; or for sales/marketing a clear ICP, enablement or ramp program, brand investment); 1 solid but less aligned, or thin funding signal; 0 weak reputation, layoffs, funding gaps, or a domain the user wants to leave. An unknown company with these traits scores as high as a famous one. |
| Growth and depth | 0-2 | 2 hard problems, real scope, mentorship or ramp for the level; 1 solid but maintenance-like; 0 resume debt (wrapper work, pure admin, call-volume churn) |
| Comp signal | 0-1 | 1 posted and clears the floor comfortably, or verified band; 0.5 unknown but plausible (tag `[comp unknown]`); 0 no signal or weak. When floor is 0, use 0.5 unless the band is posted. |
| Location alignment | 0-1 | 1 in the target metro the user is relocating to (prefs.locations.relocating_to, else the first metro); 0.5 other target metro or fully remote when relocating; with no relocation, 1 for the home metro or remote equally |

## Ladder
9-10 top 5% of roles this year. 8 excellent. 7 good, surface. 6.5-7 borderline, surface only if >= prefs.min_score. 5-6 decent, not a pick. 3-4 wrong archetype or company tier. 1-2 reject.

## Pick rule
Take the top prefs.picks_per_day roles scoring >= prefs.min_score for full packets, no confirmation step. List the rest above min_score as one line each. Zero or one qualifying role is a normal day; say so plainly and do not pad. Never build more than prefs.picks_per_day packets in a run.

## Calibration examples
Early-career marketing (entry level, home metro H, floor 0, min_score 6.5):
- "Marketing Coordinator", entry level, hybrid in H, B2B company with brand investment and a named manager, pay band not posted: 3 + 2 + 1 + 0.5 + 1 = 7.5, surface. (Floor 0 passes the pay gate.)
- "Senior Marketing Manager": gate 1 fails, score 3.
- "Digital Marketing Associate", remote, small agency, no mentorship, generic reporting tasks: 2 + 1 + 0 + 0 + 0.5 = 3.5, drop.

Early-career sales (entry level, home metro H, base floor posted, min_score 6.5):
- "Sales Development Representative" at a growth-stage software company, hybrid in H, base and OTE posted with base above the floor, named ramp or training program, user's strongest evidence is outbound prospecting: 4 + 2 + 2 + 1 + 1 = 10.
- "Business Development Representative", remote US, base not posted, OTE only, high call quotas and no training mentioned: 3 + 1 + 0 + 0.5 + 0.5 = 5, not a pick.
- "Account Executive, 3+ years closing experience": gate 1 fails, score 3.
<!-- skill-version: 2026-10-15 -->
