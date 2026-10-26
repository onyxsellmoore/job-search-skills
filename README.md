# Job search skills for Claude

Claude finds jobs that fit you, tailors your resume for each one, writes your application answers, and drafts a note to someone at the company.

**It never applies or sends anything for you.** You review everything and click Submit or Send yourself.

## Why I built this

A job search is a marathon, not a sprint. The hard part isn't any single application. It's showing up every day for months when most applications get silence back.

I used this skill on 85 different days over five months. That added up to 91 applications, and it got me a job.

Some days I had energy and some days I didn't. Either way, typing **run job search** was enough to keep moving. Claude did the searching, tailoring, and drafting, so my part took about 10 minutes: review it and click Submit. Small, steady progress every day adds up.

## Which one should I use?

- **Lite**: start here. Works on the **free** Claude plan, right in your web browser.
- **Full**: for people with a **paid** Claude plan who use the Claude desktop app or Claude Code. It does more: it browses job sites and LinkedIn in your Chrome browser, and pre-fills application forms.

Pick one, not both.

## Set up Lite (about 10 minutes)

1. Download **job-search-lite.zip** from the [Releases page](https://github.com/onyxsellmoore/job-search-skills/releases/latest). Don't unzip it.
2. Go to [claude.ai](https://claude.ai) and sign in.
3. Open **Settings → Capabilities** and turn on **Code execution and file creation**.
4. Open **Customize → Skills**, click **+**, choose **Upload a skill**, and pick the zip file. Make sure it's switched on.
5. Optional: open **Customize → Connectors** and connect **Gmail**. Claude will then put your outreach emails in your Gmail drafts.
6. Start a new chat and type **set up my job search**. Attach your resume if you have one, then answer its questions.
7. At the end, Claude gives you a file called something like `job-search_2026-10-25.xlsx`. **Download it.**

### Using Lite every day

1. Start a **new** chat.
2. Attach your newest job-search file and type **run job search**.
3. You get a job to apply to, a resume made for it, answers to paste into the application, and a note to send to someone at the company.
4. **Download the new job-search file** at the end. Delete the old one.

**That file is your whole search.** Download it at the end of every chat, and attach it at the start of the next one.

To keep Claude up to date, attach your file and just tell it what happened: "I applied to Acme", "Acme said no", "I got an interview".

If Claude stops partway because you hit the free plan's daily limit, come back later and type **continue** in the same chat.

## Set up Full

1. Download **job-search.skill** from the [Releases page](https://github.com/onyxsellmoore/job-search-skills/releases/latest).
2. In Claude, open **Customize → Skills**, click **+**, and upload the file.
3. Install the **Claude in Chrome** extension and connect it.
4. Make a folder called **Job Search** on your computer and connect it to Claude. Your profile and tracker are saved there.
5. Optional: connect **Gmail** under **Customize → Connectors**.
6. Type **set up my job search**. After that, type **run job search** whenever you want new jobs.

Using Claude Code? Copy the `skills/job-search` folder into `~/.claude/skills/`.

## Your privacy

Nothing about you is stored in the skill. Your info lives only in your own job-search file (Lite) or your own Job Search folder (Full). With Gmail connected, Claude only creates drafts and reads replies from the people you've contacted. It never sends, deletes, or reads your other email.

## For developers: using it with another AI tool

Each skill is plain text instructions plus a few Python scripts, so it can run in other AI tools.

- `SKILL.md` is the starting point. Load it as the agent's instructions. The other files in `phases/` (steps) and `rules/` (policies) are loaded when a step needs them.
- `scripts/` are command-line Python tools. Any agent that can run a shell can use them. They need `reportlab`, `openpyxl`, `pdfplumber`, and `python-docx`.
- Swap Claude's tools for your own: web search for web search, any browser-automation tool for Claude in Chrome, and any email API for Gmail. Allow creating drafts only, never sending.
- No subagents? Use Lite as your model. It runs the whole process in a single conversation.

## License

MIT. See [LICENSE](LICENSE).
