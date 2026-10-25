#!/usr/bin/env python3
"""Bundle checker: version stamps, text hygiene, references, phase headers,
load-map budget, private-data scan, stray files. Optional .skill packaging."""
import argparse
import importlib.util
import json
import re
import sys
import zipfile
from pathlib import Path

DEFAULT_ROOT = Path(__file__).resolve().parent.parent
STAMP = re.compile(r"skill-version:\s*([0-9]{4}-[0-9]{2}-[0-9]{2})")
EM = chr(0x2014)
TEXT_EXTS = {".md", ".py", ".json", ".txt", ".yaml", ".yml", ".csv", ".html", ".toml", ".cfg"}
REF = re.compile(r"(?<![A-Za-z0-9_/.\-])((?:phases|rules|sources|scripts|assets)/[A-Za-z0-9_.\-]+)")
HEADER_KEYS = ("Loaded by:", "Reads:", "Writes:")
TABLE_HEADER = "| step | phase file | rules | profile files | runner |"
AGENT_LIMIT = 25600
ORCH_WARN = 16384
ORCH_LIMIT = 20480
STRAY_DIRS = {"__pycache__"}
STRAY_NAMES = {".DS_Store"}


def is_stray(path):
    n = path.name
    return (n in STRAY_NAMES or n.endswith(".pyc") or n.endswith(".tmp")
            or (n.startswith(".~lock.") and n.endswith("#")))


def in_stray_dir(path, root):
    return any(p in STRAY_DIRS for p in path.relative_to(root).parts)


def files_under(root):
    return sorted(p for p in root.rglob("*") if p.is_file())


def text_files(root):
    return [p for p in files_under(root)
            if p.suffix.lower() in TEXT_EXTS and not is_stray(p) and not in_stray_dir(p, root)]


def read(p):
    return p.read_text(encoding="utf-8", errors="replace")


def result(problems=None, warnings=None, **extra):
    problems = problems or []
    out = {"ok": not problems, "problems": problems, "warnings": warnings or []}
    out.update(extra)
    return out


# 1
def check_version(root):
    versions = {}
    for p in text_files(root):
        if p.suffix.lower() not in (".md", ".py"):
            continue
        m = STAMP.search(read(p))
        if m:
            versions[str(p.relative_to(root))] = m.group(1)
    problems = []
    if "SKILL.md" not in versions:
        problems.append("SKILL.md has no skill-version stamp")
    if len(set(versions.values())) > 1:
        problems.append(f"version stamps disagree: {versions}")
    return result(problems)


# 2
def prose_lines(text):
    """Yield (lineno, line) for prose lines: outside fences, code spans removed."""
    fence = False
    for n, line in enumerate(text.splitlines(), 1):
        if line.lstrip().startswith(("```", "~~~")):
            fence = not fence
            continue
        if fence:
            continue
        yield n, re.sub(r"`[^`]*`", "", line)


def dash_problems(line):
    out = []
    if re.search(r"(?<=\s)--(?=\s)|(?<=\w)--(?=\w)|^--(?=\s)|(?<=\s)--$", line):
        out.append("double hyphen used as dash")
    segs = [line]
    stripped = line.strip()
    if stripped.startswith("|"):
        segs = [c.strip() for c in stripped.strip("|").split("|")]
    else:
        segs = [re.sub(r"^\s*[-*+]\s+", "", line)]
    for s in segs:
        if re.search(r"\S\s-\s\S", s):
            out.append("spaced hyphen used as punctuation")
            break
    return out


def check_hygiene(root):
    problems = []
    for p in text_files(root):
        rel = p.relative_to(root)
        text = read(p)
        for n, line in enumerate(text.splitlines(), 1):
            if EM in line:
                problems.append(f"{rel}:{n}: em-dash")
        if p.suffix.lower() == ".md":
            for n, line in prose_lines(text):
                for msg in dash_problems(line):
                    problems.append(f"{rel}:{n}: {msg}")
    return result(problems)


