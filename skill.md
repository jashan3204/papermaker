---
description: Converts forwarded Hindi or Punjabi school examination
  question sets into correctly formatted DOCX and PDF papers using the
  school's supplied Word template and a model-paper style reference. Use
  when the user provides a question-set message and wants a
  ready-to-print examination paper.
name: school-question-paper-formatter
---

# School Question Paper Formatter

## Purpose

Turn a forwarded message containing a complete school examination
question set into a print-ready Microsoft Word (`.docx`) paper and a
matching PDF.

This workflow is intended primarily for Hindi and Punjabi examination
papers, with occasional English text and instructions. It must preserve
the supplied question content faithfully, validate the marks, place an
optional supplied image at the specified question, and follow the
school's existing template.

## Required bundled assets

Keep these two files in the skill package at the following relative
paths:

-   `assets/template_grg.docx` --- authoritative school template.
-   `assets/model sample paper.docx` --- visual formatting reference.

If the files are stored under different names or paths in the installed
skill, locate the matching bundled files before proceeding. Do not ask
the user to upload these files again when the bundled assets are
available.

### Asset authority

Use the assets for different purposes:

1.  **Template is authoritative for fixed school identity and page
    structure.** Preserve its school name, logo, examination heading
    placement, class/subject/time/max-marks layout, General Instructions
    heading, and footer. Retain the template's English labels and
    wording. Do not translate the template into Hindi or Punjabi.
2.  **Model paper is authoritative for visual styling.** Match its
    overall typography, spacing, hierarchy, question layout,
    section-heading treatment, and image presentation as closely as
    practical.
3.  Do not copy sample-paper questions, dates, class, subject, marks, or
    other exam-specific content into a new paper unless the user
    supplies those details in the current question set.
4.  Do not rebuild the template from a blank document. Use the supplied
    DOCX as the starting document and preserve its logo and fixed design
    elements.

## Interaction style and language

-   Keep the interaction minimal. Do not send progress narration,
    generic acknowledgements, explanations, or unnecessary suggestions.
-   Every conversational message to the user must be in **Hindi
    transliteration (Roman script)**. This applies to clarification
    questions, validation messages, and delivery messages.
-   The actual examination paper must preserve the language of the
    supplied questions and instructions. Do not transliterate the
    examination content.
-   Use concise, direct wording. Ask only for information needed to
    proceed.
-   Do not silently guess missing exam details, question text, question
    numbering, image placement, or marks.

## Inputs

The user will normally provide:

1.  A forwarded text message containing:
    -   Class
    -   Subject
    -   Examination title/type (for example, First Term, Mid Term,
        Pre-Board, Unit Test)
    -   Examination month/year or session, if supplied
    -   Time allowed
    -   Maximum marks
    -   Full question set, including sections, sub-questions, choices,
        and marks/marking scheme where supplied
    -   General instructions, which may be in English, Hindi, or Punjabi
2.  Optionally, one image to be inserted at a particular question
    number.

The forwarded message may contain informal spelling, inconsistent
spacing, mixed scripts, or shorthand. Interpret its structure, but do
not rewrite the academic content merely to improve its style.

## Workflow

### Phase 1 --- Read and structure the question set

Read the entire forwarded message before asking questions or creating a
document.

Extract and organize:

-   School name, if the user explicitly supplies a different one.
    Otherwise use the school identity in the bundled template.
-   Examination title and session/date.
-   Class and subject.
-   Time allowed and maximum marks.
-   General instructions.
-   Section titles and section subtitles.
-   Main question numbers and all sub-question numbers.
-   Question text, passages, poems, options, prompts, word limits, and
    internal choices such as "OR".
-   Marks attached to each question, sub-question, or section.
-   Any stated choice rule, such as "attempt any five out of six".

Preserve the original order and hierarchy. Keep every question, option,
passage, instruction, and internal choice. Do not omit content because
it looks repetitive or unimportant.

Do not invent missing text. If a portion is genuinely unreadable or
structurally ambiguous, ask a concise clarification in Hindi
transliteration before continuing.

### Phase 2 --- Ask about the optional image

After understanding the question set, ask the user for the image and its
question number using this message (or a close concise equivalent):

**"Pic wale question ke liye pic aur question number bhejiye. Agar pic
wala question nahi hai to 'NO' likh dijiye."**

Interpret the response as follows:

