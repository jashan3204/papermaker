from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Inches, Pt
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.text.paragraph import Paragraph

BASE_DIR = Path(__file__).resolve().parent
TEMPLATE_PATH = BASE_DIR / "assets" / "template_grg.docx"
MODEL_PATH = BASE_DIR / "assets" / "model sample paper.docx"

SYSTEM_PROMPT = r"""
You are an expert school examination paper parser. Extract the user's complete forwarded message into structured data for a Hindi/Punjabi/English examination paper.

CRITICAL RULES:
- Preserve every supplied word and question in the original language. Do not answer, solve, translate, proofread, shorten, or omit anything.
- Preserve order, numbering, choices, passages, poem line breaks, word limits, hints, general instructions, and OR alternatives.
- Use the original message as the only source for exam details. Do not copy sample/template exam-specific values.
- Separate fixed exam metadata, general instructions, and an ordered list of document blocks.
- A block can be: section (section heading/subtitle), question (main question heading/prompt), text (passage, poem, options, sub-question, hint, or continuation), or spacer.
- For each main question, assign a stable id such as Q1, Q2, etc. Preserve its visible question number in `label` exactly as supplied (e.g. प्रश्न 1., ਪ੍ਰਸ਼ਨ 1., Q1.).
- `effective_marks` means the marks a student can actually earn for that main question after applying its internal choices. It must not double-count OR alternatives or optional subquestions. If uncertain or not stated, use null.
- `attempt_count` is the number of responses required when a question says attempt any N of M. Otherwise null.
- `marks_notation` preserves the source's notation, e.g. (6×1=6), (2×4=8). Do not invent a notation.
- `section_total` is the stated section total if explicit; otherwise null.
- `suggested_marks` may be proposed only when a question's marks are missing and the context gives a reasonable basis. Keep the proposal separate from confirmed effective_marks; never treat it as approved.
- For a section where a choice rule spans several subquestions, assign the effective total to the main question and do not also count subquestions separately.
- If message is ambiguous, include a warning rather than inventing.

Return valid JSON only, matching this shape:
{
 "metadata":{"class":"","subject":"","exam_title":"","session":"","time":"","max_marks":null},
 "general_instructions":["..."],
 "blocks":[
  {"type":"section","text":"...","subtitle":""},
  {"type":"question","id":"Q1","label":"Question 1.","text":"full main question prompt, including marks notation if present","marks_notation":"(6×1=6)","effective_marks":6,"attempt_count":null,"suggested_marks":null},
  {"type":"text","text":"passage, poem, sub-question, options, hints, OR line, or continuation"}
 ],
 "questions":[{"id":"Q1","label":"Question 1.","section":"Section title","marks_notation":"(6×1=6)","effective_marks":6,"attempt_count":null,"suggested_marks":null,"reason":"brief basis for marks or why unknown"}],
 "section_totals":[{"section":"Section title","stated_total":20}],
 "warnings":[]
}

Every main question in blocks must also appear once in questions. Do not duplicate it in blocks. For subquestions, place them as text blocks after the main question. Keep all actual text in `blocks` so it can be typeset in order.
"""


def parse_with_gemini(api_key: str, message: str, model: str = "gemini-2.5-flash") -> dict[str, Any]:
    from google import genai
    from google.genai import types

    client = genai.Client(api_key=api_key)
    response = client.models.generate_content(
        model=model,
        contents=[SYSTEM_PROMPT, "\nFORWARDED QUESTION SET:\n", message],
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            temperature=0.1,
        ),
    )
    raw = response.text or ""
    raw = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw.strip(), flags=re.I)
    data = json.loads(raw)
    if not isinstance(data, dict) or "metadata" not in data or "blocks" not in data:
        raise ValueError("Gemini response ka structure sahi nahi hai. Dobara parse karke dekhein.")
    data.setdefault("questions", [])
    data.setdefault("general_instructions", [])
    data.setdefault("section_totals", [])
    data.setdefault("warnings", [])
    for question in data.get("questions", []):
        question.setdefault("original_effective_marks", question.get("effective_marks"))
    return data


