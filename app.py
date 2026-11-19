from __future__ import annotations

import json
import re
from pathlib import Path

import streamlit as st
import pandas as pd
from PIL import Image
import io

from paper_engine import parse_with_gemini, calculate_total, build_docx, convert_docx_to_pdf, update_block_marks

st.set_page_config(page_title="PaperMaker", page_icon="📝", layout="wide")

st.markdown("""
<style>
.block-container {max-width: 1050px; padding-top: 2rem; padding-bottom: 3rem;}
[data-testid="stMetric"] {background: #f7f8fa; padding: 12px; border-radius: 12px;}
.small-note {color: #6b7280; font-size: .88rem;}
</style>
""", unsafe_allow_html=True)

st.title("📝 PaperMaker")
st.caption("Hindi aur Punjabi school examination papers — Word aur PDF mein")
st.info("Aapka question-set text aur image is app mein permanently save nahi hote. Gemini API key sirf current session mein use hoti hai. Confidential student information share na karein.")

with st.sidebar:
    st.subheader("Gemini API key")
    api_key = st.text_input("Apni Gemini API key daalein", type="password", key="gemini_api_key", help="Google AI Studio se API key banayein: aistudio.google.com/app/apikey")
    model = st.selectbox("AI model", ["gemini-2.5-flash", "gemini-2.0-flash"], index=0)
    st.caption("API key is session-only; app ise file ya database mein save nahi karti.")
    st.markdown("[Gemini API key banayein](https://aistudio.google.com/app/apikey)")

if "parsed" not in st.session_state:
    st.session_state.parsed = None
if "docx_bytes" not in st.session_state:
    st.session_state.docx_bytes = None
if "pdf_bytes" not in st.session_state:
    st.session_state.pdf_bytes = None

st.subheader("1. Question set paste karein")
message = st.text_area(
    "WhatsApp se aaya poora message yahan paste karein",
    height=260,
    placeholder="Class, subject, exam title, time, maximum marks, general instructions aur poora question set paste karein...",
    key="source_message",
)

col1, col2 = st.columns([1, 2])
with col1:
    parse_clicked = st.button("Question set parse karein", type="primary", use_container_width=True)
with col2:
    st.markdown('<p class="small-note">Poora message ek saath paste karein. Agar text bahut lamba hai, tab bhi use poora paste karein.</p>', unsafe_allow_html=True)

if parse_clicked:
    if not api_key:
        st.error("Pehle sidebar mein apni Gemini API key daalein.")
    elif not message.strip():
        st.error("Question set ka message paste karein.")
    else:
        with st.spinner("Question set samjha ja raha hai..."):
            try:
                st.session_state.parsed = parse_with_gemini(api_key, message, model)
                st.session_state.docx_bytes = None
                st.session_state.pdf_bytes = None
                st.success("Question set parse ho gaya. Ab details aur marks check karein.")
            except Exception as exc:
                st.error(f"Parse nahi ho saka: {exc}")