-   If the user uploads an image and gives a question number, associate
    that image with that exact question.
-   If the user replies `NO` (case-insensitive; allow minor surrounding
    spaces), proceed without an image.
-   If the user uploads an image but does not specify a question number,
    ask which question number it belongs to.
-   If the user gives a question number but no image is attached, ask
    them to upload the image.
-   If the response is ambiguous, ask one short clarification. Do not
    assume `NO`.
-   If multiple images are supplied, ask for the question number for
    each image, unless the mapping is already explicit.
-   Do not place an image based only on a guessed location or on the
    fact that a question mentions a picture.
-   Place the image immediately below the relevant question's prompt and
    before any answer lines/options that logically follow it, unless the
    source message clearly specifies another placement.
-   Preserve the image's aspect ratio. Resize proportionally to fit
    within the page's usable text width. Never stretch, crop, or distort
    it. Keep it legible and avoid pushing its associated question onto a
    separate page where practical.

Do not repeat this image question if the user has already clearly
supplied an image mapping or answered `NO` in the current workflow.

### Phase 3 --- Validate the marking scheme

This phase is mandatory. Do not generate final files until the marks are
reconciled.

#### 3.1 Calculate the effective marks

Calculate the marks a student is expected to earn, not merely the sum of
every printed sub-question.

Account correctly for:

-   Multipliers, for example `(6×1=6)`, `(4×2=8)`, `(5×1=5)`.
-   Choice instructions, for example "attempt any five out of six".
    Count only the required number of responses.
-   Internal alternatives marked "OR". Count the marks for the question
    once, not both alternatives.
-   Section-level totals and question-level marks.
-   Sub-question marks, including split allocations such as `(1+1=2)`.
-   Questions with several parts and a stated combined total.
-   Optional questions, internal choices, and "attempt any"
    instructions.
-   Any explicit section total.

Do not double-count the same marks at question, sub-question, and
section level. Use the most specific consistent marking information and
treat section totals as cross-checks.

#### 3.2 Identify missing or inconsistent marks

Compare:

1.  The sum of effective marks across all sections.
2.  Any section totals stated in the message.
3.  The maximum marks stated in the exam details.

Also check for: - Questions with no marks. - Contradictory marks between
a question and its section. - Multipliers that do not agree with the
number of questions or required attempts. - Choice rules that make the
printed total ambiguous. - A section total that does not equal its
effective question total.

Do not quietly modify the user's marks to force a match.

#### 3.3 If marks are missing or the total does not match

Prepare a concise diagnostic in Hindi transliteration. Identify the
exact question numbers/sections with missing or inconsistent marks,
state the calculated total, and state the expected maximum marks.

Where marks are missing, propose a reasonable marking scheme based on: -
The type and complexity of each question. - The word limit and expected
answer length. - The marks used for comparable questions elsewhere in
the same paper. - The section's stated total and the paper's maximum
marks.

Clearly label the proposed allocation as a suggestion, not as confirmed
information.

Use a message in this style:

"Question 1 aur 5 par marking scheme nahi di gayi hai. Mere hisaab se
suggested marking scheme: - Q1: ( ... ) - Q5: ( ... )

Iske alawa paper ka calculated total \_\_ marks aa raha hai, jabki
maximum marks \_\_ hain.

Aap marking scheme batayein, ya 'YES' likhein agar aapko upar di gayi
suggested marking scheme theek lagti hai."

Adapt the wording to the actual issue. If only the total is
inconsistent, show the section/question calculations that explain the
mismatch and ask which marks should be corrected.

Rules: - Wait for the user's reply before finalizing. - `YES` means the
user approves the specific proposed marking scheme shown in the
immediately preceding message. It does not authorize unrelated
changes. - If the user supplies corrected marks, recalculate the entire
paper. - If the revised total still does not match, explain the
remaining discrepancy and ask again. - Do not proceed until the
effective total matches the stated maximum marks, or the user explicitly
provides a revised maximum/marking scheme that resolves the
discrepancy. - Never fabricate marks or silently redistribute marks.

#### 3.4 Final validation record

Before document generation, internally confirm: - Every question has a
clear marks allocation, directly or through an unambiguous section
rule. - All "attempt any" and "OR" rules have been accounted for. -
Every section total is consistent, where provided. - The effective paper
total equals the confirmed maximum marks. - The marks printed in the
document agree with the validated scheme.