def _is_gurmukhi(text: str) -> bool:
    return any("\u0A00" <= ch <= "\u0A7F" for ch in text)


def _is_devanagari(text: str) -> bool:
    return any("\u0900" <= ch <= "\u097F" for ch in text)


def font_for(text: str) -> str:
    if _is_gurmukhi(text):
        return "Noto Sans Gurmukhi"
    if _is_devanagari(text):
        return "Noto Sans Devanagari"
    return "Times New Roman"


def _script_for_char(ch: str, previous: str) -> str:
    code = ord(ch)
    if 0x0A00 <= code <= 0x0A7F:
        return "Noto Sans Gurmukhi"
    if 0x0900 <= code <= 0x097F:
        return "Noto Sans Devanagari"
    if ch.isalnum() and ord(ch) < 128:
        return "Times New Roman"
    return previous or "Times New Roman"


def add_script_runs(paragraph, text: str, size: float, bold: bool | None):
    chunks = []
    current_font = ""
    current_text = ""
    for ch in text:
        next_font = _script_for_char(ch, current_font)
        if current_text and next_font != current_font:
            chunks.append((current_font, current_text))
            current_text = ""
        current_font = next_font
        current_text += ch
    if current_text:
        chunks.append((current_font, current_text))
    for font_name, chunk in chunks:
        run = paragraph.add_run(chunk)
        set_run_font(run, font_name, size, bold)


def set_run_font(run, font_name: str, size: float = 11, bold: bool | None = None):
    run.font.name = font_name
    run.font.size = Pt(size)
    if bold is not None:
        run.bold = bold
    rpr = run._element.get_or_add_rPr()
    rfonts = rpr.rFonts
    if rfonts is None:
        rfonts = OxmlElement("w:rFonts")
        rpr.insert(0, rfonts)
    for key in ("ascii", "hAnsi", "cs", "eastAsia"):
        rfonts.set(qn(f"w:{key}"), font_name)


def set_cell_text(cell, lines: list[str], bold_first: bool = False):
    cell.text = ""
    for i, line in enumerate(lines):
        p = cell.paragraphs[0] if i == 0 else cell.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        r = p.add_run(line)
        set_run_font(r, font_for(line), 12 if i == 0 else 11, bold=(bold_first or i == 0))


def add_paragraph_after(anchor: Paragraph, text: str = "", *, bold: bool = False,
                        align=None, size: float = 11, keep_with_next: bool = False,
                        space_before: float = 0, space_after: float = 3) -> Paragraph:
    new_p = OxmlElement("w:p")
    anchor._p.addnext(new_p)
    p = Paragraph(new_p, anchor._parent)
    p.paragraph_format.space_before = Pt(space_before)
    p.paragraph_format.space_after = Pt(space_after)
    p.paragraph_format.line_spacing = 1.05
    p.paragraph_format.keep_with_next = keep_with_next
    if align is not None:
        p.alignment = align
    if text:
        add_script_runs(p, text, size, bold)
    return p


def _remove_body_after(doc: Document, anchor: Paragraph):
    body = doc._element.body
    found = False
    for child in list(body):
        if child is anchor._p:
            found = True
            continue
        if found and child.tag != qn("w:sectPr"):
            body.remove(child)


