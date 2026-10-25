#!/usr/bin/env python3
# skill-version: 2026-10-13
"""Render a resume.json into the one-page house-style PDF.

The house layout: Helvetica, 0.55in side margins, centered name
and contact line, justified summary, gray rules above each section header,
two-column title/date rows, 8pt bullets with a hanging indent.

Usage:
    render_resume.py RESUME_JSON OUT_PDF [--allow-multipage]

Prints one JSON line to stdout:
    {"ok": bool, "pages": int, "remaining_pt": float, "errors": [...], "warnings": [...]}

Exit codes:
    0  rendered, exactly one page, no content errors
    2  rendered but longer than one page (prune content, never shrink the type)
    3  content errors (bad schema, em-dash, spaced hyphen); nothing written

resume.json shape (see assets/sample_resume_early_career.json for a full example):
{
  "name": "...",
  "contact": ["City, ST", "phone", "email", "linkedin.com/in/..."],
  "summary": "optional paragraph",
  "sections": [
    {"type": "skills", "title": "Skills", "items": [{"label": "...", "value": "..."}]},
    {"type": "experience", "title": "Experience", "employers": [
        {"company": "...", "location": "...", "roles": [
            {"title": "...", "dates": "Mon YYYY-Present", "bullets": ["..."]}]}]},
    {"type": "entries", "title": "Projects", "entries": [
        {"title": "...", "dates": "...", "subtitle": "optional", "bullets": ["..."]}]},
    {"type": "lines", "title": "Education", "lines": ["...", "..."]}
  ]
}
Sections render in the order given, so an early-career resume can put
Education first and add Projects or Leadership as "entries" sections.
Every role under an employer is its own titled block with its own bullets;
there is no way to express one pooled bullet list under stacked titles.
"""
import json
import re
import sys
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_RIGHT
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    BaseDocTemplate,
    Flowable,
    Frame,
    HRFlowable,
    KeepTogether,
    PageTemplate,
    Paragraph,
    Table,
    TableStyle,
)

LM = RM = 0.55 * inch
TM = 0.42 * inch
BM = 0.38 * inch
PW, PH = letter
W = PW - LM - RM


def PS(name, **kw):
    base = dict(fontName="Helvetica", fontSize=8.5, leading=11, leftIndent=0,
                rightIndent=0, firstLineIndent=0, spaceAfter=0, spaceBefore=0)
    base.update(kw)
    return ParagraphStyle(name, **base)


name_s = PS("nm", fontName="Helvetica-Bold", fontSize=16, leading=20, spaceAfter=5, alignment=TA_CENTER)
contact_s = PS("ct", fontSize=9, leading=11, spaceAfter=3, alignment=TA_CENTER)
summary_s = PS("sm", fontSize=8.5, leading=11.5, alignment=TA_JUSTIFY)
section_s = PS("sc", fontName="Helvetica-Bold", fontSize=9, leading=11, spaceAfter=1.5, spaceBefore=1)
company_s = PS("co", fontName="Helvetica-Bold", fontSize=9, leading=11, spaceBefore=2)
bullet_s = PS("bl", fontSize=8, leading=11, leftIndent=16, firstLineIndent=-12, spaceAfter=1)
line_s = PS("ln", fontSize=8.5, leading=11, spaceAfter=1)
subtitle_s = PS("st", fontName="Helvetica-Oblique", fontSize=8, leading=10.5, spaceAfter=1)
role_l_s = PS("rl", fontName="Helvetica-Bold", fontSize=8.5, leading=10.5)
role_r_s = PS("rr", fontName="Helvetica-Oblique", fontSize=8, leading=10.5, alignment=TA_RIGHT)

SEP = ' | '  # plain pipe: reads cleanly in every PDF text extractor (the old ZapfDingbats square read as 'n' in some)

# Text rules shared with the writing guidance: no em-dash anywhere, and no
# spaced hyphen or dash used as punctuation. Unspaced hyphens (LLM-driven,
# Nov 2024-Present) are fine.
EM_DASH = "\u2014"
SPACED_DASH = re.compile(r"\s[-–]\s")


