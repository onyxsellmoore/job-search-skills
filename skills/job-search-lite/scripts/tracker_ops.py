#!/usr/bin/env python3
# skill-version: 2026-10-13
"""Tracker operations for the job search skill.

Operates on an xlsx workbook with three sheets: jobs, contacts, daily_runs.

Global options (before the command):
    --path <tracker.xlsx>       required for every command
    --prefs <preferences.json>  optional; reads cooldown_days (default 7),
                                cooldown_overrides, outreach_cooldown_days
                                (default 90), excluded_companies and
                                picks_per_day (default 3)

Commands:
    init                          create the workbook (the only command that creates one)
    seen --url URL
    seen-batch [--file urls.txt] [--urls URL ...]
    dup-check --file candidates.jsonl
    blocked-companies [--cooldown-days N] [--as-of YYYY-MM-DD]
    company-cooldown --company NAME [--company NAME ...] [--file f.jsonl] [--as-of YYYY-MM-DD]
    add-job --company C --role R --url U [options]
    update-job --id N [options]
    add-contact --name N --company C --degree 1st|2nd|cold [options]
    update-contact --id N [options]
    contacts-pending [--as-of YYYY-MM-DD]
    log-run [--surfaced N] [--top-picks N] [--drafted N] [--contacts N] [--notes T]
    import-run --file run.json
    merge-reports --base base.json --dir scratch/ --out run.json
    follow-ups [--as-of YYYY-MM-DD]
    funnel [--days N]
    summary

Exit codes: 0 ok, 1 item-level failure, 2 usage error or missing file,
3 shrink guard refused a save.
"""

import argparse
import json
import re
import shutil
import sys
import urllib.parse
from datetime import date, datetime, timedelta
from pathlib import Path

try:
    from openpyxl import Workbook, load_workbook
except ImportError:
    print("ERROR: openpyxl not installed. Install with: pip install openpyxl --break-system-packages", file=sys.stderr)
    sys.exit(2)


JOBS_COLS = [
    "id", "first_seen", "last_updated", "company", "role_title", "level",
    "location", "source", "url", "alt_urls", "comp_posted", "fit_score",
    "score_rationale", "resume_variant", "status", "drafted_date",
    "submitted_date", "referral_contact", "referral_sent_date",
    "referral_response", "review_notes", "tab_info", "cover_letter_file",
    "cancellation_reason",
]

# New columns are only ever appended at the END of these lists so index-based
# reads against older trackers stay aligned; ensure_*_columns migrates them.
CONTACTS_COLS = [
    "id", "first_contacted", "contact_name", "contact_title", "company",
    "connection_degree", "connection_path", "linkedin_url",
    "message_template", "message_draft", "status", "response_summary",
    "linked_job_ids",
    "sent_date", "gmail_draft_id", "gmail_thread_id", "followup_draft_id",
    "cancellation_note_draft_id", "email",
]

RUNS_COLS = [
    "run_date", "roles_surfaced", "top_picks_count", "drafted_count",
    "contacts_drafted", "slow_day", "notes",
]

# Contact statuses the outreach-sync reconciliation is allowed to write.
CONTACT_STATUSES = {"drafted", "sent", "accepted", "replied", "ghosted", "rejected"}

# Title substrings that mark a contact as recruiter/talent/sourcer-ish: a
# bench-nurture, established contact rather than a one-off cold-outreach
# contact. contact_title is the only signal, so every place that needs the
# distinction goes through _is_recruiterish_title.
RECRUITERISH_TITLE_KEYWORDS = ("recruit", "talent", "sourcer", "people ops")


def _is_recruiterish_title(title):
    return any(k in str(title or "").lower() for k in RECRUITERISH_TITLE_KEYWORDS)


# Settings. Defaults here; load_prefs() replaces them from --prefs.
# Application cooldown: days a company is blocked from surfacing a NEW role
# after a real application. Separate from the outreach cooldown below, which
# gates cold outreach emails and never blocks an application.
COOLDOWN_DAYS = 7
OUTREACH_COOLDOWN_DAYS = 90
SLOW_DAY_THRESHOLD = 3  # a run with fewer top picks than this is a slow day

# Cooldown families from prefs cooldown_overrides. All keys are _norm_company
# output. A family is one canonical name plus its aliases; every member shares
# one clock, started by the most recent application to ANY member.
COMPANY_COOLDOWN_OVERRIDES = {}   # family key -> days
COMPANY_COOLDOWN_ALIASES = {}     # alias key -> family key
COMPANY_COOLDOWN_DISPLAY = {}     # member key -> display name as written in prefs
EXCLUDED_COMPANIES = {}           # norm name -> display name; always blocked


def load_prefs(path):
    """Read the settings used by this script from a preferences.json file."""
    global COOLDOWN_DAYS, OUTREACH_COOLDOWN_DAYS, SLOW_DAY_THRESHOLD
    try:
        prefs = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError) as e:
        print(f"ERROR: cannot read --prefs {path!r}: {e}", file=sys.stderr)
        sys.exit(2)
    if not isinstance(prefs, dict):
        print(f"ERROR: --prefs {path!r} must hold a JSON object", file=sys.stderr)
        sys.exit(2)

    def _int(key, default, minimum=0):
        v = prefs.get(key)
        if v is None:
            return default
        if isinstance(v, bool) or not isinstance(v, int) or v < minimum:
            print(f"ERROR: prefs {key} must be an integer >= {minimum}", file=sys.stderr)
            sys.exit(2)
        return v

    COOLDOWN_DAYS = _int("cooldown_days", COOLDOWN_DAYS)
    OUTREACH_COOLDOWN_DAYS = _int("outreach_cooldown_days", OUTREACH_COOLDOWN_DAYS)
    SLOW_DAY_THRESHOLD = _int("picks_per_day", SLOW_DAY_THRESHOLD)

    COMPANY_COOLDOWN_OVERRIDES.clear()
    COMPANY_COOLDOWN_ALIASES.clear()
    COMPANY_COOLDOWN_DISPLAY.clear()
    for item in prefs.get("cooldown_overrides") or []:
        name = item.get("company") if isinstance(item, dict) else None
        days = item.get("days") if isinstance(item, dict) else None
        if not name or isinstance(days, bool) or not isinstance(days, int) or days < 0:
            print(f"ERROR: bad cooldown_overrides entry {item!r} "
                  f"(needs company and integer days >= 0)", file=sys.stderr)
            sys.exit(2)
        fam = _norm_company(name)
        COMPANY_COOLDOWN_OVERRIDES[fam] = days
        COMPANY_COOLDOWN_DISPLAY[fam] = str(name).strip()
        for alias in item.get("aliases") or []:
            key = _norm_company(alias)
            if key and key != fam:
                COMPANY_COOLDOWN_ALIASES[key] = fam
                COMPANY_COOLDOWN_DISPLAY[key] = str(alias).strip()

    EXCLUDED_COMPANIES.clear()
    for name in prefs.get("excluded_companies") or []:
        if str(name).strip():
            EXCLUDED_COMPANIES[_norm_company(name)] = str(name).strip()


def _cooldown_family_key(norm_company):
    """The override family this normalized company belongs to, or None."""
    if norm_company in COMPANY_COOLDOWN_OVERRIDES:
        return norm_company
    return COMPANY_COOLDOWN_ALIASES.get(norm_company)


def _cooldown_family_members(family_key):
    """The family name itself plus every alias that resolves to it."""
    members = [family_key]
    members += sorted(a for a, k in COMPANY_COOLDOWN_ALIASES.items() if k == family_key)
    return members


# Status groups.
# Packet prepared but not applied: suppresses the exact posting only, never
# starts a company cooldown.
PACKET_STATUSES = {"drafted", "packet_ready"}

# Applied or in process: suppresses the exact posting and starts the company
# cooldown. "applied" is a legacy alias of "submitted"; "interview_scheduled"
# is a synonym of "interview".
APPLIED_STATUSES = {"submitted", "applied", "referral_sent", "interview", "interview_scheduled"}

# Terminal outcomes: the exact posting stays hidden, the company is not held in
# cooldown. "dead" is a legacy alias of withdrawn/rejected.
TERMINAL_STATUSES = {"rejected", "no_response", "withdrawn", "dead", "interview_cancelled"}