def _set_metadata(doc: Document, metadata: dict[str, Any]):
    if not doc.tables:
        return
    table = doc.tables[0]
    # Template's first row has a merged heading cell (cells 1-4 are the same merged cell).
    header_cell = table.cell(0, 1)
    school = "G.R.G. National Girls Sr. Secondary School"
    title = " ".join(x for x in [str(metadata.get("exam_title") or "").strip(), str(metadata.get("session") or "").strip()] if x)
    lines = [school, title, "", f"Class : {metadata.get('class') or ''}", f"Subject : {metadata.get('subject') or ''}"]
    set_cell_text(header_cell, lines, bold_first=True)
    if len(table.rows) > 1:
        time_cell = table.cell(1, 0)
        max_cell = table.cell(1, 3)
        time_cell.text = f"Time : {metadata.get('time') or ''}"
        max_cell.text = f"Max Marks : {metadata.get('max_marks') if metadata.get('max_marks') is not None else ''}"
        for cell in (time_cell, max_cell):
            for p in cell.paragraphs:
                for r in p.runs:
                    set_run_font(r, "Times New Roman", 11, True)
    # If an older template contains a Set field, remove that text without altering other cells.
    for row in table.rows:
        for cell in row.cells:
            if "Set" in cell.text:
                cell.text = re.sub(r"\bSet\s*:?\s*[^\n]*", "", cell.text, flags=re.I)


def build_docx(data: dict[str, Any], images_by_question: dict[str, bytes] | None = None) -> bytes:
    if not TEMPLATE_PATH.exists() or not MODEL_PATH.exists():
        raise FileNotFoundError("Bundled template ya model paper asset missing hai.")
    doc = Document(str(TEMPLATE_PATH))
    _set_metadata(doc, data.get("metadata", {}))
    gi = next((p for p in doc.paragraphs if "General Instructions" in p.text), None)
    if gi is None:
        raise ValueError("Template mein General Instructions heading nahi mili.")
    _remove_body_after(doc, gi)

    anchor = gi
    instructions = data.get("general_instructions") or []
    for instruction in instructions:
        anchor = add_paragraph_after(anchor, str(instruction), size=10.5, space_after=1)
    if instructions:
        anchor = add_paragraph_after(anchor, "", space_after=4)

    images_by_question = images_by_question or {}
    inserted_images: set[str] = set()
    for block in data.get("blocks", []):
        kind = block.get("type", "text")
        text = str(block.get("text", "") or "")
        if kind == "spacer":
            anchor = add_paragraph_after(anchor, "", space_after=2)
            continue
        if kind == "section":
            heading = text.strip()
            subtitle = str(block.get("subtitle", "") or "").strip()
            anchor = add_paragraph_after(anchor, heading, bold=True, align=WD_ALIGN_PARAGRAPH.CENTER,
                                         size=12, keep_with_next=True, space_before=8, space_after=2)
            if subtitle:
                anchor = add_paragraph_after(anchor, subtitle, bold=True, align=WD_ALIGN_PARAGRAPH.CENTER,
                                             size=10.5, keep_with_next=True, space_after=5)
            continue
        if kind == "question":
            qid = str(block.get("id", ""))
            label = str(block.get("label", "") or "")
            # Preserve original question prompt exactly; the label is metadata for image placement only.
            anchor = add_paragraph_after(anchor, text, bold=True, size=10.5, keep_with_next=True,
                                         space_before=4, space_after=2)
            if qid in images_by_question and qid not in inserted_images:
                p = add_paragraph_after(anchor, "", align=WD_ALIGN_PARAGRAPH.CENTER, space_after=4)
                with tempfile.NamedTemporaryFile(suffix=".img", delete=False) as tmp:
                    tmp.write(images_by_question[qid])
                    tmp_path = tmp.name
                try:
                    run = p.add_run()
                    run.add_picture(tmp_path, width=Inches(5.8))
                finally:
                    os.unlink(tmp_path)
                anchor = p
                inserted_images.add(qid)
            continue
        # Body text: retain supplied text and line breaks; do not bold every passage.
        anchor = add_paragraph_after(anchor, text, bold=False, size=10.5, space_after=2)

    missing_image_ids = set(images_by_question) - inserted_images
    if missing_image_ids:
        raise ValueError("In image question IDs ko document mein nahi mila: " + ", ".join(sorted(missing_image_ids)))

    # Apply the script-specific fonts to all body runs while retaining bold/size settings.
    for p in doc.paragraphs:
        for run in p.runs:
            if run.text:
                set_run_font(run, font_for(run.text), run.font.size.pt if run.font.size else 10.5, run.bold)
    # Preserve template footer, but explicitly set Latin font.
    for section in doc.sections:
        for p in section.footer.paragraphs:
            for run in p.runs:
                set_run_font(run, "Times New Roman", 8)
    out = tempfile.NamedTemporaryFile(suffix=".docx", delete=False)
    out.close()
    try:
        doc.save(out.name)
        return Path(out.name).read_bytes()
    finally:
        Path(out.name).unlink(missing_ok=True)


