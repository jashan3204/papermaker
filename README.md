# PaperMaker

A link-shareable Streamlit application for preparing Hindi and Punjabi school examination papers from a forwarded question-set message. It uses Gemini for extraction and suggested marking allocations, then performs deterministic total checks and creates an editable DOCX plus a PDF.

## What's included

- `app.py` — Streamlit interface and workflow.
- `paper_engine.py` — Gemini parsing, mark validation, and Word/PDF generation.
- `skill.md` — the full authoritative workflow specification supplied for this project.
- `assets/template_grg.docx` — the original school template.
- `assets/model sample paper.docx` — the sample formatting reference.

The template controls fixed school identity, header/footer, and page structure. The model paper is a visual reference only. Its exam-specific questions and details are never copied into a new paper.

## Run locally

Python 3.11 or 3.12 is recommended. LibreOffice is required for PDF export.

```bash
python -m venv .venv
# macOS/Linux
source .venv/bin/activate
# Windows PowerShell: .venv\\Scripts\\Activate.ps1
pip install -r requirements.txt
streamlit run app.py
```

Open the local URL shown by Streamlit. Paste a Gemini API key in the app's password field. The key is held only in the current Streamlit session and is not written to disk or included in generated files.

Get an API key from Google AI Studio: https://aistudio.google.com/app/apikey

## Deploy a public link with Streamlit Community Cloud

1. Create a GitHub account if needed: https://github.com
2. Create a **public** GitHub repository named `papermaker` (public repos are simplest for the free Streamlit Community Cloud workflow).
3. Upload the complete contents of this folder to the repository root. Keep the `assets/` directory and both DOCX files.
4. Open https://share.streamlit.io and sign in with GitHub.
5. Choose **Create app**, select the repository, branch `main`, and main file path `app.py`.
6. Choose a memorable app subdomain if available, then deploy.
7. Share the resulting `https://....streamlit.app` URL with your aunt.
8. Your aunt opens the URL and enters her own Gemini API key into the password field. She does not need a ChatGPT account or a GitHub account.

Official deployment guide: https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy

### Important public-link warning

A public Streamlit app URL is accessible to anyone who has the link (and potentially discoverable depending on platform settings). The Gemini API key is entered by each user into a password field and is not saved by this app. Anyone with the link can use the app with their own key. This is not access control. Do not paste confidential student data or personal information into a public app.

The app does not persist uploaded question text or images in a database. Generated files are held in Streamlit's temporary app session and are offered as downloads. Temporary server memory/storage is not a guaranteed long-term private vault; avoid confidential material and close the session after use.

## How to use

1. Paste the complete forwarded message, including class, subject, exam title, time, maximum marks, questions, and general instructions.
2. Click **Parse question set**.
3. Review the extracted details and questions. Correct any extraction mistakes before continuing.
4. Upload the optional question image and select the question number where it belongs. If there is no image, choose **No image**.
5. Review effective marks. The app accounts for attempt counts and alternatives as parsed by Gemini. If marks are missing, Gemini may propose values; you must explicitly approve them. You can edit the values directly.
6. Generate only when the sum of effective marks equals the maximum marks.
7. Download the DOCX and PDF.

## Mark validation model

Gemini interprets the question structure and proposes per-question effective marks, including choice rules such as “attempt any 5 out of 6” and `OR` alternatives. The app then sums the effective marks with Python. It does not silently redistribute marks to force a match. Review the extracted text and marks table: AI extraction can make mistakes, especially with dense forwarded messages, unusual choice rules, or mixed-language notation.

## Fonts and PDF export

The DOCX sets script-specific font names:

- Devanagari: Noto Sans Devanagari
- Gurmukhi: Noto Sans Gurmukhi
- English/Latin: Times New Roman

PDF export uses LibreOffice if installed. A deployment host may not have the requested Noto fonts or LibreOffice available. If PDF conversion fails, the app will still offer the DOCX and explain the failure. The DOCX font names are set, but the viewer's installed fonts determine final rendering if those fonts are absent.

For best results on Streamlit Community Cloud, test the first generated Hindi and Punjabi PDFs carefully. Community Cloud's runtime environment and installed system fonts can change; the app intentionally reports PDF export failures instead of creating a fake PDF.

## Limitations

- The current version supports one optional image per paper. If multiple images are needed, extend the image mapping UI and generator.
- The original template has a fixed one-school identity. This version retains it; it is not a multi-school template manager.
- This is a family/school utility, not a high-assurance exam publishing system. Always proofread the final paper before printing.
- Free Gemini quotas and free hosting availability/limits are controlled by their providers and may change.