# Any of these suppresses the exact URL on later runs. A row still at
# surfaced / top_pick is treated as never seen and may resurface.
SUPPRESS_STATUSES = PACKET_STATUSES | APPLIED_STATUSES | TERMINAL_STATUSES

# Every status the skill writes; others draw a warning (dedup ignores them).
KNOWN_STATUSES = (
    {"surfaced", "top_pick"} | PACKET_STATUSES | APPLIED_STATUSES | TERMINAL_STATUSES
)


def _warn_unknown_status(status):
    if status and status not in KNOWN_STATUSES:
        print(
            f"WARNING: status {status!r} is not a known status; dedup/cooldown "
            f"will ignore it. Known: {sorted(KNOWN_STATUSES)}",
            file=sys.stderr,
        )


_TRACKING_PARAMS = {
    "trk", "trkinfo", "gh_src", "source", "src", "ref", "referrer",
    "recruiter", "li_fat_id", "originalsubdomain", "position", "pipeline",
}


def _norm_company(name):
    """Canonical key for a company name: case-, whitespace-, and light
    punctuation-insensitive ('Acme Inc.' and 'acme inc' share a key).
    """
    s = str(name).strip().casefold().replace(".", "").replace(",", "")
    return " ".join(s.split())


def _norm_title(title):
    """Canonical key for a job title: case-/whitespace-insensitive, trailing
    punctuation stripped. Deliberately not fuzzy.
    """
    if title is None:
        return ""
    s = str(title).strip().casefold()
    s = re.sub(r"[.,;:]+$", "", s)
    return " ".join(s.split())


_LINKEDIN_JOB_PATH = re.compile(r"^/jobs/view/(?:[a-z0-9-]*-)?(\d{6,})$")


def _canon_url(u):
    """Canonicalize a posting URL for dedup.

    Lowercases scheme and host (any linkedin.com host, including country
    subdomains, becomes www.linkedin.com), drops the fragment and trailing slash, and
    strips tracking query params (utm_*, trk, gh_src, source, ...); other
    params are kept because job ids often live there. LinkedIn
    /jobs/view/<slug>-<id> and /jobs/view/<id> both reduce to the numeric id.
    """
    if u is None or str(u).strip() == "":
        return ""
    s = str(u).strip()
    try:
        parts = urllib.parse.urlsplit(s)
    except ValueError:
        return s.rstrip("/")
    if not parts.scheme and not parts.netloc:
        return s.rstrip("/")
    q = [
        (k, v)
        for (k, v) in urllib.parse.parse_qsl(parts.query, keep_blank_values=True)
        if k.lower() not in _TRACKING_PARAMS and not k.lower().startswith("utm_")
    ]
    path = parts.path.rstrip("/")
    host = parts.netloc.lower()
    if host == "linkedin.com" or host.endswith(".linkedin.com"):
        host = "www.linkedin.com"
        m = _LINKEDIN_JOB_PATH.match(path.lower())
        if m:
            path = f"/jobs/view/{m.group(1)}"
    return urllib.parse.urlunsplit((
        parts.scheme.lower(),
        host,
        path,
        urllib.parse.urlencode(q),
        "",
    ))


def _norm_date_str(v):
    """Normalize any date-ish input to ISO 'YYYY-MM-DD', else ''.

    The script owns the tracker's date cells and always writes ISO strings so
    later reads stay string-typed and consistent. _parse_date still tolerates
    datetime cells a human may introduce by editing the xlsx in Excel.
    """
    d = _parse_date(v)
    return d.isoformat() if d else (str(v).strip() if v else "")


def _lock_sentinels(path):
    p = Path(path)
    return [p.with_name("~$" + p.name), p.with_name(".~lock." + p.name + "#")]


def _warn_if_open(path):
    """Warn (do not block) if the tracker looks open in Excel/LibreOffice."""
    for s in _lock_sentinels(path):
        if s.exists():
            print(
                f"WARNING: {Path(path).name} looks open in Excel/LibreOffice "
                f"({s.name} present); a save now may conflict with unsaved edits.",
                file=sys.stderr,
            )
            return


def _pre_write_backup(path):
    """One backup per day, before the first write of that day (copy, not rename)."""
    p = Path(path)
    if not p.exists():
        return
    bak = p.with_name(f"{p.stem}.autobak.{date.today().isoformat()}{p.suffix}")
    if bak.exists():
        return
    try:
        shutil.copy2(p, bak)
    except OSError:
        pass


def _guard_against_shrink(wb, path):
    """Refuse to overwrite a tracker with drastically fewer job rows.

    No command removes jobs rows, so a large drop means the wrong workbook
    was loaded.
    """
    p = Path(path)
    if not p.exists():
        return
    try:
        old_wb = load_workbook(path, read_only=True)
        if "jobs" not in old_wb.sheetnames:
            return
        old_ws = old_wb["jobs"]
        old_count = sum(
            1 for row in old_ws.iter_rows(min_row=2, values_only=True)
            if row and any(c is not None and str(c).strip() != "" for c in row)
        )
    except Exception:
        return
    if "jobs" not in wb.sheetnames:
        return
    new_ws = wb["jobs"]
    new_count = sum(
        1 for row in new_ws.iter_rows(min_row=2, values_only=True)
        if row and any(c is not None and str(c).strip() != "" for c in row)
    )
    if old_count >= 5 and new_count < old_count * 0.5:
        print(
            f"REFUSING TO SAVE: {path} currently has {old_count} job rows on "
            f"disk; this write would drop it to {new_count}, a >50% loss. No "
            f"command in this script legitimately removes rows, so this almost "
            f"certainly means the wrong tracker was loaded (check --path). "
            f"Aborting without writing; the file on disk is untouched.",
            file=sys.stderr,
        )
        sys.exit(3)


def _save(wb, path):
    """Guarded save: open-file warning, daily backup, shrink guard, then write."""
    _warn_if_open(path)
    _pre_write_backup(path)
    _guard_against_shrink(wb, path)
    wb.save(path)


def tracker_path(args):
    path = getattr(args, "path", None)
    if not path:
        print("ERROR: --path <tracker.xlsx> is required for every command "
              "(there is no default location).", file=sys.stderr)
        sys.exit(2)
    return path


def ensure_jobs_columns(wb):
    """Self-healing migration: append any JOBS_COLS missing from the jobs header."""
    if "jobs" not in wb.sheetnames:
        return
    ws = wb["jobs"]
    header = [c.value for c in ws[1]]
    while header and (header[-1] is None or header[-1] == ""):
        header.pop()
    for col in JOBS_COLS:
        if col not in header:
            ws.cell(row=1, column=len(header) + 1).value = col
            header.append(col)


def ensure_contacts_columns(wb):
    """Same self-healing migration as ensure_jobs_columns, for contacts."""
    if "contacts" not in wb.sheetnames:
        return
    ws = wb["contacts"]
    header = [c.value for c in ws[1]]
    while header and (header[-1] is None or header[-1] == ""):
        header.pop()
    for col in CONTACTS_COLS:
        if col not in header:
            ws.cell(row=1, column=len(header) + 1).value = col
            header.append(col)


def _ccell(row, name):
    """Contact cell by column name, safe for rows shorter than the header."""
    i = CONTACTS_COLS.index(name)
    return row[i] if i < len(row) else None


def load_or_init(path, allow_create=False):
    p = Path(path)
    if not p.exists():
        if not allow_create:
            print(
                f"ERROR: no tracker found at {path!r}. Refusing to create a "
                f"blank one implicitly. To start a new tracker run "
                f"`tracker_ops.py --path {path} init`; otherwise fix --path "
                f"to point at the existing tracker file.",
                file=sys.stderr,
            )
            sys.exit(2)
        wb = Workbook()
        ws = wb.active
        ws.title = "jobs"
        ws.append(JOBS_COLS)
        ws_c = wb.create_sheet("contacts")
        ws_c.append(CONTACTS_COLS)
        ws_r = wb.create_sheet("daily_runs")
        ws_r.append(RUNS_COLS)
        p.parent.mkdir(parents=True, exist_ok=True)
        _save(wb, path)
        return wb
    wb = load_workbook(path)
    ensure_jobs_columns(wb)
    ensure_contacts_columns(wb)
    return wb