# 3
def check_references(root):
    problems = []
    for p in text_files(root):
        if p.suffix.lower() != ".md":
            continue
        for n, line in enumerate(read(p).splitlines(), 1):
            for m in REF.finditer(line):
                ref = m.group(1).rstrip(".")
                if not (root / ref).exists():
                    problems.append(f"{p.relative_to(root)}:{n}: missing {ref}")
    return result(problems)


# 4
def check_phase_headers(root):
    problems = []
    pdir = root / "phases"
    if not pdir.is_dir():
        return result(["phases/ directory missing"])
    for p in sorted(pdir.glob("*")):
        if not p.is_file() or is_stray(p):
            continue
        head = read(p).splitlines()[:8]
        for key in HEADER_KEYS:
            if not any(l.startswith(key) for l in head):
                problems.append(f"phases/{p.name}: missing '{key}' in first 8 lines")
    return result(problems)


# 5
def parse_load_map(text):
    rows, state = [], 0
    for line in text.splitlines():
        s = line.strip()
        if state == 0:
            if s == TABLE_HEADER:
                state = 1
            continue
        if not s.startswith("|"):
            break
        cells = [c.strip() for c in s.strip("|").split("|")]
        if cells and set("".join(cells)) <= set("-: "):
            continue
        if len(cells) < 5:
            continue
        rows.append(cells[:5])
    return rows if state else None


def split_files(cell):
    out = []
    for part in re.split(r"<br\s*/?>", cell):
        part = part.strip().strip("`").strip()
        if part.startswith("<ws>/"):
            part = part[len("<ws>/"):]
        if part and part.lower() not in ("-", "none", "n/a"):
            out.append(part)
    return out


PLACEHOLDER = "sources/<pack>.md"
READS_REF = re.compile(r"(?:rules|sources)/(?:<pack>\.md|[A-Za-z0-9_.\-]+)")


def expand_files(root, files):
    """Expand the sources placeholder to core.md plus the largest other pack file.
    Returns (files, missing_note or None)."""
    out, note = [], None
    for rel in files:
        if rel != PLACEHOLDER:
            out.append(rel)
            continue
        sdir = root / "sources"
        packs = sorted((p for p in sdir.glob("*.md") if p.name != "core.md"),
                       key=lambda p: p.stat().st_size, reverse=True) if sdir.is_dir() else []
        if not (sdir / "core.md").is_file() or not packs:
            note = f"{PLACEHOLDER} cannot expand (need sources/core.md and at least one pack file)"
            continue
        out += ["sources/core.md", f"sources/{packs[0].name}"]
    return out, note


def check_load_map(root):
    skill = root / "SKILL.md"
    rows = parse_load_map(read(skill)) if skill.exists() else None
    if rows is None:
        return result(["load-map table not found in SKILL.md"])
    problems = []
    for step, phase, rules, _profile, _runner in rows:
        pfiles = split_files(phase)
        if not pfiles:
            continue
        for rel in split_files(rules):
            if not rel.startswith(("rules/", "sources/")):
                problems.append(f"row '{step}': '{rel}' is not a rules/ or sources/ file")
        f = root / pfiles[0]
        if not f.is_file():
            continue
        reads = next((l for l in read(f).splitlines()[:8] if l.startswith("Reads:")), None)
        if reads is None:
            continue
        hdr = {m.group(0).rstrip(".") for m in READS_REF.finditer(reads)}
        row = {r for r in split_files(rules) if r.startswith(("rules/", "sources/"))}
        for rel in sorted(hdr - row):
            problems.append(f"row '{step}': {pfiles[0]} Reads lists {rel} but the load-map row does not")
        for rel in sorted(row - hdr):
            problems.append(f"row '{step}': load-map row lists {rel} but {pfiles[0]} Reads does not")
    return result(problems)


