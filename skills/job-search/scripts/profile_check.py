#!/usr/bin/env python3
# skill-version: 2026-10-13
"""Validate a user workspace's profile files and resolve preferences.

Usage:
    profile_check.py --workspace WS [--print-prefs]

Checks WS/profile/: profile.md (non-empty), preferences.json (schema v1:
required function, target_titles non-empty, locations with metros or remote,
application_email that looks like an email, identity.full_name (linkedin_url a full https URL or empty), resume.json (render_resume.validate),
profile_summary.md (exists, at most 2048 bytes), eeo.json (optional; a JSON
object if present; its values are never printed).

Prints {"ok", "missing": [], "errors": [], "warnings": []}.
With --print-prefs prints the merged preferences JSON instead (defaults filled
in) when the profile is valid, so scripts and agents share one resolved view.
Exit codes: 0 ok, 1 not ok, 2 workspace has no profile dir at all (onboarding trigger).
"""
import argparse
import copy
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

FUNCTIONS = {"software_engineering", "sales", "marketing", "other"}
SUMMARY_MAX = 2048
LEVELS = {"intern", "entry", "associate", "mid", "senior", "senior staff", "staff", "lead", "principal", "manager", "director"}
EMAIL = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

PACKS = {
    "software_engineering": ["core", "software-engineering"],
    "sales": ["core", "sales-marketing"],
    "marketing": ["core", "sales-marketing"],
    "other": ["core"],
}

DEFAULTS = {
    "schema_version": 1,
    "function_other": "",
    "identity": {"full_name": "", "phone": "", "linkedin_url": "", "current_employer": "",
                 "current_title": "", "years_experience": "", "pronouns": ""},
    "title_exclude_keywords": [],
    "levels": [],
    "career_stage": "mid",
    "locations": {
        "metros": [],
        "metro_aliases": [],
        "remote": "none",
        "current_city": "",
        "relocating_to": "",
        "relocation_clause_rule": "target_metro_only",
    },
    "comp_floor": {"onsite_or_hybrid": 0, "remote": 0, "currency": "USD", "basis": "total_comp"},
    "excluded_companies": [],
    "dealbreaker_keywords": [],
    "cooldown_days": 7,
    "cooldown_overrides": [],
    "outreach_cooldown_days": 90,
    "picks_per_day": 3,
    "min_score": 7.0,
    "freshness_days": 14,
    "resume_variants": [],
    "extra_sources": [],
    "direct_career_pages": [],
    "gmail_account": "",
    "networking": {"enabled": True, "home_city": "", "virtual_ok": True},
    "work_authorization": "",
    "outreach": {"contact_targets": []},
    "voice": {"banned_words": [], "preferred_verbs": [], "avoid_verbs": []},
    "resume": {"skills_cap": None, "max_pages": 1},
    "cover_letter": {"policy": "field_only", "signoff": ""},
    "models": {"search": "sonnet", "recon": "sonnet", "prefill": "sonnet", "builder": "inherit", "draft": "inherit"},
}


def merge(defaults, user):
    out = copy.deepcopy(defaults)
    for k, v in user.items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = merge(out[k], v)
        else:
            out[k] = v
    return out


def resolve(prefs):
    out = merge(DEFAULTS, prefs)
    if "min_score" not in prefs and out.get("career_stage") == "early":
        out["min_score"] = 6.5
    if not out.get("levels") and out.get("career_stage") == "early":
        out["levels"] = ["entry", "associate"]
    if "source_packs" not in prefs:
        out["source_packs"] = list(PACKS.get(out.get("function"), ["core"]))
    return out


def check_variants(rv, pdir, errors):
    if not isinstance(rv, list):
        errors.append("preferences.json: resume_variants must be a list of {file, use_when}")
        return
    for i, v in enumerate(rv):
        if not isinstance(v, dict) or not all(isinstance(v.get(k), str) and v[k].strip() for k in ("file", "use_when")):
            errors.append(f"preferences.json: resume_variants[{i}] must be an object with non-empty file and use_when")
        elif not os.path.isfile(os.path.join(pdir, v["file"])):
            errors.append(f"preferences.json: resume_variants[{i}] file not found under profile/: {v['file']}")