def next_id(ws, id_col_idx=1):
    """Next id that cannot collide with an existing row, even when some id
    cells are not integers (those are still counted).
    """
    max_id = 0
    count = 0
    for row in ws.iter_rows(min_row=2, values_only=True):
        if row and row[id_col_idx - 1] is not None and str(row[id_col_idx - 1]).strip() != "":
            count += 1
            try:
                max_id = max(max_id, int(float(str(row[id_col_idx - 1]).strip())))
            except (ValueError, TypeError):
                pass
    return max(max_id, count) + 1


def _id_match(cell_val, target):
    """True if a tracker id cell equals the target id, tolerant of int/str."""
    if cell_val is None:
        return False
    try:
        return int(float(str(cell_val).strip())) == int(target)
    except (ValueError, TypeError):
        return str(cell_val).strip() == str(target)


def today():
    return date.today().isoformat()


def cmd_init(args):
    path = tracker_path(args)
    wb = load_or_init(path, allow_create=True)
    _save(wb, path)
    print(f"Tracker ready at: {path}")


def cmd_seen(args):
    path = tracker_path(args)
    wb = load_or_init(path)
    ws = wb["jobs"]
    url_idx = JOBS_COLS.index("url")
    alt_idx = JOBS_COLS.index("alt_urls")
    target = _canon_url(args.url)
    status_idx = JOBS_COLS.index("status")
    for row in ws.iter_rows(min_row=2, values_only=True):
        if not row:
            continue
        urls = []
        if row[url_idx]:
            urls.append(_canon_url(row[url_idx]))
        if row[alt_idx]:
            urls.extend(_canon_url(u) for u in str(row[alt_idx]).split(";") if u.strip())
        if target and target in urls:
            status = row[status_idx]
            _warn_unknown_status(status)
            print(json.dumps({
                "seen": True,
                "suppress": status in SUPPRESS_STATUSES,
                "id": row[0],
                "company": row[3],
                "role": row[4],
                "status": status,
            }))
            return
    print(json.dumps({"seen": False, "suppress": False}))


def _parse_date(val):
    """Best-effort parse of a tracker date cell into a date, or None.

    openpyxl returns date-typed cells as datetime objects. datetime is a
    subclass of date, so we must check datetime FIRST and coerce to .date(),
    otherwise downstream date-vs-datetime comparisons raise TypeError.
    """
    if val is None or val == "":
        return None
    if isinstance(val, datetime):
        return val.date()
    if isinstance(val, date):
        return val
    s = str(val).strip().split("T")[0].split(" ")[0]
    try:
        return datetime.strptime(s, "%Y-%m-%d").date()
    except ValueError:
        return None


def _blocked_companies(args):
    """Companies currently inside the per-company cooldown window.

    A company is blocked if it has a row in an APPLIED status whose most
    recent application activity (submitted_date, else referral_sent_date,
    else drafted_date, else first_seen, else last_updated) is within the
    cooldown of the as-of date. Packet and terminal statuses never block.

    Length: cooldown_days from prefs (or --cooldown-days), except a company
    in a prefs cooldown_overrides family, which uses the override days. A
    family shares ONE clock started by the latest application to any member,
    and every member is listed while it is open, even one with no row of its
    own. Excluded companies from prefs are always listed with "excluded": true.
    """
    path = tracker_path(args)
    wb = load_or_init(path)
    ws = wb["jobs"]
    co_idx = JOBS_COLS.index("company")
    status_idx = JOBS_COLS.index("status")
    sub_idx = JOBS_COLS.index("submitted_date")
    draft_idx = JOBS_COLS.index("drafted_date")
    ref_idx = JOBS_COLS.index("referral_sent_date")
    first_idx = JOBS_COLS.index("first_seen")
    upd_idx = JOBS_COLS.index("last_updated")

    cooldown = getattr(args, "cooldown_days", None)
    if cooldown is None:
        cooldown = COOLDOWN_DAYS
    if cooldown < 0:
        print("ERROR: --cooldown-days must be >= 0", file=sys.stderr)
        sys.exit(2)

    # A bad --as-of fails loudly rather than silently meaning today.
    as_of_raw = getattr(args, "as_of", None)
    if as_of_raw:
        as_of = _parse_date(as_of_raw)
        if as_of is None:
            print(f"ERROR: --as-of {as_of_raw!r} is not a valid YYYY-MM-DD date",
                  file=sys.stderr)
            sys.exit(2)
    else:
        as_of = date.today()

    # Full-day window: a company applied on day D reopens on D + cooldown
    # (e.g. applied 06-30, cooldown 7 -> free on 07-07).
    latest = {}  # norm company -> {"display": first-seen spelling, "date": date}
    unknown_statuses = set()
    for row in ws.iter_rows(min_row=2, values_only=True):
        if not row or not row[co_idx]:
            continue
        status = row[status_idx]
        if status and status not in KNOWN_STATUSES:
            unknown_statuses.add(status)
        if status not in APPLIED_STATUSES:
            continue
        # Anchor on real application activity; first_seen never changes, and
        # last_updated is last because unrelated edits move it.
        d = (_parse_date(row[sub_idx]) or _parse_date(row[ref_idx])
             or _parse_date(row[draft_idx]) or _parse_date(row[first_idx])
             or _parse_date(row[upd_idx]))
        if d is None:
            continue
        key = _norm_company(row[co_idx])
        entry = latest.get(key)
        if entry is None:
            latest[key] = {"display": str(row[co_idx]).strip(), "date": d}
        elif d > entry["date"]:
            entry["date"] = d

    if unknown_statuses:
        print(
            "WARNING: tracker rows carry unknown statuses not counted for "
            f"cooldown/dedup: {sorted(unknown_statuses)}. Known: "
            f"{sorted(KNOWN_STATUSES)}",
            file=sys.stderr,
        )

    # Group tracker company names by cooldown family.
    family_of = {}
    for lit_key in latest:
        fam = _cooldown_family_key(lit_key)
        if fam:
            family_of[lit_key] = fam
    family_literal_keys = set(family_of)

    blocked = []

    # One shared clock per active family, anchored on the most recent
    # application to any member; cooldown_source names that member.
    for fam_key in sorted(set(family_of.values())):
        members = _cooldown_family_members(fam_key)
        dated = [(m, latest[m]) for m in members if m in latest]
        if not dated:
            continue
        anchor_key, anchor_entry = max(dated, key=lambda kv: kv[1]["date"])
        shared_date = anchor_entry["date"]
        days = COMPANY_COOLDOWN_OVERRIDES[fam_key]
        free_on = shared_date + timedelta(days=days)
        if as_of >= free_on:
            continue
        for m in members:
            display = latest[m]["display"] if m in latest else (
                COMPANY_COOLDOWN_DISPLAY.get(m, m.title())
            )
            blocked.append({
                "company": display,
                "last_applied": shared_date.isoformat(),
                "free_on": free_on.isoformat(),
                "cooldown_days": days,
                "cooldown_source": anchor_entry["display"],
            })

    # Everything else: one company, one clock, standard length.
    for key, entry in sorted(latest.items()):
        if key in family_literal_keys:
            continue
        d = entry["date"]
        free_on = d + timedelta(days=cooldown)
        if as_of < free_on:
            blocked.append({
                "company": entry["display"],
                "last_applied": d.isoformat(),
                "free_on": free_on.isoformat(),
                "cooldown_days": cooldown,
            })

    # Excluded companies are always blocked, whatever the tracker says.
    if EXCLUDED_COMPANIES:
        blocked = [b for b in blocked if _norm_company(b["company"]) not in EXCLUDED_COMPANIES]
        for display in EXCLUDED_COMPANIES.values():
            blocked.append({
                "company": display,
                "last_applied": None,
                "free_on": None,
                "cooldown_days": None,
                "excluded": True,
            })

    blocked.sort(key=lambda b: _norm_company(b["company"]))
    return blocked


def cmd_blocked_companies(args):
    print(json.dumps(_blocked_companies(args)))


