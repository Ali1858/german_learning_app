---
name: german-reader-project-structure
description: Where things live in the german_learning project — generator script, output HTML, dev tooling, annotation syntax
metadata:
  type: reference
---

- `generate_reader_framework.py` is the SOURCE — a Python script containing the STORIES data (20 stories, 500 target A2 nouns + B1 bridge words) plus the HTML/CSS/JS renderer. Run `python generate_reader_framework.py <output.html>` to build. See `workflow_edit_framework_not_html.md` — never edit the built HTML directly.
- Output file: `german_a2_annotated_stories.html` (renamed from earlier `german_a2_b1_case_gender_reader_v8.html` / `german_a2_stories.html` per user request — confirm current name before referencing it, filenames have changed multiple times).
- `scan_annotation_gaps.py` — a dev/audit script that masks out already-annotated spans and checks whether target nouns still appear as plain unannotated text; useful for future content-completeness audits.
- Annotation markup syntax (documented in the framework's own module docstring):
  - `{{case|gender|left|noun}}` — full case phrase, `left` is article+adjective text with `[ending]` bracket cues that render bold and case-colored.
  - `<<gender|noun>>` — gender-only tag (no case shown), used mainly for bare nouns with no visible article/case marking.
  - `[[case|trigger]]` — case-triggering preposition or verb (e.g. `[[dat|mit]]`, `[[akk|sucht]]`).
  - `((word|gloss))` — B1 bridge vocabulary with an English gloss tooltip.
  - Annotation scope was expanded (by explicit user request) from "just the 500 curated target nouns" to "every noun phrase with a determinable case" course-wide — see `repetition_design_philosophy.md` for the related content-repetition rule.
  - Genitive constructions and fixed idioms (`zu Fuß`, `eines Abends`, `in Ordnung`) are deliberately left unannotated since the system only teaches nom/akk/dat.
- CSS toggle classes on `<body>`: `no-gender`, `no-case`, `no-trigger`, `no-ending`, `no-b1`, `no-new` strip the corresponding visual hint. Each toggle must reset BOTH color and font-weight where the base rule sets both — a past bug (`.gender`/`.trigger` staying bold in Plain reading mode) came from an override resetting only color.
