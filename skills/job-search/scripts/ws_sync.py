#!/usr/bin/env python3
# skill-version: 2026-10-13
"""Workspace mirror helper for device-folder mode (stdlib only).

In device mode the user's folder lives on their computer. Scripts run in the
container on a local mirror <ws>; this tool moves changes between the two.

  pull       --src STAGED_ROOT --dst WS [--force]
                                            refuses (exit 3) when the mirror has unsynced changes unless --force;
                                            copy staged files into the mirror (overwrite),
                                            then record the baseline <ws>/.ws_manifest.json
  changed    --ws WS                        JSON list of relative paths that are new or differ
                                            from the baseline (junk and the manifest ignored)
  ack        --ws WS [PATH ...]             update the baseline for PATH ... (default: all changed);
                                            a path that no longer exists is dropped from it
  plan-stage --listing JSON --date D [--date D2] [--batch N]
                                            from a device_list_dir recursive result
                                            ({"entries":[{name,type,...}]}, name relative to the
                                            listed folder) print the device-relative files to stage:
                                            profile/**, application_tracker.xlsx, newest tracker
                                            backup, networking/events_log.md, outreach/outreach_*.md from the 31 days before the
                                            newest D (outreach sync reads older drafts),
                                            runs/<D>/**, every runs/*/run_state.json, and the newest
                                            10 runs/*/search_B.json. --batch N prints a list of lists.

Sync-back: `changed`, device_commit_files each path to the same relative path in
the user's folder, then `ack`.
"""
import argparse
import fnmatch
import hashlib
import json
import os
import re
import shutil
import sys
from datetime import date as _date

MANIFEST = ".ws_manifest.json"
JUNK_NAMES = {".DS_Store", MANIFEST}
JUNK_GLOBS = ("*.pyc", "*.tmp", ".~lock.*#", "~$*", "*.swp")
BACKUP = re.compile(r"^application_tracker\.autobak\..+\.xlsx$")
OUTREACH = re.compile(r"^outreach/outreach_(\d{4}-\d{2}-\d{2})\.md$")
OUTREACH_DAYS = 31
RUN_FILE = re.compile(r"^runs/(\d{4}-\d{2}-\d{2})/(.+)$")


def is_junk(rel):
    parts = rel.split("/")
    if rel.startswith("runs/onboarding/"):
        return True
    if "__pycache__" in parts:
        return True
    n = parts[-1]
    return n in JUNK_NAMES or any(fnmatch.fnmatch(n, g) for g in JUNK_GLOBS)


def sha(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def scan(ws):
    out = {}
    for base, dirs, files in os.walk(ws):
        dirs[:] = [d for d in dirs if d != "__pycache__"]
        for n in files:
            rel = os.path.relpath(os.path.join(base, n), ws).replace(os.sep, "/")
            if not is_junk(rel):
                out[rel] = sha(os.path.join(ws, rel))
    return out


def load_manifest(ws):
    try:
        with open(os.path.join(ws, MANIFEST), encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return {}


def save_manifest(ws, man):
    path = os.path.join(ws, MANIFEST)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(man, f, indent=1, sort_keys=True)
        f.write("\n")
    os.replace(tmp, path)


def changed_paths(ws):
    base, now = load_manifest(ws), scan(ws)
    return sorted(p for p, h in now.items() if base.get(p) != h)


def cmd_pull(a):
    if not os.path.isdir(a.src):
        print(f"staged root not found: {a.src}", file=sys.stderr)
        return 2
    if not a.force and os.path.isdir(a.dst):
        dirty = changed_paths(a.dst)
        if dirty:
            print(f"refusing to pull: the mirror has unsynced changes ({len(dirty)}, e.g. {dirty[0]}); "
                  "sync back first (changed, device_commit_files, ack) or pass --force to overwrite", file=sys.stderr)
            return 3
    os.makedirs(a.dst, exist_ok=True)
    for base, dirs, files in os.walk(a.src):
        for n in files:
            s = os.path.join(base, n)
            rel = os.path.relpath(s, a.src)
            if is_junk(rel.replace(os.sep, "/")):
                continue
            d = os.path.join(a.dst, rel)
            os.makedirs(os.path.dirname(d), exist_ok=True)
            shutil.copy2(s, d)
    save_manifest(a.dst, scan(a.dst))
    return 0


def cmd_changed(a):
    print(json.dumps(changed_paths(a.ws)))
    return 0


def cmd_ack(a):
    man = load_manifest(a.ws)
    paths = [p.replace(os.sep, "/") for p in a.paths] or changed_paths(a.ws)
    for p in paths:
        full = os.path.join(a.ws, p)
        if os.path.isfile(full) and not is_junk(p):
            man[p] = sha(full)
        else:
            man.pop(p, None)
    save_manifest(a.ws, man)
    return 0


def cmd_plan(a):
    try:
        with open(a.listing, encoding="utf-8") as f:
            entries = json.load(f)["entries"]
        files = [e["name"].strip("/") for e in entries if e.get("type") == "file"]
    except (OSError, ValueError, KeyError, TypeError) as e:
        print(f"bad listing: {e}", file=sys.stderr)
        return 2
    files = sorted({f for f in files if not is_junk(f)})
    dates = set(a.date or [])
    picked = set()
    backups = []
    search_b = {}
    for f in files:
        m = RUN_FILE.match(f)
        if f.startswith("profile/") or f in ("application_tracker.xlsx", "networking/events_log.md"):
            picked.add(f)
        elif BACKUP.match(f):
            backups.append(f)
        elif m:
            d, rest = m.groups()
            if d in dates or rest == "run_state.json":
                picked.add(f)
            if rest == "search_B.json":
                search_b[d] = f
        elif OUTREACH.match(f) and dates:
            try:
                age = (_date.fromisoformat(max(dates)) - _date.fromisoformat(OUTREACH.match(f).group(1))).days
            except ValueError:
                continue
            if age <= OUTREACH_DAYS:
                picked.add(f)
    if backups:
        picked.add(sorted(backups)[-1])
    for d in sorted(search_b, reverse=True)[:10]:
        picked.add(search_b[d])
    out = sorted(picked)
    if a.batch:
        out = [out[i:i + a.batch] for i in range(0, len(out), a.batch)]
    print(json.dumps(out))
    return 0


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("pull")
    s.add_argument("--src", required=True)
    s.add_argument("--dst", required=True)
    s.add_argument("--force", action="store_true")
    s = sub.add_parser("changed")
    s.add_argument("--ws", required=True)
    s = sub.add_parser("ack")
    s.add_argument("--ws", required=True)
    s.add_argument("paths", nargs="*")
    s = sub.add_parser("plan-stage")
    s.add_argument("--listing", required=True)
    s.add_argument("--date", action="append")
    s.add_argument("--batch", type=int, default=0)
    a = p.parse_args(argv)
    return {"pull": cmd_pull, "changed": cmd_changed, "ack": cmd_ack, "plan-stage": cmd_plan}[a.cmd](a)


if __name__ == "__main__":
    sys.exit(main())