def check_prefs(prefs, missing, errors, warnings, pdir=""):
    if not isinstance(prefs, dict):
        errors.append("preferences.json: must be a JSON object")
        return
    for f in ("function", "target_titles", "locations", "application_email"):
        if f not in prefs:
            missing.append(f"preferences.json: {f}")
    fn = prefs.get("function")
    if fn is not None and fn not in FUNCTIONS:
        errors.append(f"preferences.json: function {fn!r} must be one of {sorted(FUNCTIONS)}")
    if "target_titles" in prefs:
        tt = prefs["target_titles"]
        if not isinstance(tt, list) or not tt or not all(isinstance(t, str) and t.strip() for t in tt):
            errors.append("preferences.json: target_titles must be a non-empty list of strings")
    if "locations" in prefs:
        loc = prefs["locations"]
        if not isinstance(loc, dict):
            errors.append("preferences.json: locations must be an object")
        else:
            metros = loc.get("metros") or []
            remote = loc.get("remote") or "none"
            if not isinstance(metros, list) or (not metros and remote == "none"):
                errors.append("preferences.json: locations needs at least one metro or remote set to 'us'")
    if "application_email" in prefs:
        e = prefs["application_email"]
        if not isinstance(e, str) or not EMAIL.match(e):
            errors.append("preferences.json: application_email does not look like an email address")
    ident = prefs.get("identity")
    if not isinstance(ident, dict):
        missing.append("preferences.json: identity")
    else:
        if not isinstance(ident.get("full_name"), str) or not ident["full_name"].strip():
            missing.append("preferences.json: identity.full_name")
        li = ident.get("linkedin_url")
        if li not in (None, "") and not (isinstance(li, str) and re.match(r"^https://\S+$", li)):
            errors.append("preferences.json: identity.linkedin_url must be a full https URL (or empty if the user has none)")
    lv = prefs.get("levels")
    if isinstance(lv, list):
        for x in lv:
            if not isinstance(x, str) or x.strip().lower() not in LEVELS:
                warnings.append(f"preferences.json: unknown level {x!r}; use {', '.join(sorted(LEVELS))}")
    if "resume_variants" in prefs:
        check_variants(prefs["resume_variants"], pdir, errors)
    cl = prefs.get("cover_letter")
    if isinstance(cl, dict) and cl.get("policy") not in (None, "field_only", "always"):
        errors.append("preferences.json: cover_letter.policy must be 'field_only' or 'always'")
    known = set(DEFAULTS) | {"function", "target_titles", "application_email", "source_packs"}
    for k in prefs:
        if k not in known:
            warnings.append(f"preferences.json: unknown key {k!r} ignored")


def load_json(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def run(ws):
    """Return (code, result dict, prefs or None)."""
    pdir = os.path.join(ws, "profile")
    missing, errors, warnings = [], [], []
    if not os.path.isdir(pdir):
        return 2, {"ok": False, "missing": ["profile/"], "errors": [], "warnings": []}, None

    pm = os.path.join(pdir, "profile.md")
    if not os.path.isfile(pm):
        missing.append("profile/profile.md")
    elif not open(pm, encoding="utf-8").read().strip():
        errors.append("profile.md: empty")

    prefs = None
    pp = os.path.join(pdir, "preferences.json")
    if not os.path.isfile(pp):
        missing.append("profile/preferences.json")
    else:
        try:
            prefs = load_json(pp)
            check_prefs(prefs, missing, errors, warnings, pdir)
        except ValueError as e:
            errors.append(f"preferences.json: invalid JSON ({e})")
            prefs = None

    rp = os.path.join(pdir, "resume.json")
    if not os.path.isfile(rp):
        missing.append("profile/resume.json")
    else:
        try:
            from render_resume import validate
            for e in validate(load_json(rp)):
                errors.append(f"resume.json: {e}")
        except ValueError as e:
            errors.append(f"resume.json: invalid JSON ({e})")

    sp = os.path.join(pdir, "profile_summary.md")
    if not os.path.isfile(sp):
        missing.append("profile/profile_summary.md")
    else:
        size = os.path.getsize(sp)
        if size > SUMMARY_MAX:
            errors.append(f"profile_summary.md: {size} bytes exceeds the {SUMMARY_MAX} byte limit")

    ep = os.path.join(pdir, "eeo.json")
    if os.path.isfile(ep):
        try:
            if not isinstance(load_json(ep), dict):
                errors.append("eeo.json: must be a JSON object")
        except ValueError:
            errors.append("eeo.json: invalid JSON")

    ok = not missing and not errors
    return (0 if ok else 1), {"ok": ok, "missing": missing, "errors": errors, "warnings": warnings}, prefs


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--workspace", required=True)
    p.add_argument("--print-prefs", action="store_true")
    a = p.parse_args(argv)
    code, res, prefs = run(a.workspace)
    if a.print_prefs and code == 0:
        print(json.dumps(resolve(prefs), indent=2))
    else:
        print(json.dumps(res, indent=2))
    return code


if __name__ == "__main__":
    sys.exit(main())