def _install_bundled_fonts():
    font_dir = Path.home() / ".local" / "share" / "fonts"
    font_dir.mkdir(parents=True, exist_ok=True)
    bundled = BASE_DIR / "assets" / "fonts"
    for font_file in bundled.glob("*.ttf"):
        target = font_dir / font_file.name
        if not target.exists():
            shutil.copy2(font_file, target)
    fc_cache = shutil.which("fc-cache")
    if fc_cache:
        subprocess.run([fc_cache, "-f", str(font_dir)], capture_output=True, timeout=20)


def convert_docx_to_pdf(docx_bytes: bytes) -> bytes:
    _install_bundled_fonts()
    executable = shutil.which("libreoffice") or shutil.which("soffice")
    if not executable:
        raise RuntimeError("Is hosting environment mein LibreOffice available nahi hai; PDF export nahi ho saka.")
    with tempfile.TemporaryDirectory() as tmpdir:
        src = Path(tmpdir) / "paper.docx"
        src.write_bytes(docx_bytes)
        profile = Path(tmpdir) / "lo-profile"
        cmd = [executable, "-env:UserInstallation=" + profile.as_uri(), "--headless", "--convert-to", "pdf", "--outdir", tmpdir, str(src)]
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=90)
        pdf_path = Path(tmpdir) / "paper.pdf"
        if proc.returncode != 0 or not pdf_path.exists() or pdf_path.stat().st_size == 0:
            detail = (proc.stderr or proc.stdout or "Unknown LibreOffice error")[-1200:]
            raise RuntimeError("PDF conversion fail hui: " + detail)
        return pdf_path.read_bytes()


def calculate_total(questions: list[dict[str, Any]]) -> tuple[int, list[str]]:
    total = 0
    missing = []
    for q in questions:
        marks = q.get("effective_marks")
        if marks is None or str(marks).strip() == "":
            missing.append(str(q.get("id") or q.get("label") or "Unknown question"))
            continue
        try:
            total += int(float(marks))
        except (TypeError, ValueError):
            missing.append(str(q.get("id") or q.get("label") or "Unknown question"))
    return total, missing


def update_block_marks(data: dict[str, Any]):
    """Reflect user-confirmed effective marks into question prompt text when notation is absent."""
    by_id = {str(q.get("id")): q for q in data.get("questions", [])}
    for block in data.get("blocks", []):
        if block.get("type") != "question":
            continue
        q = by_id.get(str(block.get("id")))
        if not q:
            continue
        notation = str(q.get("marks_notation") or "").strip()
        current = str(block.get("text", ""))
        effective = q.get("effective_marks")
        original = q.get("original_effective_marks")
        changed = effective is not None and original is not None and int(effective) != int(original)
        if changed:
            # The user changed the effective allocation; replace a trailing source marks group.
            current = re.sub(r"\s*[（(][^()（）]*[)）]\s*$", "", current)
            block["text"] = current.rstrip() + f" ({int(effective)})"
        elif notation and notation not in current:
            block["text"] = current.rstrip() + " " + notation
        elif not notation and effective is not None:
            if not re.search(r"[（(]\s*\d+\s*(?:×|x|\+|=|marks?|अंक|ਅੰਕ)", current, re.I):
                block["text"] = current.rstrip() + f" ({int(effective)})"
