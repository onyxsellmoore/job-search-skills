#!/usr/bin/env python3
# skill-version: 2026-10-13
"""Fabrication and structure guard for a tailored resume.json.

Usage:
    resume_guard.py --base BASE.json --tailored TAILORED.json [--variants-dir DIR]

Prints {"ok": bool, "violations": [...], "warnings": [...]} and exits 0 when ok,
1 when there are violations, 2 when an input cannot be read.
Schema: see the docstring of render_resume.py.

Violations (the tailored resume must not):
  * change name or contact, except the location item (the first contact item
    that looks like "City, ST" in each file); other contact items must match
    in order
  * add a section (type + title) absent from the base; reordering sections is fine
  * change, drop, add or reorder employers (company, location) or roles
    (title, dates)
  * carry a bullet that is not close to a bullet of the SAME role (or entry) in
    the base or any variant. Closeness = max(token Jaccard on content words,
    difflib ratio); a bullet passes at Jaccard >= 0.40 or ratio >= 0.60
    (SIM_JACCARD / SIM_RATIO). A bullet that fits a different role better is
    reported as moved. Dropping bullets (pruning) and reordering are allowed.
  * contain a number token (99.99%, $50K, $150M/year, 50M+, 3+, 12, 2016) that
    appears nowhere in base or variants (summary, bullets, skills, lines)
  * use a skill word absent from the base and variant skills sections, or a
    skill label that does not exist there
  * change an entries item title/dates/subtitle, add an entry, or use an
    education/lines line absent from base or variants
  * fail render_resume.validate (schema, em-dash, spaced hyphen)
Warnings: bullets that pass but sit under 0.60 similarity (heavy rewording),
dropped sections, entries or lines.
Pure standard library apart from importing render_resume.validate.
"""
import argparse
import difflib
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

SIM_JACCARD = 0.40
SIM_RATIO = 0.60
WARN_BELOW = 0.60

STOP = set("a an the and or of to in on for with by from at as is was were be been into onto that this it its "
           "their our across over per than then so but not no".split())
NUM = re.compile(r"\$?\d+(?:,\d{3})*(?:\.\d+)?(?:%|\+|[kmbx](?![a-z]))?(?:\+)?", re.I)
WORD = re.compile(r"[a-z0-9]+(?:[+#.][a-z0-9+#]+)*|[a-z0-9]+")
SKILL_WORD = re.compile(r"[a-z0-9][a-z0-9+#./-]*", re.I)
LOCATION = re.compile(r"^[^@\d/]*,\s*[A-Z]{2}\b")


def numbers(text):
    return {m.group(0).lower() for m in NUM.finditer(text or "")}


def words(text):
    return [w for w in WORD.findall((text or "").lower()) if w not in STOP]


def similarity(a, b):
    wa, wb = set(words(a)), set(words(b))
    jac = len(wa & wb) / len(wa | wb) if wa | wb else 0.0
    ratio = difflib.SequenceMatcher(None, a.lower(), b.lower()).ratio()
    return jac, ratio


def passes(jac, ratio):
    return jac >= SIM_JACCARD or ratio >= SIM_RATIO


def score(a, b):
    jac, ratio = similarity(a, b)
    return max(jac / SIM_JACCARD, ratio / SIM_RATIO) * 0.5  # 0.5 == pass threshold


def best(text, pool):
    return max((score(text, p) for p in pool), default=0.0)


def is_location(item):
    low = item.lower()
    return bool(LOCATION.match(item)) and "linkedin" not in low and "http" not in low and ".com" not in low


def strip_location(contact):
    out, done = [], False
    for c in contact:
        if not done and is_location(c):
            done = True
            continue
        out.append(c)
    return out


