#!/usr/bin/env python3
# skill-version: 2026-10-13
"""Checkpoint state machine so an interrupted run resumes without redoing work.

Subcommands (all print JSON except show):
  init      --runs-dir DIR --date YYYY-MM-DD   create DIR/<date>/run_state.json if missing; print its path
  next      --state PATH [--parallel]          first incomplete unit, or {"step": "done"}
  mark      --state PATH --step S [--role SLUG] --status done|failed|skipped [--output key=path ...] [--force]
  set-roles --state PATH --roles slug1,slug2   ranked role slugs, written at finalize
  show      --state PATH                       compact human summary
  latest    --runs-dir DIR                     newest run whose next step is not done:
                                               {"path","date","next"} or {} when none

Step order: orient, search, finalize, build, contacts, draft, prefill, report, outreach_sync.
Per-role steps (build, contacts, draft, prefill) are tracked per role slug.
Unit ordering for per-role steps (matches the design: build parallel, contacts
sequential, draft parallel, prefill sequential): ALL roles' build first, then
contacts role by role, then ALL roles' draft, then prefill role by role, each
in rank order. `next --parallel` returns every pending unit of the current step
as {"step", "parallel": true, "units": [{"role", "attempts"}], "phase_file"}
for build and draft; for other steps it still returns a single unit.

Semantics:
  done / skipped complete a unit; failed leaves it pending and increments its
  attempts counter (next reports attempts so the router can retry once, then
  do the work inline). A role marked skipped at any step (for example contacts,
  location disqualified) skips all its remaining per-role steps.
  mark verifies every --output file exists (relative paths resolve against the
  run dir, the folder holding the state file); otherwise it exits 1 and writes nothing.
  Marking done is refused (exit 1) while any earlier step, in step order, is pending (a skipped role
  does not block); --force overrides. failed and skipped marks are always allowed.
  Writes are atomic (temp file + rename). Unknown step names exit 2.
"""
import argparse
import json
import os
import re
import sys
import tempfile

STEPS = ["orient", "search", "finalize", "build", "contacts", "draft", "prefill", "report", "outreach_sync"]
PER_ROLE = {"build", "contacts", "draft", "prefill"}
PARALLEL = {"build", "draft"}
PHASE_FILES = {
    "orient": "phases/01-orient.md",
    "search": "phases/02-search-agent.md",
    "finalize": "phases/03-finalize.md",
    "build": "phases/04a-builder-agent.md",
    "contacts": "phases/04b1-contacts-agent.md",
    "draft": "phases/04b2-draft-agent.md",
    "prefill": "phases/04b3-prefill-agent.md",
    "report": "phases/05-report.md",
    "outreach_sync": "phases/06-outreach-sync.md",
}
SLUG = re.compile(r"^[a-z0-9][a-z0-9_-]*$")


def die(msg, code=1):
    print(msg, file=sys.stderr)
    sys.exit(code)


def load(path):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError) as e:
        die(f"cannot read state {path}: {e}")


def save(path, state):
    d = os.path.dirname(os.path.abspath(path))
    fd, tmp = tempfile.mkstemp(dir=d, prefix=".run_state.", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=2)
            f.write("\n")
        os.replace(tmp, path)
    except BaseException:
        if os.path.exists(tmp):
            os.unlink(tmp)
        raise


def blank_unit():
    return {"status": "pending", "attempts": 0, "outputs": {}}


def role_skipped(state, slug):
    for step in PER_ROLE:
        u = state["steps"][step].get("roles", {}).get(slug)
        if u and u["status"] == "skipped":
            return True
    return False


def unit_pending(u):
    return u["status"] not in ("done", "skipped")


def pending_units(state, step):
    """Pending (step, role, unit) tuples for one step, in rank order."""
    if step not in PER_ROLE:
        u = state["steps"][step]
        return [(None, u)] if unit_pending(u) else []
    out = []
    for slug in state["roles"]:
        if role_skipped(state, slug):
            continue
        u = state["steps"][step]["roles"].setdefault(slug, blank_unit())
        if unit_pending(u):
            out.append((slug, u))
    return out


def cmd_init(a):
    d = os.path.join(a.runs_dir, a.date)
    path = os.path.join(d, "run_state.json")
    if not os.path.exists(path):
        os.makedirs(d, exist_ok=True)
        steps = {s: ({"roles": {}} if s in PER_ROLE else blank_unit()) for s in STEPS}
        save(path, {"version": 1, "date": a.date, "roles": [], "steps": steps})
    print(path)


def cmd_next(a):
    state = load(a.state)
    for step in STEPS:
        pend = pending_units(state, step)
        if not pend:
            continue
        base = {"step": step, "phase_file": PHASE_FILES[step]}
        if a.parallel and step in PARALLEL:
            base.update(parallel=True, units=[{"role": r, "attempts": u["attempts"]} for r, u in pend])
        else:
            r, u = pend[0]
            base = {"step": step, "role": r, "phase_file": PHASE_FILES[step], "attempts": u["attempts"]}
        save(a.state, state)
        print(json.dumps(base))
        return
    print(json.dumps({"step": "done"}))


def first_pending(state):
    """The `next` payload for a state without writing anything."""
    for step in STEPS:
        pend = pending_units(state, step)
        if pend:
            r, u = pend[0]
            return {"step": step, "role": r, "phase_file": PHASE_FILES[step], "attempts": u["attempts"]}
    return {"step": "done"}