class _Marker(Flowable):
    """Zero-size flowable that records where the content ended."""

    def __init__(self, sink):
        super().__init__()
        self.sink = sink

    def wrap(self, aw, ah):
        return 0, 0

    def draw(self):
        x, y = self.canv.absolutePosition(0, 0)
        self.sink["y"] = y
        self.sink["page"] = self.canv.getPageNumber()


def t(s):
    return escape(str(s))


def hr(before=3, after=1.5):
    return HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#aaaaaa"),
                      spaceBefore=before, spaceAfter=after)


def bullet(text):
    return Paragraph(f"• {t(text)}", bullet_s)


def title_row(title, dates):
    tbl = Table([[Paragraph(f"<b>{t(title)}</b>", role_l_s),
                  Paragraph(f"<i>{t(dates or '')}</i>", role_r_s)]],
                colWidths=[W * 0.63, W * 0.37])
    tbl.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "BOTTOM"),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
    ]))
    tbl.hAlign = "LEFT"
    return tbl


def header(title):
    return [hr(), Paragraph(t(title).upper(), section_s)]


# ---------------------------------------------------------------- validation

def _texts(data):
    """Yield (path, text) for every string the resume will print."""
    yield "name", data.get("name", "")
    for i, c in enumerate(data.get("contact", [])):
        yield f"contact[{i}]", c
    if data.get("summary"):
        yield "summary", data["summary"]
    for si, sec in enumerate(data.get("sections", [])):
        p = f"sections[{si}]"
        yield f"{p}.title", sec.get("title", "")
        for i, it in enumerate(sec.get("items", [])):
            yield f"{p}.items[{i}].label", it.get("label", "")
            yield f"{p}.items[{i}].value", it.get("value", "")
        for ei, emp in enumerate(sec.get("employers", [])):
            yield f"{p}.employers[{ei}].company", emp.get("company", "")
            yield f"{p}.employers[{ei}].location", emp.get("location", "")
            for ri, role in enumerate(emp.get("roles", [])):
                q = f"{p}.employers[{ei}].roles[{ri}]"
                yield f"{q}.title", role.get("title", "")
                yield f"{q}.dates", role.get("dates", "")
                for bi, b in enumerate(role.get("bullets", [])):
                    yield f"{q}.bullets[{bi}]", b
        for ni, ent in enumerate(sec.get("entries", [])):
            q = f"{p}.entries[{ni}]"
            for k in ("title", "dates", "subtitle"):
                if ent.get(k):
                    yield f"{q}.{k}", ent[k]
            for bi, b in enumerate(ent.get("bullets", [])):
                yield f"{q}.bullets[{bi}]", b
        for li, line in enumerate(sec.get("lines", [])):
            yield f"{p}.lines[{li}]", line


def validate(data):
    errors = []
    if not isinstance(data.get("name"), str) or not data["name"].strip():
        errors.append("name is required")
    if not isinstance(data.get("contact"), list) or not data["contact"]:
        errors.append("contact must be a non-empty list")
    secs = data.get("sections")
    if not isinstance(secs, list) or not secs:
        errors.append("sections must be a non-empty list")
        secs = []
    for si, sec in enumerate(secs):
        p = f"sections[{si}]"
        typ = sec.get("type")
        if not sec.get("title"):
            errors.append(f"{p}: title is required")
        if typ == "skills":
            items = sec.get("items") or []
            if not items:
                errors.append(f"{p}: skills section needs items")
            for i, it in enumerate(items):
                if not it.get("label") or not it.get("value"):
                    errors.append(f"{p}.items[{i}]: label and value are required")
        elif typ == "experience":
            emps = sec.get("employers") or []
            if not emps:
                errors.append(f"{p}: experience section needs employers")
            for ei, emp in enumerate(emps):
                if not emp.get("company"):
                    errors.append(f"{p}.employers[{ei}]: company is required")
                roles = emp.get("roles") or []
                if not roles:
                    errors.append(f"{p}.employers[{ei}]: needs at least one role")
                for ri, role in enumerate(roles):
                    q = f"{p}.employers[{ei}].roles[{ri}]"
                    if not role.get("title"):
                        errors.append(f"{q}: title is required")
                    if not role.get("dates"):
                        errors.append(f"{q}: dates are required")
                    if not role.get("bullets"):
                        errors.append(f"{q}: every title needs its own bullets (no pooled lists)")
        elif typ == "entries":
            ents = sec.get("entries") or []
            if not ents:
                errors.append(f"{p}: entries section needs entries")
            for ni, ent in enumerate(ents):
                if not ent.get("title"):
                    errors.append(f"{p}.entries[{ni}]: title is required")
        elif typ == "lines":
            if not sec.get("lines"):
                errors.append(f"{p}: lines section needs lines")
        else:
            errors.append(f"{p}: unknown type {typ!r} (skills|experience|entries|lines)")
    for path, text in _texts(data):
        if not isinstance(text, str):
            errors.append(f"{path}: must be a string")
            continue
        if EM_DASH in text:
            errors.append(f"{path}: contains an em-dash")
        if SPACED_DASH.search(text):
            errors.append(f"{path}: contains a spaced hyphen/dash used as punctuation")
    return errors