def all_text(doc):
    """Every free-text string in a resume (excludes nothing; used for number pool)."""
    out = [doc.get("name", ""), doc.get("summary", "")] + list(doc.get("contact", []))
    for s in doc.get("sections", []):
        t = s.get("type")
        if t == "skills":
            out += [i.get("label", "") + " " + i.get("value", "") for i in s.get("items", [])]
        elif t == "experience":
            for e in s.get("employers", []):
                for r in e.get("roles", []):
                    out += [r.get("dates", "")] + list(r.get("bullets", []))
        elif t == "entries":
            for e in s.get("entries", []):
                out += [e.get("title", ""), e.get("dates", ""), e.get("subtitle", "")] + list(e.get("bullets", []))
        elif t == "lines":
            out += list(s.get("lines", []))
    return out


def sections_of(doc, typ):
    return [s for s in doc.get("sections", []) if s.get("type") == typ]


def role_key(emp, role):
    return (emp.get("company"), role.get("title"), role.get("dates"))


def check(base, tailored, variants):
    from render_resume import validate
    V, W = [], []
    errs = validate(tailored)
    if errs:
        return [f"schema: {e}" for e in errs], W
    docs = [base] + variants

    # name and contact
    if tailored.get("name") != base.get("name"):
        V.append(f"name changed: {base.get('name')!r} -> {tailored.get('name')!r}")
    if strip_location(tailored.get("contact", [])) != strip_location(base.get("contact", [])):
        V.append("contact changed (only the location item may differ)")

    # sections
    bkeys = {(s["type"], s["title"]) for s in base["sections"]}
    tkeys = [(s["type"], s["title"]) for s in tailored["sections"]]
    for k in tkeys:
        if k not in bkeys:
            V.append(f"new section not in base: {k[1]!r} ({k[0]})")
    for k in bkeys - set(tkeys):
        W.append(f"section dropped: {k[1]!r}")

    # numbers
    pool_nums = set()
    for d in docs:
        for t in all_text(d):
            pool_nums |= numbers(t)
    seen = set()
    for t in all_text(tailored):
        for n in numbers(t):
            if n not in pool_nums and n not in seen:
                seen.add(n)
                V.append(f"number token not in base or variants: {n!r}")

    # skills
    skill_labels, skill_words = set(), set()
    for d in docs:
        for s in sections_of(d, "skills"):
            for it in s.get("items", []):
                skill_labels.add(it["label"].strip().lower())
                skill_words |= {w.lower() for w in SKILL_WORD.findall(it["value"])}
    for s in sections_of(tailored, "skills"):
        for it in s.get("items", []):
            if it["label"].strip().lower() not in skill_labels:
                V.append(f"new skill category: {it['label']!r}")
            for w in SKILL_WORD.findall(it["value"]):
                if w.lower() not in skill_words:
                    V.append(f"skill not in base or variants: {w!r}")

    # experience
    bexp = [(s, e) for s in sections_of(base, "experience") for e in s["employers"]]
    texp = [(s, e) for s in sections_of(tailored, "experience") for e in s["employers"]]
    # role -> candidate bullets from base+variants, keyed by (company, title, dates)
    pools = {}
    for d in docs:
        for s in sections_of(d, "experience"):
            for e in s["employers"]:
                for r in e["roles"]:
                    pools.setdefault(role_key(e, r), []).extend(r.get("bullets", []))
    if len(texp) != len(bexp):
        V.append(f"employer count changed: {len(bexp)} -> {len(texp)} (employers may not be dropped or added)")
    for i, (_, te) in enumerate(texp[:len(bexp)]):
        be = bexp[i][1]
        if te.get("company") != be.get("company"):
            V.append(f"employer {i + 1} company changed or reordered: {be.get('company')!r} -> {te.get('company')!r}")
            continue
        if te.get("location") != be.get("location"):
            V.append(f"{be['company']}: location changed {be.get('location')!r} -> {te.get('location')!r}")
        troles, broles = te["roles"], be["roles"]
        if len(troles) != len(broles):
            V.append(f"{be['company']}: role count changed {len(broles)} -> {len(troles)} (roles may not be dropped or added)")
        for j, tr in enumerate(troles[:len(broles)]):
            br = broles[j]
            if tr.get("title") != br.get("title"):
                V.append(f"{be['company']}: title changed or reordered: {br.get('title')!r} -> {tr.get('title')!r}")
                continue
            if tr.get("dates") != br.get("dates"):
                V.append(f"{be['company']} / {br['title']}: dates changed {br.get('dates')!r} -> {tr.get('dates')!r}")
            own = pools.get(role_key(be, br), [])
            others = [(k, v) for k, v in pools.items() if k != role_key(be, br)]
            for b in tr.get("bullets", []):
                s_own = best(b, own)
                if s_own >= 0.5:
                    jac = max((similarity(b, p)[0] for p in own), default=0)
                    rat = max((similarity(b, p)[1] for p in own), default=0)
                    if max(jac, rat) < WARN_BELOW:
                        W.append(f"{br['title']}: heavily reworded bullet: {b[:60]!r}")
                    continue
                other = max(((best(b, v), k) for k, v in others), default=(0.0, None))
                if other[0] >= 0.5:
                    V.append(f"bullet moved from {other[1][0]} / {other[1][1]} into {be['company']} / {br['title']}: {b[:60]!r}")
                else:
                    V.append(f"bullet not traceable to {be['company']} / {br['title']}: {b[:60]!r}")

    # entries
    epool, emeta = {}, {}
    for d in docs:
        for s in sections_of(d, "entries"):
            for e in s["entries"]:
                epool.setdefault(e["title"], []).extend(e.get("bullets", []))
                emeta.setdefault(e["title"], e)
    base_titles = {e["title"] for s in sections_of(base, "entries") for e in s["entries"]}
    tail_titles = set()
    for s in sections_of(tailored, "entries"):
        for e in s["entries"]:
            tail_titles.add(e["title"])
            if e["title"] not in epool:
                V.append(f"new entry not in base: {e['title']!r}")
                continue
            m = emeta[e["title"]]
            for f in ("dates", "subtitle"):
                if e.get(f) != m.get(f):
                    V.append(f"entry {e['title']!r}: {f} changed {m.get(f)!r} -> {e.get(f)!r}")
            for b in e.get("bullets", []):
                if best(b, epool[e["title"]]) < 0.5:
                    V.append(f"entry {e['title']!r}: bullet not traceable: {b[:60]!r}")
    for t in base_titles - tail_titles:
        W.append(f"entry dropped: {t!r}")

    # lines
    lpool = {l.strip() for d in docs for s in sections_of(d, "lines") for l in s["lines"]}
    tlines = set()
    for s in sections_of(tailored, "lines"):
        for l in s["lines"]:
            tlines.add(l.strip())
            if l.strip() not in lpool:
                V.append(f"line not in base or variants ({s['title']}): {l[:60]!r}")
    for l in {l.strip() for s in sections_of(base, "lines") for l in s["lines"]} - tlines:
        W.append(f"line dropped: {l[:60]!r}")
    return V, W


def read_json(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--base", required=True)
    p.add_argument("--tailored", required=True)
    p.add_argument("--variants-dir")
    a = p.parse_args(argv)
    try:
        base, tailored = read_json(a.base), read_json(a.tailored)
    except (OSError, ValueError) as e:
        print(json.dumps({"ok": False, "violations": [f"cannot read input: {e}"], "warnings": []}))
        return 2
    variants, vwarn = [], []
    if a.variants_dir and os.path.isdir(a.variants_dir):
        for fn in sorted(os.listdir(a.variants_dir)):
            if fn.endswith(".json"):
                try:
                    variants.append(read_json(os.path.join(a.variants_dir, fn)))
                except (OSError, ValueError) as e:
                    vwarn.append(f"variant {fn} unreadable: {e}")
    V, W = check(base, tailored, variants)
    out = {"ok": not V, "violations": V, "warnings": vwarn + W}
    print(json.dumps(out, indent=2))
    return 0 if out["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
