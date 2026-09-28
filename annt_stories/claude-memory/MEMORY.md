# Claude memory for this project

This folder is a plain-text export of the persistent memory Claude built up while working on this project, so it travels with the repo instead of living only in Claude's local memory store. Each file below is a standalone note; `[[links]]` refer to other files in this folder by their `name:` slug.

- [Edit the framework, not the HTML](workflow_edit_framework_not_html.md) — never hand-edit german_a2_annotated_stories.html; edit generate_reader_framework.py and regenerate
- [Checkpoint once, then batch](incremental_checkpoint_then_batch.md) — confirm approach on one unit, then stop checkpointing and push through the rest
- [Repetition spans stories, not within one](repetition_design_philosophy.md) — vocab reuse belongs in later stories, not crammed into the home story
- [Project structure & annotation syntax](german_reader_project_structure.md) — where the generator, output, and dev tools live; markup syntax reference