if st.session_state.parsed:
    data = st.session_state.parsed
    meta = data.setdefault("metadata", {})
    st.divider()
    st.subheader("2. Exam details verify karein")
    c1, c2, c3 = st.columns(3)
    meta["class"] = c1.text_input("Class", str(meta.get("class") or ""))
    meta["subject"] = c2.text_input("Subject", str(meta.get("subject") or ""))
    meta["exam_title"] = c3.text_input("Exam title", str(meta.get("exam_title") or ""))
    c4, c5, c6 = st.columns(3)
    meta["session"] = c4.text_input("Session / month / year", str(meta.get("session") or ""))
    meta["time"] = c5.text_input("Time", str(meta.get("time") or ""))
    max_default = meta.get("max_marks")
    max_marks_input = c6.text_input("Maximum marks", str(max_default) if max_default not in (None, "") else "")
    try:
        meta["max_marks"] = int(max_marks_input.strip()) if max_marks_input.strip() else None
        if meta["max_marks"] is not None and meta["max_marks"] < 1:
            raise ValueError
    except ValueError:
        meta["max_marks"] = None
        st.error("Maximum marks mein valid positive number daalein.")

    st.subheader("3. General instructions")
    instr_text = "\n".join(str(x) for x in data.get("general_instructions", []))
    instr_text = st.text_area("Original language mein instructions verify/correct karein", value=instr_text, height=100)
    data["general_instructions"] = [x for x in instr_text.splitlines() if x.strip()]

    if data.get("warnings"):
        st.warning("AI ne ye ambiguities note ki hain:\n" + "\n".join(f"• {w}" for w in data["warnings"]))

    st.subheader("4. Questions aur marking scheme")
    st.caption("AI extraction ko zaroor check karein. Effective marks ka matlab hai choices apply karne ke baad student ke maximum marks.")
    questions = data.get("questions", [])
    total, missing = 0, []
    target = int(meta.get("max_marks") or 0)
    section_mismatches = []
    if questions:
        rows = []
        for q in questions:
            rows.append({
                "Question": str(q.get("id") or q.get("label") or ""),
                "Section": str(q.get("section") or ""),
                "Marks notation": str(q.get("marks_notation") or ""),
                "Effective marks": q.get("effective_marks"),
                "AI suggestion": q.get("suggested_marks"),
                "Reason / note": str(q.get("reason") or ""),
            })
        edited = st.data_editor(pd.DataFrame(rows), use_container_width=True, hide_index=True,
                                disabled=["Question", "Section", "Marks notation", "AI suggestion", "Reason / note"],
                                column_config={"Effective marks": st.column_config.NumberColumn("Effective marks", min_value=0, max_value=500, step=1, required=False)})
        for i, q in enumerate(questions):
            val = edited.iloc[i]["Effective marks"]
            q["effective_marks"] = None if pd.isna(val) else int(val)

        if any(q.get("effective_marks") is None and q.get("suggested_marks") is not None for q in questions):
            if st.button("YES — AI suggested marks approve karein"):
                for q in questions:
                    if q.get("effective_marks") is None and q.get("suggested_marks") is not None:
                        q["effective_marks"] = int(q["suggested_marks"])
                st.rerun()

        total, missing = calculate_total(questions)
        target = int(meta.get("max_marks") or 0)
        stated_by_section = {str(x.get("section")): x.get("stated_total") for x in data.get("section_totals", []) if x.get("stated_total") is not None}
        calculated_by_section = {}
        for q in questions:
            sec = str(q.get("section") or "").strip()
            if sec and q.get("effective_marks") is not None:
                calculated_by_section[sec] = calculated_by_section.get(sec, 0) + int(q["effective_marks"])
        for sec, stated in stated_by_section.items():
            if sec in calculated_by_section and int(stated) != calculated_by_section[sec]:
                section_mismatches.append(f"{sec}: calculated {calculated_by_section[sec]}, stated {stated}")
        a, b, c = st.columns(3)
        a.metric("Calculated total", total)
        b.metric("Maximum marks", target)
        c.metric("Difference", total - target)
        if missing:
            st.error("In questions par marks missing hain: " + ", ".join(missing))
        elif section_mismatches:
            st.error("Section totals match nahi kar rahe: " + "; ".join(section_mismatches))
        elif total != target:
            st.error(f"Marks match nahi kar rahe. Calculated total {total}, jabki maximum marks {target} hain. Table mein effective marks correct karein.")
        else:
            st.success("Effective marks ka total maximum marks se match karta hai.")

        section_totals = data.get("section_totals", [])
        if section_totals:
            with st.expander("AI se nikale gaye section totals dekhein"):
                st.json(section_totals)
    else:
        st.error("Koi main question identify nahi hua. Source message dobara check karein.")

    st.subheader("5. Question content verify karein")
    st.caption("Document mein isi ordered content ka use hoga. Agar AI ne text galat padha hai, yahan JSON edit karke save karein.")
    with st.expander("Parsed document blocks (advanced editing)"):
        blocks_json = st.text_area("Blocks JSON", value=json.dumps(data.get("blocks", []), ensure_ascii=False, indent=2), height=320)
        if st.button("Edited blocks apply karein"):
            try:
                new_blocks = json.loads(blocks_json)
                if not isinstance(new_blocks, list):
                    raise ValueError("Blocks JSON ek list hona chahiye.")
                data["blocks"] = new_blocks
                st.success("Blocks update ho gaye.")
                st.rerun()
            except Exception as exc:
                st.error(f"JSON valid nahi hai: {exc}")

    st.subheader("6. Optional question image")
    image_files = st.file_uploader("Ek ya adhik question images upload karein (optional)", type=["png", "jpg", "jpeg", "webp"], accept_multiple_files=True)
    question_ids = [str(q.get("id")) for q in questions if q.get("id")]
    image_mapping = {}
    image_mapping_valid = True
    if image_files:
        st.caption("Har image ke liye uska question number select karein.")
        for idx, img in enumerate(image_files):
            left, right = st.columns([2, 1])
            left.write(f"**{idx + 1}. {img.name}**")
            selected_q = right.selectbox("Question", question_ids, key=f"image_question_{idx}")
            if selected_q in image_mapping:
                st.error(f"{selected_q} ke liye ek se adhik image select hui hain. Har image ko alag question dein.")
                image_mapping_valid = False
            try:
                if img.size > 12 * 1024 * 1024:
                    st.error(f"{img.name} 12 MB se badi hai. Chhoti image upload karein.")
                    image_mapping_valid = False
                else:
                    pil_image = Image.open(img).convert("RGB")
                    buffer = io.BytesIO()
                    pil_image.save(buffer, format="PNG", optimize=True)
                    image_mapping[selected_q] = buffer.getvalue()
            except Exception as image_exc:
                st.error(f"{img.name} image read nahi ho saki: {image_exc}")
                image_mapping_valid = False
    else:
        st.caption("Agar picture wala question nahi hai, image upload na karein.")

    can_generate = bool(meta.get("class") and meta.get("subject") and meta.get("exam_title") and meta.get("time") and meta.get("max_marks") and questions and not missing and not section_mismatches and total == target)
    st.divider()
    if not can_generate or not image_mapping_valid:
        st.button("Word aur PDF generate karein", disabled=True, use_container_width=True)
        st.caption("Generate karne se pehle required details, image mapping aur marks mismatch resolve karein.")
    else:
        if st.button("Word aur PDF generate karein", type="primary", use_container_width=True):
            with st.spinner("Word document banaya ja raha hai..."):
                try:
                    update_block_marks(data)
                    docx_bytes = build_docx(data, image_mapping)
                    st.session_state.docx_bytes = docx_bytes
                    st.session_state.pdf_bytes = None
                    try:
                        st.session_state.pdf_bytes = convert_docx_to_pdf(docx_bytes)
                    except Exception as pdf_exc:
                        st.warning(f"Word file ban gayi, lekin PDF export nahi ho saka: {pdf_exc}")
                    st.success("Document generation complete. Download kar sakte hain.")
                except Exception as exc:
                    st.error(f"Document generate nahi ho saka: {exc}")

    if st.session_state.docx_bytes:
        safe = re.sub(r"[^A-Za-z0-9_-]+", "_", f"Class_{meta.get('class')}_{meta.get('subject')}_{meta.get('exam_title')}").strip("_")[:90]
        st.subheader("7. Download files")
        d1, d2 = st.columns(2)
        d1.download_button("⬇ Word file (.docx)", st.session_state.docx_bytes, file_name=f"{safe}.docx", mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document", use_container_width=True)
        if st.session_state.pdf_bytes:
            d2.download_button("⬇ PDF file (.pdf)", st.session_state.pdf_bytes, file_name=f"{safe}.pdf", mime="application/pdf", use_container_width=True)
        else:
            d2.info("PDF available nahi hai. DOCX download karein; hosting par LibreOffice support check karein.")

st.divider()
st.caption("PaperMaker · Final printing se pehle Word/PDF ko proofread zaroor karein.")
