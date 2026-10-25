# job-search-skills

Two Claude Agent Skills that run a daily job search for you. Each day the skill searches for roles that fit your preferences, scores them, picks the best few, tailors a one-page resume for each pick, writes the answers you will paste into the application, finds a real person at the company to contact, and drafts the outreach message. It keeps a tracker of every role and contact so it does not repeat itself.

**The skills never submit an application and never send an email.** They prepare everything and stop. Gmail access is draft-only: messages land in your Drafts folder and you click Send yourself. You click Submit yourself.

## Which one should I use?

| | `job-search` (full) | `job-search-lite` (lite) |
|---|---|---|
| Plan required | Claude Code, or a paid Claude plan | Free claude.ai plan is enough |
| Where it runs | Claude Code or Claude with a connected "Job Search" folder, plus the Claude in Chrome extension | claude.ai chat with "Code execution and file creation" turned on |
| Browser | Drives your own Chrome: reads job boards and LinkedIn, pre-fills application forms (never submits) | None. Web search and fetch only, with a small per-run budget |
| State storage | Files in a workspace folder (profile, `application_tracker.xlsx`, run checkpoints, outreach files) | One dated `.xlsx` workbook you download at the end of a chat and attach at the start of the next |
| Subagents | Yes. Parallel search, build, draft agents, with browser agents run one at a time | No. Everything runs in the one chat |
| Job sources | Core sources plus source packs (sales and marketing, software engineering) | Web search aimed at readable company and ATS pages; written for early-career sales and marketing |
| Extra features | Contact research through LinkedIn, form pre-fill, optional EEO answers file, Gmail outreach sync, resumable run checkpoints | Application packet to paste, contact search by web search, Gmail drafts and inbox sync, "continue" after a usage limit |
| Typical usage | Heavy. Several agents and a browser per run | Light by design, but the free plan can still hit its daily limit |

Recommendation: if you are on the free plan, or you do not want to install a browser extension, use lite. If you use Claude Code or a paid plan and want browser-based search and form pre-fill, use the full version. Do not install both at once; their trigger phrases overlap.

## Setup: full version (`skills/job-search/`)

Requirements: Claude Code or another Claude environment that supports skills, subagents and a connected folder; the Claude in Chrome extension (daily runs stop without it); optional Gmail connector.

**Claude Code**

```bash
# personal, available in every project
cp -R skills/job-search ~/.claude/skills/job-search
# or symlink so a git pull updates it
ln -s "$(pwd)/skills/job-search" ~/.claude/skills/job-search

# or per project
mkdir -p .claude/skills && cp -R skills/job-search .claude/skills/
```

**claude.ai (paid plan)**