Do not add a separate marks-validation report to the examination paper.

### Phase 4 --- Build the examination paper

Create the DOCX by editing a copy of the bundled `template_grg.docx`,
retaining its fixed template elements.

#### 4.1 Header and fixed template content

Populate the appropriate fields using the current message:

-   Examination title/session
-   Class
-   Subject
-   Time
-   Max Marks

Keep the template's labels and fixed text in English, including: -
`Class` - `Subject` - `Time` - `Max Marks` - `General Instructions`

Do not translate these labels or the school heading into the subject
language.

Remove the `Set` field if it exists in any version of the template.
There is only one set unless the user explicitly says otherwise.

Keep the school logo and school name from the template. Keep the footer
and its placement. Do not introduce a new school identity or use the
model paper's footer as a replacement if it differs from the template.

The template's editable content area begins after
`General Instructions`. Preserve the fixed header structure and replace
only the appropriate placeholder/content area.

#### 4.2 General Instructions

Place the general instructions supplied in the forwarded message
directly below the template's `General Instructions:` heading.

-   Preserve the language of the supplied instructions. If the message
    gives them in Punjabi, keep Punjabi; if Hindi, keep Hindi; if
    English, keep English.
-   Preserve their meaning and numbering.
-   Do not translate them into another language.
-   Do not substitute the sample paper's instructions for the current
    exam's instructions.
-   If no general instructions are supplied, leave the area below the
    heading blank rather than inventing instructions.

#### 4.3 Subject-language fonts

Apply fonts consistently by script:

-   Hindi / Devanagari text: **Noto Sans Devanagari**
-   Punjabi / Gurmukhi text: **Noto Sans Gurmukhi**
-   English text and Latin-script numerals/labels: **Times New Roman**

Set the font for all relevant Word font slots, including normal text,
complex-script text, and East Asian font properties where applicable.
Set the font explicitly on runs rather than relying only on the document
theme.

If the required font is not installed in the document-generation
environment: - Do not silently substitute a visually unrelated font. -
Use the requested font name in the DOCX font settings where possible. -
Check whether the font is available for PDF rendering. If it is
unavailable, report the limitation to the user in Hindi transliteration
rather than claiming that the PDF uses the requested font. - Prefer
installing/using the correct font when the environment permits.

For mixed-language lines, apply the appropriate font to each run/script.
Do not convert Punjabi or Hindi text into an image to work around font
issues.

#### 4.4 Formatting style

Use the model paper as the visual reference. Aim for a clean, compact,
print-ready paper with a clear hierarchy.

Apply these rules:

-   **Section headings:** bold and visually prominent; centered where
    the model paper centers them.
-   **Section subtitles:** centered and bold when present, positioned
    immediately below the section heading.
-   **Main question numbers and question prompts:** bold.
-   **Marks / marking scheme:** bold, easy to locate, and placed
    consistently with the model paper.
-   **Sub-question numbers:** clearly distinguishable and consistently
    aligned.
-   **Answer options:** keep grouped under their question; preserve
    their original order. Use separators or line breaks similar to the
    model paper, without making the options difficult to read.
-   **Passages and poems:** preserve paragraph/line breaks and keep them
    visually distinct from the question prompt.
-   **Word limits, hints, points, and prompts:** retain them and format
    them consistently; do not mistake them for separate questions.
-   **Internal choices (`OR` / `या` / `ਜਾਂ`):** keep them between the
    alternatives and visually clear.
-   **Spacing:** use consistent paragraph spacing and compact line
    spacing. Avoid excessive blank lines, large gaps, or cramped text.
-   **Page breaks:** avoid splitting a question from its options or
    splitting a short question's marks from its prompt. Keep section
    headings with the first question that follows them where practical.
-   **Margins and page size:** preserve the template's page setup unless
    the model paper clearly requires a small adjustment for
    printability.
-   **Footer:** retain the template footer on all pages, with consistent
    placement.
-   Do not add decorative colors, boxes, borders, watermarks, or
    ornamental elements that are absent from the model-paper style.
-   Do not add a cover page.

Use the model paper's layout as a guide, not as a reason to reproduce
its exact page breaks. Let the new paper paginate naturally according to
its content.

#### 4.5 Question numbering and content fidelity

-   Preserve the user's question numbering exactly, including
    section-wise numbering and sub-question numbering.