# ------------------------------------------------------------------- render

def build_story(data):
    story = [Paragraph(t(data["name"]).upper(), name_s),
             Paragraph(SEP.join(t(c) for c in data["contact"]), contact_s)]
    if data.get("summary"):
        story.append(Paragraph(t(data["summary"]), summary_s))

    for sec in data["sections"]:
        typ = sec["type"]
        head = header(sec["title"])
        if typ == "skills":
            rows = [Paragraph(f"<b>{t(it['label'])}:</b> {t(it['value'])}", line_s)
                    for it in sec["items"]]
            story.append(KeepTogether(head + rows))
        elif typ == "lines":
            rows = [Paragraph(t(line), line_s) for line in sec["lines"]]
            story.append(KeepTogether(head + rows))
        elif typ == "experience":
            first = True
            for emp in sec["employers"]:
                comp = emp["company"] + (f" | {emp['location']}" if emp.get("location") else "")
                lead = (head if first else []) + [Paragraph(t(comp), company_s)]
                first = False
                for ri, role in enumerate(emp["roles"]):
                    block = [title_row(role["title"], role["dates"])]
                    block += [bullet(b) for b in role["bullets"]]
                    # Keep each title with its bullets; keep the section and
                    # company header with the first title so neither strands.
                    story.append(KeepTogether((lead if ri == 0 else []) + block))
        elif typ == "entries":
            for ni, ent in enumerate(sec["entries"]):
                block = [title_row(ent["title"], ent.get("dates", ""))]
                if ent.get("subtitle"):
                    block.append(Paragraph(t(ent["subtitle"]), subtitle_s))
                block += [bullet(b) for b in ent.get("bullets", [])]
                story.append(KeepTogether((head if ni == 0 else []) + block))
    return story


def render(data, out_path):
    sink = {}
    frame = Frame(LM, BM, PW - LM - RM, PH - TM - BM, leftPadding=0, rightPadding=0,
                  topPadding=0, bottomPadding=0, id="main")
    doc = BaseDocTemplate(out_path, pagesize=letter, leftMargin=LM, rightMargin=RM,
                          topMargin=TM, bottomMargin=BM, title=data["name"], author=data["name"])
    doc.addPageTemplates([PageTemplate(id="main", frames=[frame])])
    story = build_story(data) + [_Marker(sink)]
    doc.build(story)
    pages = sink.get("page", 1)
    remaining = round(sink.get("y", BM) - BM, 1)
    return pages, remaining


def main(argv):
    args = [a for a in argv[1:] if not a.startswith("--")]
    allow_multi = "--allow-multipage" in argv
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
    ok = pages == 1 or allow_multi
    if pages > 1:
        warnings.append(f"rendered {pages} pages; prune bullets (never shrink type or margins)")
    elif remaining > 60:
        warnings.append(f"{remaining}pt of empty space at the bottom; room for another bullet")
    print(json.dumps({"ok": ok, "pages": pages, "remaining_pt": remaining,
                      "errors": [], "warnings": warnings}))
    return 0 if ok else 2


if __name__ == "__main__":
    sys.exit(main(sys.argv))