def _outreach_cooldown_for_companies(args, companies):
    """Per-company cold OUTREACH cooldown state (a separate question from
    blocked-companies, the application cooldown).

    For each requested company (matched with _norm_company), scans the
    cold-outreach rows of the contacts sheet and reports last_cold_outreach
    (sent_date, else first_contacted), last_contact_name, free_on (that date
    plus OUTREACH_COOLDOWN_DAYS), has_reply (any such row at status
    "replied", which clears the cooldown) and in_cooldown. Recruiter-ish
    contacts are excluded entirely: they are established contacts, not cold
    outreach. Read-only.
    """
    path = tracker_path(args)
    wb = load_or_init(path)
    ws = wb["contacts"]

    as_of_raw = getattr(args, "as_of", None)
    if as_of_raw:
        as_of = _parse_date(as_of_raw)
        if as_of is None:
            print(f"ERROR: --as-of {as_of_raw!r} is not a valid YYYY-MM-DD date",
                  file=sys.stderr)
            sys.exit(2)
    else:
        as_of = date.today()

    by_company = {}  # norm company -> list of {"anchor", "name", "status"}
    fc_i = CONTACTS_COLS.index("first_contacted")
    for row in ws.iter_rows(min_row=2, values_only=True):
        if not row or not _ccell(row, "company"):
            continue
        # Recruiter contacts neither anchor the clock nor count as a reply.
        if _is_recruiterish_title(_ccell(row, "contact_title")):
            continue
        key = _norm_company(_ccell(row, "company"))
        first = _parse_date(row[fc_i])
        sent = _parse_date(_ccell(row, "sent_date"))
        anchor = sent or first
        status = str(_ccell(row, "status") or "").strip().lower()
        by_company.setdefault(key, []).append({
            "anchor": anchor,
            "name": _ccell(row, "contact_name"),
            "status": status,
        })

    out = []
    for company in companies:
        key = _norm_company(company)
        entries = by_company.get(key, [])
        has_reply = any(e["status"] == "replied" for e in entries)
        dated = [e for e in entries if e["anchor"] is not None]
        if not dated:
            out.append({
                "company": company,
                "in_cooldown": False,
                "last_cold_outreach": None,
                "last_contact_name": None,
                "free_on": None,
                "has_reply": has_reply,
                "cooldown_days": OUTREACH_COOLDOWN_DAYS,
            })
            continue
        latest = max(dated, key=lambda e: e["anchor"])
        free_on = latest["anchor"] + timedelta(days=OUTREACH_COOLDOWN_DAYS)
        out.append({
            "company": company,
            "in_cooldown": (as_of < free_on) and not has_reply,
            "last_cold_outreach": latest["anchor"].isoformat(),
            "last_contact_name": latest["name"],
            "free_on": free_on.isoformat(),
            "has_reply": has_reply,
            "cooldown_days": OUTREACH_COOLDOWN_DAYS,
        })
    return out


def cmd_company_cooldown(args):
    """Read-only: per-company cold outreach cooldown state, one JSON object
    per line, one per requested company.
    """
    companies = list(getattr(args, "company", None) or [])
    if getattr(args, "file", None):
        for ln in Path(args.file).read_text(encoding="utf-8").splitlines():
            ln = ln.strip()
            if not ln or ln.startswith("#"):
                continue
            try:
                obj = json.loads(ln)
            except json.JSONDecodeError as e:
                print(f"ERROR: bad JSON line in {args.file}: {ln!r} ({e})", file=sys.stderr)
                sys.exit(2)
            name = obj.get("company") if isinstance(obj, dict) else None
            if name:
                companies.append(name)
    if not companies:
        print(
            "ERROR: no companies given (use --company, repeatable, or --file "
            "JSON-lines with {\"company\": \"...\"} per line)",
            file=sys.stderr,
        )
        sys.exit(2)
    for result in _outreach_cooldown_for_companies(args, companies):
        print(json.dumps(result))


def cmd_add_job(args):
    path = tracker_path(args)
    wb = load_or_init(path)
    ws = wb["jobs"]
    _warn_unknown_status(args.status)
    new_id = next_id(ws)
    row = {
        "id": new_id,
        "first_seen": _norm_date_str(args.first_seen) or today(),
        "last_updated": today(),
        "company": args.company,
        "role_title": args.role,
        "level": args.level or "",
        "location": args.location or "",
        "source": args.source or "",
        "url": _canon_url(args.url),
        "alt_urls": ";".join(_canon_url(u) for u in str(args.alt_urls).split(";") if u.strip()) if args.alt_urls else "",
        "comp_posted": args.comp_posted or "unknown",
        "fit_score": args.fit if args.fit is not None else "",
        "score_rationale": args.rationale or "",
        "resume_variant": args.resume or "",
        "status": args.status or "surfaced",
        "drafted_date": _norm_date_str(args.drafted_date),
        "submitted_date": _norm_date_str(args.submitted_date),
        "referral_contact": "",
        "referral_sent_date": _norm_date_str(args.referral_sent_date),
        "referral_response": "",
        "review_notes": args.review_notes or "",
        "tab_info": args.tab_info or "",
        "cover_letter_file": args.cover_letter or "",
        "cancellation_reason": getattr(args, "cancellation_reason", None) or "",
    }
    ws.append([row[c] for c in JOBS_COLS])
    _save(wb, path)
    print(json.dumps({"added": True, "id": new_id}))


def cmd_update_job(args):
    path = tracker_path(args)
    wb = load_or_init(path)
    ws = wb["jobs"]
    id_idx = JOBS_COLS.index("id")
    for r_i, row in enumerate(ws.iter_rows(min_row=2), start=2):
        if _id_match(row[id_idx].value, args.id):
            updates = {}
            if args.status:
                _warn_unknown_status(args.status)
                updates["status"] = args.status
            if args.drafted_date:
                updates["drafted_date"] = _norm_date_str(args.drafted_date)
            if args.submitted_date:
                updates["submitted_date"] = _norm_date_str(args.submitted_date)
            if args.referral_contact:
                updates["referral_contact"] = args.referral_contact
            if args.referral_sent_date:
                updates["referral_sent_date"] = _norm_date_str(args.referral_sent_date)
            if args.referral_response:
                updates["referral_response"] = args.referral_response
            if args.review_notes:
                updates["review_notes"] = args.review_notes
            if args.tab_info:
                updates["tab_info"] = args.tab_info
            if args.cover_letter:
                updates["cover_letter_file"] = args.cover_letter
            if getattr(args, "cancellation_reason", None):
                updates["cancellation_reason"] = args.cancellation_reason
            updates["last_updated"] = today()
            for col, val in updates.items():
                c_i = JOBS_COLS.index(col) + 1
                ws.cell(row=r_i, column=c_i).value = val
            _save(wb, path)
            print(json.dumps({"updated": True, "id": args.id, "fields": list(updates.keys())}))
            return
    print(json.dumps({"updated": False, "reason": f"no row with id={args.id}"}))


def cmd_add_contact(args):
    path = tracker_path(args)
    wb = load_or_init(path)
    ws = wb["contacts"]
    new_id = next_id(ws)
    row = {
        "id": new_id,
        "first_contacted": today(),
        "contact_name": args.name,
        "contact_title": args.title or "",
        "company": args.company,
        "connection_degree": args.degree,
        "connection_path": args.path_ctx or "",
        "linkedin_url": args.linkedin or "",
        "message_template": "",  # deprecated: outreach is email only
        # draft_ref (a pointer into the day's outreach file) wins over legacy --draft.
        "message_draft": args.draft_ref or args.draft or "",
        "status": args.status or "drafted",
        "response_summary": "",
        "linked_job_ids": str(args.job_id) if args.job_id else "",
        "sent_date": "",
        "gmail_draft_id": "",
        "gmail_thread_id": "",
        "followup_draft_id": "",
        "cancellation_note_draft_id": "",
        "email": (args.email or "").strip(),
    }
    ws.append([row[c] for c in CONTACTS_COLS])
    _save(wb, path)
    print(json.dumps({"added": True, "id": new_id}))