-   Do not renumber questions merely to make the sequence continuous.
-   Preserve all supplied wording, spelling, punctuation, symbols,
    options, and answer-choice order as closely as possible.
-   Do not solve questions, provide answers, add answer keys, or add
    explanations.
-   Do not change a question's language.
-   Do not translate English questions into Hindi/Punjabi or vice versa.
-   Preserve "attempt any", "choose one", "answer in \_\_ words", and
    similar instructions.
-   Preserve marks notation such as `(6×1=6)` and `(1+1=2)` after
    checking it.
-   Do not duplicate a question or omit a question.
-   Do not invent missing options or fill in missing passage text.
-   If the source has an obvious typographical issue, preserve it unless
    the user explicitly asks for proofreading. If a correction is
    necessary to avoid changing the question's meaning, ask first.

#### 4.6 Insert the supplied image

-   Insert the confirmed image at the specified question number.
-   Place it directly with that question, normally after the question
    prompt and before any answer space or subsequent question.
-   Keep it centered unless the sample paper clearly uses another
    alignment.
-   Maintain aspect ratio and readable resolution.
-   Constrain its width to the available text area; do not let it
    overlap margins, footer, or text.
-   Avoid splitting the image from its question across pages. If
    necessary, move the whole question-and-image block to the next page.
-   Do not use an unrelated image from the sample paper or template as
    the question image. The school logo is a fixed template element and
    must remain in the header.

### Phase 5 --- Quality assurance

Before delivering, inspect both generated files.

#### Content checks

-   All exam details match the forwarded message.
-   All sections and questions are present and in the correct order.
-   No question or option is duplicated or omitted.
-   All question numbers and sub-question numbers are correct.
-   General instructions are present in their original language.
-   The image is present at the correct question, if one was supplied.
-   All printed marks match the confirmed scheme.
-   Effective total equals the confirmed maximum marks.

#### Layout checks

-   The school logo, heading, and fixed template elements remain intact.
-   The `Set` field is absent.
-   Template labels remain in English.
-   The document uses the requested script-specific fonts.
-   Section headings, question prompts/numbers, and marks are bold as
    specified.
-   No text is clipped, overlapping, hidden, or outside the printable
    area.
-   No blank pages or accidental extra pages exist.
-   The image is clear and not distorted.
-   Footer placement is consistent across pages.
-   Page breaks do not leave headings stranded or separate questions
    from their options/images unnecessarily.

#### PDF checks

Export the completed DOCX to PDF using a reliable DOCX-compatible
renderer available in the environment (prefer LibreOffice in headless
mode when available).

-   Do not create a PDF by renaming the DOCX or by taking screenshots of
    pages.
-   Confirm that the PDF exists and has a non-zero file size.
-   Inspect the rendered PDF pages, not just the DOCX source.
-   Check font substitution, Gurmukhi/Devanagari glyph rendering, image
    placement, page count, margins, and pagination.
-   If PDF export fails, do not provide a fake or empty PDF. Explain the
    issue and provide the valid DOCX only if it passed its own checks.

## Output

Provide two files:

1.  A completed, editable Word document (`.docx`).
2.  A matching, print-ready PDF (`.pdf`).

Use a clear filename, for example:

`Class_10_Punjabi_Pre_Board_Dec_2026.docx`
`Class_10_Punjabi_Pre_Board_Dec_2026.pdf`

Use the actual class, subject, and examination title/date in the
filename. Avoid special characters that may cause download issues.

The final delivery message must be short and in Hindi transliteration,
with direct download links to both files. Do not include a long
explanation or a validation essay. Example:

"Paper taiyar hai:

-   [Word file download karein](...)
-   [PDF download karein](...)"

If only one format was generated successfully, state that plainly and
link only to the valid file. Never claim that a file was created,
checked, or is ready unless that is true.

## Stop conditions

Stop and ask the user for clarification rather than generating the final
paper if:

-   Class, subject, examination title, time, or maximum marks are
    missing and cannot be reliably inferred from the message/template.
-   The image is required by the user's instructions but its file or
    question number is missing.
-   Question text or numbering is materially ambiguous.
-   Marks are missing or inconsistent and have not been confirmed.
-   The calculated effective total does not match the confirmed maximum
    marks.
-   The template or model-paper asset cannot be located or opened.

Ask one focused question at a time, in Hindi transliteration. Do not
overwhelm the user with a long list of unrelated questions.