def cmd_latest(a):
    dates = []
    if os.path.isdir(a.runs_dir):
        for name in os.listdir(a.runs_dir):
            if re.match(r"^\d{4}-\d{2}-\d{2}$", name) and os.path.isfile(os.path.join(a.runs_dir, name, "run_state.json")):
                dates.append(name)
    for d in sorted(dates, reverse=True):
        path = os.path.join(a.runs_dir, d, "run_state.json")
        try:
            state = load(path)
        except SystemExit:
            continue
        nxt = first_pending(state)
        if nxt["step"] != "done":
            print(json.dumps({"path": path, "date": state.get("date", d), "next": nxt}))
            return
    print("{}")


def check_order(state, step, role):
    """Refuse to complete a unit while an earlier unit (step order) is still pending."""
    for prev in STEPS[: STEPS.index(step)]:
        pend = pending_units(state, prev)
        if pend:
            who = f" (role {pend[0][0]})" if pend[0][0] else ""
            if role and prev in PER_ROLE:
                for slug, _ in pend:
                    if slug == role:
                        who = f" (role {role})"
                        break
            die(f"refused: cannot mark {step} done while earlier step {prev}{who} is still pending; "
                f"finish it first or pass --force")


def cmd_mark(a):
    if a.step not in STEPS:
        die(f"unknown step {a.step!r}; valid: {', '.join(STEPS)}", 2)
    state = load(a.state)
    if a.step in PER_ROLE:
        if not a.role:
            die(f"step {a.step} is per-role and needs --role")
        if a.role not in state["roles"]:
            die(f"unknown role {a.role!r}; run set-roles first")
        unit = state["steps"][a.step]["roles"].setdefault(a.role, blank_unit())
    else:
        if a.role:
            die(f"step {a.step} is not per-role; do not pass --role")
        unit = state["steps"][a.step]
    outputs = {}
    run_dir = os.path.dirname(os.path.abspath(a.state))
    for item in a.output or []:
        if "=" not in item or not item.split("=", 1)[0]:
            die(f"bad --output {item!r}, expected key=path")
        k, p = item.split("=", 1)
        full = p if os.path.isabs(p) else os.path.join(run_dir, p)
        if a.status == "done" and not os.path.exists(full):
            die(f"output {k} missing on disk: {full}")
        outputs[k] = p
    if a.status == "done" and not a.force:
        check_order(state, a.step, a.role)
    if a.status == "failed":
        unit["attempts"] += 1
        unit["status"] = "failed"
    else:
        unit["status"] = a.status
    unit["outputs"].update(outputs)
    save(a.state, state)
    print(json.dumps({"step": a.step, "role": a.role, "status": unit["status"], "attempts": unit["attempts"]}))


def cmd_set_roles(a):
    slugs = [s for s in a.roles.split(",") if s.strip()]
    slugs = [s.strip() for s in slugs]
    for s in slugs:
        if not SLUG.match(s):
            die(f"bad role slug {s!r} (lowercase letters, digits, hyphen and underscore)")
    if len(set(slugs)) != len(slugs):
        die("duplicate role slugs")
    state = load(a.state)
    if not a.force:
        for step in PER_ROLE:
            for u in state["steps"][step]["roles"].values():
                if u["status"] in ("done", "skipped"):
                    die("set-roles refused: a per-role step already has a done unit; pass --force to rewrite roles")
    state["roles"] = slugs
    for step in PER_ROLE:
        for s in slugs:
            state["steps"][step]["roles"].setdefault(s, blank_unit())
    save(a.state, state)
    print(json.dumps({"roles": slugs}))


def cmd_show(a):
    state = load(a.state)
    print(f"run {state['date']}  roles: {', '.join(state['roles']) or '(none yet)'}")
    for step in STEPS:
        if step in PER_ROLE:
            parts = []
            for slug in state["roles"]:
                u = state["steps"][step]["roles"].get(slug, blank_unit())
                st = u["status"]
                if st == "pending" and role_skipped(state, slug):
                    st = "skipped"
                parts.append(f"{slug}={st}" + (f"({u['attempts']}x failed)" if u["attempts"] else ""))
            print(f"  {step:14} " + (", ".join(parts) or "(no roles)"))
        else:
            u = state["steps"][step]
            print(f"  {step:14} {u['status']}" + (f" ({u['attempts']}x failed)" if u["attempts"] else ""))


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)
    i = sub.add_parser("init")
    i.add_argument("--runs-dir", required=True)
    i.add_argument("--date", required=True)
    n = sub.add_parser("next")
    n.add_argument("--state", required=True)
    n.add_argument("--parallel", action="store_true")
    m = sub.add_parser("mark")
    m.add_argument("--state", required=True)
    m.add_argument("--step", required=True)
    m.add_argument("--role")
    m.add_argument("--status", required=True, choices=["done", "failed", "skipped"])
    m.add_argument("--output", action="append")
    m.add_argument("--force", action="store_true", help="allow marking done out of step order")
    r = sub.add_parser("set-roles")
    r.add_argument("--state", required=True)
    r.add_argument("--roles", required=True)
    r.add_argument("--force", action="store_true")
    s = sub.add_parser("show")
    s.add_argument("--state", required=True)
    lt = sub.add_parser("latest")
    lt.add_argument("--runs-dir", required=True)
    a = p.parse_args(argv)
    {"latest": cmd_latest, "init": cmd_init, "next": cmd_next, "mark": cmd_mark, "set-roles": cmd_set_roles, "show": cmd_show}[a.cmd](a)


if __name__ == "__main__":
    main()