def cmd_update_contact(args):
    """Update a contact's Gmail and reply state; every flag optional except --id."""
    path = tracker_path(args)
    wb = load_or_init(path)
    ws = wb["contacts"]
    fields = {
        "status": args.status,
        "sent_date": _norm_date_str(args.sent_date) if args.sent_date else None,
        "response_summary": args.response_summary,
        "gmail_draft_id": args.gmail_draft_id,
        "gmail_thread_id": args.gmail_thread_id,
        "followup_draft_id": args.followup_draft_id,
        "cancellation_note_draft_id": getattr(args, "cancellation_note_draft_id", None),
        "message_draft": args.draft_ref,
        "email": args.email.strip() if args.email is not None else None,
    }
    fields = {k: v for k, v in fields.items() if v is not None}
    if not fields:
        print("ERROR: nothing to update; pass at least one field flag", file=sys.stderr)
        sys.exit(2)
    if "status" in fields and str(fields["status"]).lower() not in CONTACT_STATUSES:
        print(f"WARNING: unknown contact status {fields['status']!r} "
              f"(known: {sorted(CONTACT_STATUSES)})", file=sys.stderr)
    for r in ws.iter_rows(min_row=2):
        if _id_match(r[0].value, args.id):
            for name, val in fields.items():
                r[CONTACTS_COLS.index(name)].value = val
            _save(wb, path)
            print(json.dumps({"updated": True, "id": args.id,
                              "fields": sorted(fields)}))
            return
    print(json.dumps({"updated": False, "id": args.id, "error": "id not found"}))
    sys.exit(1)


def cmd_contacts_pending(args):
    """Read-only, for outreach-sync: contacts needing Gmail sync/reconciliation.

    Returns every contact at status drafted or sent, with the Gmail columns and
    day counts. days_since prefers the verified sent_date over first_contacted.
    """
    asof = date.today()
    if getattr(args, "as_of", None):
        parsed = _parse_date(args.as_of)
        if parsed is None:
            print(f"ERROR: bad --as-of {args.as_of!r}", file=sys.stderr)
            sys.exit(2)
        asof = parsed
    path = tracker_path(args)
    wb = load_or_init(path)
    ws = wb["contacts"]
    out = []
    for row in ws.iter_rows(min_row=2, values_only=True):
        if not row or row[0] is None:
            continue
        status = str(_ccell(row, "status") or "").lower()
        if status not in ("drafted", "sent"):
            continue
        first = _parse_date(_ccell(row, "first_contacted"))
        sent = _parse_date(_ccell(row, "sent_date"))
        anchor = sent or first
        out.append({
            "id": row[0],
            "name": _ccell(row, "contact_name"),
            "title": _ccell(row, "contact_title") or "",
            "company": _ccell(row, "company"),
            "status": status,
            "first_contacted": str(_ccell(row, "first_contacted") or "")[:10],
            "sent_date": str(_ccell(row, "sent_date") or "")[:10],
            "days_since": (asof - anchor).days if anchor else None,
            "draft_ref": _ccell(row, "message_draft") or "",
            "gmail_draft_id": _ccell(row, "gmail_draft_id") or "",
            "gmail_thread_id": _ccell(row, "gmail_thread_id") or "",
            "followup_draft_id": _ccell(row, "followup_draft_id") or "",
            "linked_job_ids": str(_ccell(row, "linked_job_ids") or ""),
            "email": _ccell(row, "email") or "",
        })
    print(json.dumps({"as_of": asof.isoformat(), "contacts": out}, indent=2))


def cmd_log_run(args):
    path = tracker_path(args)
    wb = load_or_init(path)
    ws = wb["daily_runs"]
    row = {
        "run_date": today(),
        "roles_surfaced": args.surfaced or 0,
        "top_picks_count": args.top_picks or 0,
        "drafted_count": args.drafted or 0,
        "contacts_drafted": args.contacts or 0,
        "slow_day": (args.top_picks or 0) < SLOW_DAY_THRESHOLD,
        "notes": args.notes or "",
    }
    ws.append([row[c] for c in RUNS_COLS])
    _save(wb, path)
    print(json.dumps({"logged": True, "date": row["run_date"]}))


def cmd_summary(args):
    path = tracker_path(args)
    wb = load_or_init(path)
    ws = wb["jobs"]
    by_status = {}
    total = 0
    for row in ws.iter_rows(min_row=2, values_only=True):
        if not row or row[0] is None:
            continue
        total += 1
        status = row[JOBS_COLS.index("status")] or "unknown"
        by_status[status] = by_status.get(status, 0) + 1
    ws_r = wb["daily_runs"]
    run_count = 0
    last_run_date = None
    rd_i = RUNS_COLS.index("run_date")
    for row in ws_r.iter_rows(min_row=2, values_only=True):
        if not row or not row[0]:
            continue
        run_count += 1
        d = _parse_date(row[rd_i])
        if d is not None and (last_run_date is None or d > last_run_date):
            last_run_date = d
    unknown = sorted(s for s in by_status if s not in KNOWN_STATUSES and s != "unknown")
    out = {
        "total_jobs": total,
        "by_status": by_status,
        "total_runs": run_count,
        # Most recent daily_runs.run_date as ISO, or null when no run is logged.
        "last_run_date": last_run_date.isoformat() if last_run_date else None,
        "tracker_path": path,
    }
    if unknown:
        out["unknown_statuses"] = unknown
    print(json.dumps(out, indent=2))



def _build_url_index(ws):
    """One pass over the jobs sheet: canonical URL -> row summary dict."""
    url_idx = JOBS_COLS.index("url")
    alt_idx = JOBS_COLS.index("alt_urls")
    status_idx = JOBS_COLS.index("status")
    index = {}
    for row in ws.iter_rows(min_row=2, values_only=True):
        if not row:
            continue
        urls = []
        if row[url_idx]:
            urls.append(_canon_url(row[url_idx]))
        if row[alt_idx]:
            urls.extend(_canon_url(u) for u in str(row[alt_idx]).split(";") if u.strip())
        for u in urls:
            if u and u not in index:
                index[u] = row
    return index


def cmd_seen_batch(args):
    """Batch form of `seen`: one workbook load for N URLs, one JSON line each.

    Read-only: never writes, never backs up. Input via --file (one URL per
    line, blank lines and #comments skipped) and/or --urls.
    """
    urls = []
    if args.file:
        for ln in Path(args.file).read_text(encoding="utf-8").splitlines():
            ln = ln.strip()
            if ln and not ln.startswith("#"):
                urls.append(ln)
    if args.urls:
        urls.extend(args.urls)
    if not urls:
        print("ERROR: no URLs given (use --file or --urls)", file=sys.stderr)
        sys.exit(2)
    path = tracker_path(args)
    wb = load_or_init(path)
    index = _build_url_index(wb["jobs"])
    status_idx = JOBS_COLS.index("status")
    for u in urls:
        row = index.get(_canon_url(u))
        if row is None:
            print(json.dumps({"url": u, "seen": False, "suppress": False}))
        else:
            status = row[status_idx]
            _warn_unknown_status(status)
            print(json.dumps({
                "url": u,
                "seen": True,
                "suppress": status in SUPPRESS_STATUSES,
                "id": row[0],
                "company": row[3],
                "role": row[4],
                "status": status,
            }))


def cmd_dup_check(args):
    """Bulk duplicate check: exact URL match (as seen-batch), or a company+
    title match against a row already in a SUPPRESS status, which catches a
    posting reposted under a new URL.

    Read-only. Input via --file, one JSON object per line:
    {"url": "...", "company": "...", "role": "..."} (company and role are
    optional; without them only the URL is checked). Output: one JSON line
    per input with url, seen, suppress, matched_by ("url", "title" or null),
    id, company, role, status. Title matching is exact after case and
    whitespace normalization, not fuzzy.
    """
    if not args.file:
        print("ERROR: --file is required (JSON lines: {\"url\":, \"company\":, \"role\":})", file=sys.stderr)
        sys.exit(2)
    items = []
    for ln in Path(args.file).read_text(encoding="utf-8").splitlines():
        ln = ln.strip()
        if not ln or ln.startswith("#"):
            continue
        try:
            items.append(json.loads(ln))
        except json.JSONDecodeError as e:
            print(f"ERROR: bad JSON line in {args.file}: {ln!r} ({e})", file=sys.stderr)
            sys.exit(2)
    if not items:
        print("ERROR: no candidates given in --file", file=sys.stderr)
        sys.exit(2)
    path = tracker_path(args)
    wb = load_or_init(path)
    ws = wb["jobs"]
    url_index = _build_url_index(ws)
    co_idx = JOBS_COLS.index("company")
    role_idx = JOBS_COLS.index("role_title")
    status_idx = JOBS_COLS.index("status")
    title_index = {}
    for row in ws.iter_rows(min_row=2, values_only=True):
        if not row:
            continue
        status = row[status_idx]
        if status not in SUPPRESS_STATUSES:
            continue
        key = (_norm_company(row[co_idx]), _norm_title(row[role_idx]))
        if key not in title_index:
            title_index[key] = row
    for item in items:
        url = item.get("url", "")
        company = item.get("company", "")
        role = item.get("role", "")
        row = url_index.get(_canon_url(url))
        matched_by = "url" if row is not None else None
        if row is None and company and role:
            row = title_index.get((_norm_company(company), _norm_title(role)))
            if row is not None:
                matched_by = "title"
        if row is None:
            print(json.dumps({"url": url, "seen": False, "suppress": False, "matched_by": None}))
            continue
        status = row[status_idx]
        _warn_unknown_status(status)
        print(json.dumps({
            "url": url,
            "seen": True,
            "suppress": status in SUPPRESS_STATUSES,
            "matched_by": matched_by,
            "id": row[0],
            "company": row[3],
            "role": row[4],
            "status": status,
        }))