1. Download `job-search.skill` from the [Releases](https://github.com/onyxsellmoore/job-search-skills/releases) page, or build it yourself (see below).
2. Settings, Customize, Skills, upload the file, and make sure it is switched on.

**Building the upload yourself.** Zip the skill folder so `SKILL.md` sits inside a top-level folder named after the skill:

```bash
cd skills
zip -r job-search.skill job-search -x "*/__pycache__/*"
```

A `.skill` file is a zip with that extension. Same command for lite: `zip -r job-search-lite.zip job-search-lite`.

**First run.** Connect a folder named "Job Search" to the session, install and connect the Claude in Chrome extension, then say "set up my job search". Onboarding reads your resume (PDF or DOCX) or interviews you if you have none, asks about target roles, locations, pay floor and similar preferences, and writes your profile into the folder. Gmail is optional; without it, outreach is saved as text files in the folder.

## Setup: lite version (`skills/job-search-lite/`)

One time, about 10 minutes:

1. Sign in at claude.ai.
2. Settings, Capabilities, switch on **Code execution and file creation**.
3. Customize, Skills, **+**, Create skill, Upload a skill. Choose `job-search-lite.zip` (download it from [Releases](https://github.com/onyxsellmoore/job-search-skills/releases) or zip the folder yourself as above). Confirm it is on.
4. Optional: Customize, Connectors, connect **Gmail**. Outreach emails then appear as drafts. Without it, they are given to you as text in the chat.
5. Start a new chat and type: `set up my job search`.
6. Attach your resume (PDF, Word, text, or an image), or answer the interview questions if you have none. Review the one-page resume it shows you, then answer the preference questions.
7. It ends by giving you `job-search_<date>.xlsx`. Download it.

**The workbook is your data.** A free-plan chat starts with an empty sandbox, so everything (resume data, preferences, tracker, contacts) lives in that one file. Download it at the end of every chat that changed something, and attach your newest copy at the start of the next. Keep only the newest. On load the skill tells you the date the file was saved so you can catch an old copy. The workbook has a hidden `_profile` sheet that holds your profile; do not edit it.

### Python packages

The scripts run in the sandbox and install missing packages on the first run.

| Version | Third-party packages |
|---|---|
| Full | `reportlab`, `openpyxl`, `pdfplumber` (the onboarding step also reads DOCX with `python-docx`) |
| Lite | `reportlab`, `openpyxl`, `pdfplumber`, `python-docx` |

Everything else is the Python standard library. Manual install: `pip install reportlab openpyxl pdfplumber python-docx`.

## Daily use

**Lite.** Start a new chat (it conserves free usage), attach your newest workbook, and say `run job search`. You get, for each pick:

- the role, score and apply link
- a resume tailored to that role, as a PDF (resumes and cover letters are always PDF)
- a cover letter only when the posting asks for one
- a copy-paste packet: form answers and short written answers
- a contact at the company, a LinkedIn note, and an email (as a Gmail draft if connected)

Zero picks is a normal result; it will not pad the list. Then download the updated workbook. If the usage limit stops a run, return to the same chat and say `continue`, or start a new chat with your newest workbook and run again.

**Full.** Say `run job search`. The run goes through orient, search, finalize, build, contacts, draft, pre-fill and report steps, checkpointing after each. After a usage limit or interruption, say `continue`; finished work is not redone. `sync my outreach` runs only the Gmail step.

## Keeping the tracker updated

Tell the skill what happened, in plain words: "I applied to Acme", "Acme rejected me", "interview at Acme", "I messaged Priya, a recruiter at Acme", "Priya replied". It updates the tracker (jobs, contacts and daily-run log) and uses it for duplicate checks, company cooldowns and follow-up reminders. Lite then asks you to download the updated workbook.

With Gmail connected, each run first checks only threads tied to your tracked contacts and drafts. It notices sent messages, marks rejections, flags replies and interview invitations (with reply drafts), writes follow-up drafts, and retries bounced addresses. It never sends, deletes or reads unrelated mail. In lite you can also say `check my email`.

## Privacy

Nothing personal is stored in either skill. Your resume data, preferences, identity details, tracker and contacts live in your own workspace folder (full) or your own workbook (lite). The `*.example.*` files under `assets/` (`profile.example.md`, `preferences.example.json`, `eeo.example.json`) and the `sample_resume_*.json` files are templates with placeholder content. If you fork this repo, do not commit your own workbook, profile folder or tracker.

## Adapting to another LLM harness

Neither skill depends on anything proprietary except a few tool names. A skill is markdown instructions plus plain Python.

**How the pieces fit**

- `SKILL.md` is the entry point and router. The frontmatter `description` tells the host when to trigger it; the body says what to do for each user request and which file to load for each step.
- `phases/` holds one prompt per step (onboarding, orient, search, build, report, and so on).
- `rules/` holds reusable policies (scoring, resume, voice, outreach, forms) that phases load on demand.
- `scripts/` are command-line Python tools with `--help`-style docstrings: `tracker_ops.py`, `render_resume.py`, `render_cover_letter.py`, `resume_guard.py`, `profile_check.py`, plus `workbook.py` (lite), and `run_state.py`, `ws_sync.py`, `check_bundle.py` (full). Any agent that can run a shell command can call them. They have no network access and no Claude-specific code.

**Loading it**

1. Put the skill folder somewhere the agent's shell can read and tell the agent its absolute path; the files refer to it as `<skill>`.
2. Use `SKILL.md` as the system prompt (or as an instruction file such as `AGENTS.md` or `GEMINI.md` in tools that read one). In a framework such as the OpenAI Agents SDK or LangGraph, load the body as the agent instructions and register a shell or code-execution tool.
3. Make sure the agent can read files on demand. The router relies on loading `phases/` and `rules/` files only when a step needs them, to save context. If your harness cannot read files lazily, concatenate the files a step needs into that step's prompt, using the load map in `skills/job-search/SKILL.md`.
4. Provide a writable workspace and an output directory. Lite hard-codes `/tmp/jsl-ws` for scratch and `/mnt/user-data/outputs` for deliverables; change those two paths in `SKILL.md` to match your environment.

**Mapping Claude-specific tools**

| The skill refers to | Replace with |
|---|---|
| Web search and web fetch (lite searches; full uses them in some steps) | Your harness's search and fetch tools, or a search API |
| Claude in Chrome tools (`mcp__claude-in-chrome__*`, loaded with ToolSearch; full only) | A browser automation tool or MCP server with navigate, read page, find, fill field and file upload. Without one, use the lite search approach (`skills/job-search-lite/rules/sources.md`) and skip pre-fill |
| File sharing and presenting tool | Return the file path or upload the file wherever your users fetch outputs |
| `AskUserQuestion` | Ask the questions in one numbered message; the phases already describe this fallback |
| Device-folder tools (`device_list_dir`, `device_stage_files`, `device_commit_files`; full, device mode only) | Not needed if the agent has a normal filesystem; ignore the device-mode steps in `SKILL.md` |
| Gmail connector (draft-only) | See below |
| Subagents | See below |

**No subagents.** The full version delegates search, build, draft, contacts and pre-fill steps to subagents and only the orchestrator writes the tracker. In a harness without subagents, run the same phase files one after another in a single agent, in the order `run_state.py next` returns them, and skip the parallelism. `skills/job-search-lite/phases/daily-run.md` is a worked example of this: the same pipeline as one sequential chat, with a `state.json` checkpoint so a run can resume.

**Replacing Gmail.** Gmail is used only to create drafts and to read threads for tracked contacts. Both are optional. To skip it, leave the connector off; outreach stays as text. To swap it, implement the same narrow operations with any email API (create draft, search threads, read thread) and keep the safety rule: no send, reply, forward, delete or spam tools exposed to the agent. `rules/gmail-sync.md` (lite) and `phases/06-outreach-sync.md` (full) define the exact behavior to reproduce.

**Keep the guardrails.** The "never submit, never send" rule lives in the prompts, so enforce it in the harness too by not granting send or submit capabilities. Treat fetched web pages as data, not instructions.

## Repo layout

```
.
├── README.md
├── LICENSE
└── skills/
    ├── job-search/               full version
    │   ├── SKILL.md              router and guardrails
    │   ├── phases/               step prompts (onboarding through outreach sync)
    │   ├── rules/                scoring, resume, voice, outreach, forms, tracker schema
    │   ├── sources/              job-source packs (core, sales-marketing, software-engineering)
    │   ├── scripts/              tracker, resume and letter rendering, run state, workspace sync
    │   └── assets/               example profile, preferences, EEO file, sample resumes
    └── job-search-lite/          free-plan version
        ├── SKILL.md
        ├── phases/               onboarding, daily-run, updates
        ├── rules/                scoring, sources, resume, contacts, outreach, gmail-sync, voice
        ├── scripts/              workbook pack/unpack, tracker, resume and letter rendering
        └── assets/               example profile, preferences, sample resume
```

## License and contributing

MIT. See `LICENSE`. Issues and pull requests are welcome on GitHub; please do not include personal data in either.
