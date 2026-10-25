#!/usr/bin/env python3
# skill-version: 2026-10-13
"""Render a cover letter JSON into a one-page PDF in the resume's house style.

Usage:
    render_cover_letter.py LETTER_JSON OUT_PDF

LETTER_JSON:
{
  "name": "Full Name",
  "contact": ["City, ST", "phone", "email", "linkedin.com/in/..."],
  "date": "October 13, 2026",
  "recipient_lines": ["Acme Hiring Team", "Acme Corp"],
  "salutation": "Dear Acme Hiring Team,",
  "paragraphs": ["...", "..."],
  "signoff": "Sincerely,"
}
The name is printed under the signoff, so do not repeat it inside signoff.
recipient_lines may be empty. Helvetica, letter size, 1in side margins, the
same centered name and contact header as render_resume.py.

Prints one JSON line to stdout:
    {"ok": bool, "pages": int, "remaining_pt": float, "errors": [...], "warnings": [...]}

Exit codes:
    0  rendered, exactly one page, no content errors
    2  rendered but longer than one page (cut words, never shrink type or margins)
    3  content errors (bad schema, em-dash, spaced hyphen); nothing written
    64 usage
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.platypus import BaseDocTemplate, Frame, PageTemplate, Paragraph, Spacer

import render_resume as rr

PW, PH = letter
LM = RM = 1.0 * inch
TM = 0.8 * inch
BM = 0.8 * inch

body_s = rr.PS("cl_body", fontSize=11, leading=15, spaceAfter=9, alignment=TA_LEFT)
line_s = rr.PS("cl_line", fontSize=11, leading=14, alignment=TA_LEFT)


def _texts(d):
    yield "name", d.get("name", "")
    for i, c in enumerate(d.get("contact") or []):
        yield f"contact[{i}]", c
    yield "date", d.get("date", "")
    for i, c in enumerate(d.get("recipient_lines") or []):
        yield f"recipient_lines[{i}]", c
    yield "salutation", d.get("salutation", "")
    for i, c in enumerate(d.get("paragraphs") or []):
        yield f"paragraphs[{i}]", c
    yield "signoff", d.get("signoff", "")


def validate(d):
    errors = []
    for k in ("name", "date", "salutation", "signoff"):
        if not isinstance(d.get(k), str) or not d[k].strip():
            errors.append(f"{k} is required")
    for k in ("contact", "paragraphs"):
        v = d.get(k)
        if not isinstance(v, list) or not v or not all(isinstance(x, str) and x.strip() for x in v):
            errors.append(f"{k} must be a non-empty list of strings")
    rl = d.get("recipient_lines", [])
    if not isinstance(rl, list) or not all(isinstance(x, str) for x in rl):
        errors.append("recipient_lines must be a list of strings")
    if errors:
        return errors
    for path, text in _texts(d):
        if rr.EM_DASH in text:
            errors.append(f"{path}: contains an em-dash")
        if rr.SPACED_DASH.search(text):
            errors.append(f"{path}: contains a spaced hyphen or dash used as punctuation")
    return errors


def build_story(d):
    story = [Paragraph(rr.t(d["name"]), rr.name_s),
             Paragraph(rr.t("  |  ".join(d["contact"])), rr.contact_s),
             Spacer(1, 14), Paragraph(rr.t(d["date"]), line_s), Spacer(1, 10)]
    rl = d.get("recipient_lines") or []
    if rl:
        story += [Paragraph(rr.t(x), line_s) for x in rl] + [Spacer(1, 10)]
    story.append(Paragraph(rr.t(d["salutation"]), body_s))
    story += [Paragraph(rr.t(p), body_s) for p in d["paragraphs"]]
    story += [Paragraph(rr.t(d["signoff"]), line_s), Spacer(1, 14), Paragraph(rr.t(d["name"]), line_s)]
    return story


def render(d, out_path):
    sink = {}
    frame = Frame(LM, BM, PW - LM - RM, PH - TM - BM, leftPadding=0, rightPadding=0,
                  topPadding=0, bottomPadding=0, id="main")
    doc = BaseDocTemplate(out_path, pagesize=letter, leftMargin=LM, rightMargin=RM,
                          topMargin=TM, bottomMargin=BM, title=d["name"], author=d["name"])
    doc.addPageTemplates([PageTemplate(id="main", frames=[frame])])
    doc.build(build_story(d) + [rr._Marker(sink)])
    return sink.get("page", 1), round(sink.get("y", BM) - BM, 1)


def main(argv):
    args = [a for a in argv[1:] if not a.startswith("--")]
    if len(args) != 2:
        print(__doc__, file=sys.stderr)
        return 64
    src, out = args
    with open(src, encoding="utf-8") as f:
        data = json.load(f)
    errors = validate(data)
    if errors:
        print(json.dumps({"ok": False, "pages": 0, "remaining_pt": 0, "errors": errors, "warnings": []}))
        return 3
    pages, remaining = render(data, out)
    warnings = []
    if pages > 1:
        warnings.append(f"rendered {pages} pages; cut words (never shrink type or margins)")
    print(json.dumps({"ok": pages == 1, "pages": pages, "remaining_pt": remaining,
                      "errors": [], "warnings": warnings}))
    return 0 if pages == 1 else 2


if __name__ == "__main__":
    sys.exit(main(sys.argv))