# import-run: apply a whole run's tracker writes in ONE load/backup/save.
# Field names mirror the add-job / update-job / add-contact CLI flags.
_IMPORT_JOB_UPDATE_MAP = {
    "status": "status",
    "drafted_date": "drafted_date",
    "submitted_date": "submitted_date",
    "referral_contact": "referral_contact",
    "referral_sent_date": "referral_sent_date",
    "referral_response": "referral_response",
    "review_notes": "review_notes",
    "tab_info": "tab_info",
    "cover_letter": "cover_letter_file",
    "resume": "resume_variant",
    "cancellation_reason": "cancellation_reason",
    "fit": "fit_score",
    "rationale": "score_rationale",
    "level": "level",
    "location": "location",
    "source": "source",
    "comp_posted": "comp_posted",
}
_DATEISH = {"drafted_date", "submitted_date", "referral_sent_date"}


def _import_append_job(ws, d):
    new_id = next_id(ws)
    status = d.get("status") or "surfaced"
    _warn_unknown_status(status)
    row = {
        "id": new_id,
        "first_seen": _norm_date_str(d.get("first_seen")) or today(),
        "last_updated": today(),
        "company": d["company"],
        "role_title": d["role"],
        "level": d.get("level") or "",
        "location": d.get("location") or "",
        "source": d.get("source") or "",
        "url": _canon_url(d["url"]),
        "alt_urls": ";".join(_canon_url(u) for u in str(d.get("alt_urls", "")).split(";") if u.strip()),
        "comp_posted": d.get("comp_posted") or "unknown",
        "fit_score": d.get("fit", ""),
        "score_rationale": d.get("rationale") or "",
        "resume_variant": d.get("resume") or "",
        "status": status,
        "drafted_date": _norm_date_str(d.get("drafted_date")),
        "submitted_date": _norm_date_str(d.get("submitted_date")),
        "referral_contact": d.get("referral_contact") or "",
        "referral_sent_date": _norm_date_str(d.get("referral_sent_date")),
        "referral_response": "",
        "review_notes": d.get("review_notes") or "",
        "tab_info": d.get("tab_info") or "",
        "cover_letter_file": d.get("cover_letter") or "",
        "cancellation_reason": d.get("cancellation_reason") or "",
    }
    ws.append([row[c] for c in JOBS_COLS])
    return new_id


def _import_update_job(ws, d):
    id_idx = JOBS_COLS.index("id")
    for r_i, row in enumerate(ws.iter_rows(min_row=2), start=2):
        if _id_match(row[id_idx].value, d["id"]):
            updated = []
            for key, col in _IMPORT_JOB_UPDATE_MAP.items():
                if key in d and d[key] not in (None, ""):
                    val = d[key]
                    if key in _DATEISH:
                        val = _norm_date_str(val)
                    if key == "status":
                        _warn_unknown_status(val)
                    ws.cell(row=r_i, column=JOBS_COLS.index(col) + 1).value = val
                    updated.append(col)
            ws.cell(row=r_i, column=JOBS_COLS.index("last_updated") + 1).value = today()
            return updated
    raise KeyError(f"no row with id={d['id']}")


def cmd_import_run(args):
    """Apply one run's writes from a JSON file in a single load/backup/save.

    Schema: {"jobs": [...], "contacts": [...], "run_log": {...}} where each
    jobs item either has "id" (update in place) or "company"+"role"+"url"
    (append), contacts items mirror add-contact flags, and run_log mirrors
    log-run flags. Valid items are applied even when other items error;
    exits non-zero if anything failed so the orchestrator can repair.
    """
    data = json.loads(Path(args.file).read_text(encoding="utf-8"))
    path = tracker_path(args)
    wb = load_or_init(path)
    report = {"jobs_added": [], "jobs_updated": [], "contacts_added": [],
              "run_logged": False, "errors": []}

    ws_jobs = wb["jobs"]
    for i, d in enumerate(data.get("jobs", [])):
        try:
            if d.get("id") not in (None, ""):
                cols = _import_update_job(ws_jobs, d)
                report["jobs_updated"].append({"id": d["id"], "fields": cols})
            else:
                missing = [k for k in ("company", "role", "url") if not d.get(k)]
                if missing:
                    raise KeyError(f"missing {missing}")
                new_id = _import_append_job(ws_jobs, d)
                report["jobs_added"].append({"id": new_id, "company": d["company"]})
        except Exception as e:  # keep going; report per item
            report["errors"].append(f"jobs[{i}]: {e}")

    ws_c = wb["contacts"]
    for i, d in enumerate(data.get("contacts", [])):
        try:
            if not d.get("name") or not d.get("company"):
                raise KeyError("missing name/company")
            degree = d.get("degree", "cold")
            if degree not in ("1st", "2nd", "cold"):
                raise ValueError(f"bad degree {degree!r}")
            new_id = next_id(ws_c)
            row = {
                "id": new_id,
                "first_contacted": today(),
                "contact_name": d["name"],
                "contact_title": d.get("title") or "",
                "company": d["company"],
                "connection_degree": degree,
                "connection_path": d.get("path_ctx") or "",
                "linkedin_url": d.get("linkedin") or "",
                "message_template": "",
                # draft_ref (outreach/outreach_<date>.md#<company>) is the
                # preferred value; legacy full-text "draft" still accepted.
                "message_draft": d.get("draft_ref") or d.get("draft") or "",
                "status": d.get("status") or "drafted",
                "response_summary": "",
                "linked_job_ids": str(d.get("job_id") or ""),
                "sent_date": "",
                "gmail_draft_id": "",
                "gmail_thread_id": "",
                "followup_draft_id": "",
                "cancellation_note_draft_id": "",
                "email": str(d.get("email") or "").strip(),
            }
            ws_c.append([row[c] for c in CONTACTS_COLS])
            report["contacts_added"].append({"id": new_id, "name": d["name"]})
        except Exception as e:
            report["errors"].append(f"contacts[{i}]: {e}")

    rl = data.get("run_log")
    if rl:
        try:
            ws_r = wb["daily_runs"]
            top = int(rl.get("top_picks") or 0)
            ws_r.append([{
                "run_date": today(),
                "roles_surfaced": int(rl.get("surfaced") or 0),
                "top_picks_count": top,
                "drafted_count": int(rl.get("drafted") or 0),
                "contacts_drafted": int(rl.get("contacts") or 0),
                "slow_day": top < SLOW_DAY_THRESHOLD,
                "notes": rl.get("notes") or "",
            }[c] for c in RUNS_COLS])
            report["run_logged"] = True
        except Exception as e:
            report["errors"].append(f"run_log: {e}")

    changed = (report["jobs_added"] or report["jobs_updated"]
               or report["contacts_added"] or report["run_logged"])
    if changed:
        _save(wb, path)
    print(json.dumps(report, indent=2))
    if report["errors"]:
        sys.exit(1)



