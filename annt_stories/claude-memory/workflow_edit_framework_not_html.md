---
name: workflow-edit-framework-not-html
description: Never hand-edit german_a2_annotated_stories.html directly — always edit generate_reader_framework.py and regenerate
metadata:
  type: feedback
---

Never hand-edit the generated HTML reader file directly. Always edit `generate_reader_framework.py` (the Python source-of-truth) and regenerate via `python generate_reader_framework.py german_a2_annotated_stories.html`.

**Why:** The user explicitly corrected this early in the project ("dont make edit in html directly, edit the framework file, so that we can scale it later with new contents"). A prior corruption of the shipped HTML's CSS (the `.ending` case-color rules) was traced to exactly this anti-pattern — someone had hand-edited the HTML output instead of the generator, silently breaking selector syntax.

**How to apply:** Any UI/CSS/JS change or content fix goes into the Python STORIES data or the CSS/JS string constants in generate_reader_framework.py. After editing, always regenerate and spot-check (grep for stray unmatched `{{`/`}}`/`[[`/`]]` in the output) before considering the change done.