def check_budget(root):
    skill = root / "SKILL.md"
    if not skill.exists():
        return result(["SKILL.md missing"], rows=[])
    rows = parse_load_map(read(skill))
    if rows is None:
        return result([f"load-map table not found in SKILL.md (header: {TABLE_HEADER})"], rows=[])
    problems, warnings, out = [], [], []
    orch = skill.stat().st_size
    for step, phase, rules, _profile, runner in rows:
        total, missing = 0, []
        files, note = expand_files(root, split_files(phase) + split_files(rules))
        if note:
            problems.append(f"row '{step}': {note}")
        for rel in files:
            f = root / rel
            if f.is_file():
                total += f.stat().st_size
            else:
                missing.append(rel)
        if missing:
            problems.append(f"row '{step}': missing files {missing}")
        out.append({"step": step, "runner": runner, "bytes": total})
        low = runner.lower()
        if "agent" in low and total > AGENT_LIMIT:
            problems.append(f"row '{step}': {total} bytes exceeds agent limit {AGENT_LIMIT}")
        if "orchestrator" in low and step != "onboarding":  # one-time step, not part of a run
            orch += total
    if orch > ORCH_LIMIT:
        problems.append(f"orchestrator total {orch} bytes exceeds hard limit {ORCH_LIMIT}")
    elif orch > ORCH_WARN:
        warnings.append(f"orchestrator total {orch} bytes above target {ORCH_WARN}")
    return result(problems, warnings, rows=out, orchestrator_bytes=orch)


# 6
def find_leak_scan(root):
    for base in (root.parent.parent, root.parent):
        cand = base / "dev" / "leak_scan.py"
        if cand.is_file():
            return cand
    return None


def check_pii(root, pii_terms=None):
    if not pii_terms:
        return result(warnings=["no --pii-terms given, private-data scan skipped"])
    leak = find_leak_scan(root)
    if leak is None:
        return result(warnings=["dev/leak_scan.py not found, private-data scan skipped"])
    spec = importlib.util.spec_from_file_location("leak_scan_ext", leak)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    hits = mod.scan_tree(root, mod.load_terms(pii_terms))
    return result([f"private term hit: {h}" for h in hits])


# 7
def check_stray(root):
    bad = [str(p.relative_to(root)) for p in root.rglob("*")
           if is_stray(p) or (p.is_dir() and p.name in STRAY_DIRS)]
    return result([f"stray: {b}" for b in sorted(bad)])


def run_checks(root, pii_terms=None):
    root = Path(root)
    checks = {
        "version": check_version(root),
        "hygiene": check_hygiene(root),
        "references": check_references(root),
        "phase_headers": check_phase_headers(root),
        "load_map": check_load_map(root),
        "budget": check_budget(root),
        "pii": check_pii(root, pii_terms),
        "stray": check_stray(root),
    }
    return {"root": str(root), "ok": all(c["ok"] for c in checks.values()), "checks": checks}


def package(root, out):
    root = Path(root)
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as zf:
        for p in files_under(root):
            if is_stray(p) or in_stray_dir(p, root):
                continue
            zf.write(p, f"{root.name}/{p.relative_to(root)}")


def print_budget(rep):
    b = rep["checks"]["budget"]
    print(f"{'step':<24}{'runner':<16}{'bytes':>8}", file=sys.stderr)
    for r in b.get("rows", []):
        print(f"{r['step']:<24}{r['runner']:<16}{r['bytes']:>8}", file=sys.stderr)
    if "orchestrator_bytes" in b:
        print(f"orchestrator total incl. SKILL.md: {b['orchestrator_bytes']}", file=sys.stderr)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--root", default=str(DEFAULT_ROOT))
    ap.add_argument("--budget", action="store_true", help="print per-row budget table")
    ap.add_argument("--pii-terms")
    ap.add_argument("--package", metavar="OUT.skill")
    a = ap.parse_args(argv)
    rep = run_checks(a.root, a.pii_terms)
    print(json.dumps(rep, indent=2))
    if a.budget:
        print_budget(rep)
    if not rep["ok"]:
        return 1
    if a.package:
        package(a.root, a.package)
    return 0


if __name__ == "__main__":
    sys.exit(main())