def cmd_merge_reports(args):
    """Fold per-agent report_*.json files into the run.json import-run accepts.

    Never touches the tracker. base.json carries the job metadata and run-log
    skeleton: {"jobs": [...], "run_log": {...}}. Each report's "tracker" block
    merges into the base job matched by company (_norm_company) and its
    "contacts" list is appended, with company and job_id defaulted from the
    matched job. Reports with neither block are noted and skipped. Per-item
    errors print and are skipped; exit 1 if anything failed.
    """
    import glob as _glob
    try:
        base = json.loads(Path(args.base).read_text(encoding="utf-8"))
    except Exception as e:
        print(f"ERROR: cannot read base {args.base}: {e}", file=sys.stderr)
        sys.exit(2)
    jobs = list(base.get("jobs", []))
    contacts = list(base.get("contacts", []))
    run_log = dict(base.get("run_log") or {})
    errors = []
    by_company = {}
    for j in jobs:
        if isinstance(j, dict) and j.get("company"):
            by_company.setdefault(_norm_company(j["company"]), j)

    reports = sorted(_glob.glob(str(Path(args.dir) / "report_*.json")))
    if not reports:
        print(f"WARNING: no report_*.json files found in {args.dir}", file=sys.stderr)
    merged_blocks = 0
    for rp in reports:
        name = Path(rp).name
        try:
            rep = json.loads(Path(rp).read_text(encoding="utf-8"))
        except Exception as e:
            msg = f"{name}: unreadable ({e})"
            print(f"ERROR: {msg}", file=sys.stderr)
            errors.append(msg)
            continue
        if not isinstance(rep, dict):
            msg = f"{name}: not a JSON object"
            print(f"ERROR: {msg}", file=sys.stderr)
            errors.append(msg)
            continue
        tracker = rep.get("tracker")
        rep_contacts = rep.get("contacts") or []
        if not tracker and not rep_contacts:
            print(f"note: {name} carries no tracker block or contacts; skipped")
            continue
        company = rep.get("company") or (tracker or {}).get("company")
        job = by_company.get(_norm_company(company)) if company else None
        if tracker:
            if job is None:
                msg = f"{name}: tracker block but no base job matches company {company!r}"
                print(f"ERROR: {msg}", file=sys.stderr)
                errors.append(msg)
            else:
                for k, v in tracker.items():
                    if k == "company" or v in (None, ""):
                        continue
                    job[k] = v
                if rep.get("cover_letter_path") and not job.get("cover_letter"):
                    job["cover_letter"] = rep["cover_letter_path"]
                merged_blocks += 1
        for i, c in enumerate(rep_contacts):
            try:
                if not isinstance(c, dict) or not c.get("name"):
                    raise KeyError("missing name")
                c = dict(c)
                c.setdefault("company", company or "")
                if not c["company"]:
                    raise KeyError("missing company")
                if job and job.get("id") and not c.get("job_id"):
                    c["job_id"] = job["id"]
                contacts.append(c)
            except Exception as e:
                msg = f"{name} contacts[{i}]: {e}"
                print(f"ERROR: {msg}", file=sys.stderr)
                errors.append(msg)

    # Fill run-log counts the orchestrator no longer needs to compute by hand.
    if "contacts" not in run_log:
        run_log["contacts"] = len(contacts)
    if "drafted" not in run_log:
        run_log["drafted"] = sum(
            1 for j in jobs
            if isinstance(j, dict) and str(j.get("status") or "").lower() in PACKET_STATUSES
        )
    out = {"jobs": jobs, "contacts": contacts, "run_log": run_log}
    Path(args.out).write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(json.dumps({
        "reports_seen": len(reports),
        "tracker_blocks_merged": merged_blocks,
        "jobs": len(jobs),
        "contacts": len(contacts),
        "out": str(args.out),
        "errors": errors,
    }, indent=2))
    if errors:
        sys.exit(1)


def cmd_follow_ups(args):
    """Read-only: what outreach/application motion is due today.

    - contacts_due: contact anchored 5-10 days ago, no response recorded,
      status not a reply/closed status; items age out after day 10.
    - applications_stale: jobs at submitted/applied, submitted_date 7-14 days
      ago. Past 14 days they age out.
    - bench_nudges: recruiter-ish contacts last touched 21+ days ago (max 3).
    """
    asof = date.today()
    if getattr(args, "as_of", None):
        parsed = _parse_date(args.as_of)
        if parsed is None:
            print(f"ERROR: bad --as-of {args.as_of!r}", file=sys.stderr)
            sys.exit(2)
        asof = parsed
    path = tracker_path(args)
    wb = load_or_init(path)

    # A reply, a rejection or a ghosted contact never gets a follow-up draft.
    replied = {"replied", "responded", "call_scheduled", "closed",
               "do_not_contact", "rejected", "ghosted"}
    contacts_due, bench = [], []
    ws = wb["contacts"]
    fc_i = CONTACTS_COLS.index("first_contacted")
    for row in ws.iter_rows(min_row=2, values_only=True):
        if not row or row[0] is None:
            continue
        first = _parse_date(row[fc_i])
        # Prefer the Gmail-verified send date over the drafting date.
        sent = _parse_date(_ccell(row, "sent_date"))
        anchor = sent or first
        if anchor is None:
            continue
        days = (asof - anchor).days
        status = str(row[CONTACTS_COLS.index("status")] or "").lower()
        response = row[CONTACTS_COLS.index("response_summary")]
        title = str(row[CONTACTS_COLS.index("contact_title")] or "")
        item = {
            "name": row[CONTACTS_COLS.index("contact_name")],
            "title": title,
            "company": row[CONTACTS_COLS.index("company")],
            "first_contacted": str(row[fc_i])[:10],
            "days_since": days,
            "status": status,
            "linked_job_ids": str(row[CONTACTS_COLS.index("linked_job_ids")] or ""),
        }
        if response or status in replied:
            continue
        # One follow-up per contact: an existing follow-up draft ends it.
        if str(_ccell(row, "followup_draft_id") or "").strip():
            continue
        if 5 <= days <= 10:
            contacts_due.append(item)
        elif days >= 21 and _is_recruiterish_title(title):
            bench.append(item)
    bench.sort(key=lambda d: -d["days_since"])

    applications_stale = []
    wj = wb["jobs"]
    for row in wj.iter_rows(min_row=2, values_only=True):
        if not row or row[0] is None:
            continue
        status = str(row[JOBS_COLS.index("status")] or "").lower()
        if status not in ("submitted", "applied"):
            continue
        sub = _parse_date(row[JOBS_COLS.index("submitted_date")])
        if sub is None:
            continue
        days = (asof - sub).days
        if 7 <= days <= 14:
            applications_stale.append({
                "id": row[0],
                "company": row[JOBS_COLS.index("company")],
                "role": row[JOBS_COLS.index("role_title")],
                "submitted_date": str(row[JOBS_COLS.index("submitted_date")])[:10],
                "days_since": days,
                "referral_contact": row[JOBS_COLS.index("referral_contact")] or "",
            })

    print(json.dumps({
        "as_of": asof.isoformat(),
        "contacts_due": contacts_due,
        "applications_stale": applications_stale,
        "bench_nudges": bench[:3],
    }, indent=2))


def cmd_funnel(args):
    """Read-only: funnel counts and conversion rates, plus per-source counts.

    All-time by default; --days restricts to rows first_seen within the window.
    Stages (each a superset of the next):
      surfaced:  every row in the jobs sheet
      applied:   has a submitted_date, or status shows application motion
                 (referral_sent, interview*, rejected, no_response, withdrawn)
      response:  status in (interview*, rejected), referral_response is
                 non-blank, or a linked contact is replied/rejected
      interview: status in (interview, interview_scheduled, interview_cancelled)
    Conversion rates are stage over previous stage, 0.0 for an empty denominator.
    """
    path = tracker_path(args)
    wb = load_or_init(path)
    ws = wb["jobs"]

    days = getattr(args, "days", None)
    cutoff = None
    if days is not None:
        if days < 0:
            print("ERROR: --days must be >= 0", file=sys.stderr)
            sys.exit(2)
        cutoff = date.today() - timedelta(days=days)

    # Which jobs (by normalized company+role key) have a contact whose status
    # is replied or rejected; used for the "response" stage.
    contact_signal = {}  # linked job id (str) -> True if replied/rejected
    if "contacts" in wb.sheetnames:
        wc = wb["contacts"]
        for row in wc.iter_rows(min_row=2, values_only=True):
            if not row:
                continue
            status = str(_ccell(row, "status") or "").lower()
            if status not in ("replied", "rejected"):
                continue
            for jid in str(_ccell(row, "linked_job_ids") or "").split(","):
                jid = jid.strip()
                if jid:
                    contact_signal[jid] = True

    surfaced = applied = response = interview = 0
    by_source = {}
    interview_statuses = {"interview", "interview_scheduled", "interview_cancelled"}
    response_statuses = interview_statuses | {"rejected"}

    for row in ws.iter_rows(min_row=2, values_only=True):
        if not row or row[0] is None:
            continue
        if cutoff is not None:
            fs = _parse_date(row[JOBS_COLS.index("first_seen")])
            if fs is None or fs < cutoff:
                continue
        surfaced += 1
        source = row[JOBS_COLS.index("source")] or "unknown"
        by_source[source] = by_source.get(source, 0) + 1

        status = str(row[JOBS_COLS.index("status")] or "").lower()
        submitted = row[JOBS_COLS.index("submitted_date")]
        is_applied = bool(submitted) or status in (
            "referral_sent", "interview", "interview_scheduled",
            "interview_cancelled", "rejected", "no_response", "withdrawn",
        )
        if is_applied:
            applied += 1

        job_id = str(row[JOBS_COLS.index("id")])
        has_response = (
            status in response_statuses
            or bool(row[JOBS_COLS.index("referral_response")])
            or contact_signal.get(job_id, False)
        )
        if has_response:
            response += 1
        if status in interview_statuses:
            interview += 1

    def pct(numer, denom):
        return round(100.0 * numer / denom, 1) if denom else 0.0

    print(json.dumps({
        "as_of": today(),
        "window_days": days,
        "totals": {
            "surfaced": surfaced,
            "applied": applied,
            "response": response,
            "interview": interview,
        },
        "conversion_pct": {
            "applied_of_surfaced": pct(applied, surfaced),
            "response_of_applied": pct(response, applied),
            "interview_of_response": pct(interview, response),
        },
        "by_source": by_source,
    }, indent=2))


