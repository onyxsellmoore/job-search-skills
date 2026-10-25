# Rule: Voice and AI-tell checklist
Loaded by: the daily run before writing any prose (resume bullets, cover letters, short answers, outreach). Run it before saving any file and fix every hit.

Everything must read like the candidate wrote it, in their own facts. AI tells get applications filtered and emails ignored.

1. No em-dash character (U+2014). No `--` used as a dash. No hyphen with a space on both sides (`word - word`). Use a comma, period, colon, or rewrite. Compound hyphens (`LLM-driven`) and unspaced date ranges (`Nov 2024-Present`) are fine. Scan every file for these before saving. Highest priority.
2. No antithesis crutch ("X, not Y", "not just X but Y") as a repeated move. One may be fine; a pattern is a tell.
3. No reflexive tricolons ("build, ship, and scale") unless all three words carry weight.
4. Vary sentence length. Uniform medium sentences and uniformly parallel bullets read as machine output.
5. No hollow openers: "Hope this finds you well", "I wanted to reach out", "I came across your profile", "I'm excited to". Start with the point.
6. Banned words and phrases in the candidate's own prose: delve, robust, seamless, leverage (verb), synergy, passionate about, results-driven, fast-paced, hit the ground running, wear many hats, circle back, touch base, think outside the box, buzzwords generally. Extra words come from `prefs.voice.banned_words`.
7. The banned list applies to prose you write, never to proper nouns or quoted names taken from `resume.json` or the job posting (a project, product, or company name that contains a banned word is copied exactly).
8. Use only facts from `resume.json` and `profile.md`. Numbers carry their hedge every time (estimates stay estimates). Never invent a metric, name, or news item.
9. Verbs: follow `prefs.voice.preferred_verbs` and `avoid_verbs` when set. Otherwise prefer concrete verbs the candidate can defend (built, owned, ran, sold, launched) over inflated ones.
10. Read it back. If it sounds like a template, rewrite it. Short beats long. Match the register to the function: plain and specific, with no seniority claims for early-career candidates.
<!-- skill-version: 2026-10-15 -->
