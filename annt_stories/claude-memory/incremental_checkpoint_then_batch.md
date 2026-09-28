---
name: incremental-checkpoint-then-batch
description: For large mechanical rewrites, do one representative unit first and confirm before replicating across the rest — then stop checkpointing and batch through
metadata:
  type: feedback
---

When a task requires the same kind of large, repetitive edit across many units (e.g. re-annotating all 20 stories in the German reader), do ONE unit first as a thorough, careful example, describe the concrete result, and get explicit confirmation before replicating it everywhere.

**Why:** For the "annotate every case-bearing noun, not just the 500 target list" task, doing Story 1 first and describing the density increase let the user confirm the approach before committing to the same treatment across all 20 stories — a much bigger effort that could have gone the wrong direction if unconfirmed.

**How to apply:** Once the user confirms the approach (e.g. "yes go on"), stop checkpointing after every unit — the user explicitly said "fix all not one by one" when I kept doing individual regenerate-and-verify cycles after each story. After confirmation, batch through the remaining units efficiently, doing periodic sanity regenerations (not after every single edit) rather than a full report after each one. Save the detailed summary for the end. See `repetition_design_philosophy.md` for the content-scope lesson learned the same session.