def main():
    p = argparse.ArgumentParser(description="Tracker ops for daily job search.")
    p.add_argument("--path", help="Path to the tracker xlsx (required for every command)")
    p.add_argument("--prefs", help="Path to preferences.json (cooldowns, excluded companies)")
    sub = p.add_subparsers(dest="cmd", required=True)

    sub.add_parser("init", help="Create empty tracker if it doesn't exist")

    s = sub.add_parser("seen", help="Check if a URL has been seen before")
    s.add_argument("--url", required=True)

    s = sub.add_parser("blocked-companies", help="List companies currently inside the per-company cooldown window")
    s.add_argument("--cooldown-days", type=int, help="Default cooldown length in days (default from prefs cooldown_days or 7; prefs cooldown_overrides still win)")
    s.add_argument("--as-of", help="Evaluate as of this YYYY-MM-DD date (default today)")

    s = sub.add_parser("company-cooldown", help="Read-only: per-company cold outreach cooldown state (90 days by default; separate from the application cooldown)")
    s.add_argument("--company", action="append", help="Company name to check (repeatable)")
    s.add_argument("--file", help="JSON-lines file: {\"company\": \"...\"} per line, alternative to --company")
    s.add_argument("--as-of", help="Evaluate as of this YYYY-MM-DD date (default today)")

    s = sub.add_parser("add-job", help="Append a new job row")
    s.add_argument("--company", required=True)
    s.add_argument("--role", required=True)
    s.add_argument("--url", required=True)
    s.add_argument("--level")
    s.add_argument("--location")
    s.add_argument("--source")
    s.add_argument("--alt-urls")
    s.add_argument("--comp-posted")
    s.add_argument("--fit", type=float)
    s.add_argument("--rationale")
    s.add_argument("--resume")
    s.add_argument("--cover-letter", help="Relative path to the tailored cover-letter PDF")
    s.add_argument("--status", default="surfaced")
    s.add_argument("--drafted-date")
    s.add_argument("--submitted-date")
    s.add_argument("--referral-sent-date")
    s.add_argument("--review-notes")
    s.add_argument("--tab-info")
    s.add_argument("--first-seen")
    s.add_argument("--cancellation-reason", help="Why an interview was cancelled, when known")

    s = sub.add_parser("update-job", help="Update an existing job row")
    s.add_argument("--id", required=True, type=int)
    s.add_argument("--status")
    s.add_argument("--drafted-date")
    s.add_argument("--submitted-date")
    s.add_argument("--referral-contact")
    s.add_argument("--referral-sent-date")
    s.add_argument("--referral-response")
    s.add_argument("--review-notes")
    s.add_argument("--tab-info")
    s.add_argument("--cover-letter", help="Relative path to the tailored cover-letter PDF")
    s.add_argument("--cancellation-reason", help="Why an interview was cancelled, when known")

    s = sub.add_parser("add-contact", help="Append a contact outreach row")
    s.add_argument("--name", required=True)
    s.add_argument("--company", required=True)
    s.add_argument("--degree", required=True, choices=["1st", "2nd", "cold"])
    s.add_argument("--title")
    s.add_argument("--path-ctx", help="How the candidate is connected to this person")
    s.add_argument("--linkedin")
    s.add_argument("--email", help="Contact's email address (empty when unknown)")
    s.add_argument("--draft", help="Legacy: full outreach email body (To/Subject/Body); prefer --draft-ref")
    s.add_argument("--draft-ref", help="Pointer into the day's outreach file, e.g. outreach/outreach_2026-07-05.md#acme")
    s.add_argument("--status", default="drafted")
    s.add_argument("--job-id", type=int)

    s = sub.add_parser("update-contact", help="outreach-sync: update a contact's Gmail/reply state")
    s.add_argument("--id", required=True, type=int)
    s.add_argument("--status", help="drafted / sent / accepted / replied / ghosted / rejected")
    s.add_argument("--sent-date", help="YYYY-MM-DD the email was ACTUALLY sent (verified in Gmail)")
    s.add_argument("--response-summary")
    s.add_argument("--gmail-draft-id")
    s.add_argument("--gmail-thread-id")
    s.add_argument("--followup-draft-id")
    s.add_argument("--cancellation-note-draft-id", help="Gmail draft id of the one interview-cancellation recovery note")
    s.add_argument("--draft-ref", help="Overwrite the draft_ref pointer (rarely needed)")
    s.add_argument("--email", help="Set the contact's email address")

    s = sub.add_parser("contacts-pending", help="Read-only: contacts at drafted/sent, with Gmail state, for outreach-sync")
    s.add_argument("--as-of", help="Evaluate as of this YYYY-MM-DD date (default today)")

    s = sub.add_parser("log-run", help="Log a daily run")
    s.add_argument("--surfaced", type=int)
    s.add_argument("--top-picks", type=int)
    s.add_argument("--drafted", type=int)
    s.add_argument("--contacts", type=int)
    s.add_argument("--notes")

    s = sub.add_parser("seen-batch", help="Batch `seen`: one workbook load for many URLs (read-only)")
    s.add_argument("--file", help="File with one URL per line")
    s.add_argument("--urls", nargs="*", help="URLs on the command line")

    s = sub.add_parser("dup-check", help="Bulk URL+title duplicate check (catches a posting reposted under a new URL)")
    s.add_argument("--file", required=True, help="JSON-lines file: {\"url\":, \"company\":, \"role\":} per candidate")

    s = sub.add_parser("import-run", help="Apply a whole run's writes from a JSON file in one save")
    s.add_argument("--file", required=True, help="Path to run.json")

    s = sub.add_parser("merge-reports", help="Fold per-agent report_*.json files into a run.json for import-run (no tracker access)")
    s.add_argument("--base", required=True, help="base.json written by the orchestrator (Phase 3 job metadata + run_log)")
    s.add_argument("--dir", required=True, help="Scratch directory holding report_*.json files")
    s.add_argument("--out", required=True, help="Where to write the merged run.json")

    s = sub.add_parser("follow-ups", help="Read-only: contacts due a follow-up, stale applications, recruiter bench")
    s.add_argument("--as-of", help="Evaluate as of this YYYY-MM-DD date (default today)")

    s = sub.add_parser("funnel", help="Read-only: funnel counts, conversion rates, per-source counts")
    s.add_argument("--days", type=int, help="Restrict to roles first_seen within this many days (default: all-time)")

    sub.add_parser("summary", help="Print a summary of the tracker state")

    args = p.parse_args()
    tracker_path(args)
    if args.prefs:
        load_prefs(args.prefs)
    cmd = args.cmd.replace("-", "_")
    func = globals().get(f"cmd_{cmd}")
    if not func:
        print(f"Unknown command: {args.cmd}", file=sys.stderr)
        sys.exit(1)
    func(args)


if __name__ == "__main__":
    main()
