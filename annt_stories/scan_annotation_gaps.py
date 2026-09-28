#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Scan STORIES for target nouns that appear as PLAIN, unannotated text
(i.e. not wrapped in {{..}}, <<..>>, [[..]], or ((..)) markup).

This flags candidate gaps where the prose mentions a noun (this story's own
new target, or an already-introduced one due for repetition) but the author
forgot to wrap it in the case/gender annotation syntax, so the reader sees
it with no color/underline/ending cue at all.

Output is a human-reviewable candidate list, not an automatic "fix" --
some hits will be false positives (different word sharing a stem, a proper
name, part of a compound the regex boundary didn't catch, etc.) and need
eyeballing in context.
"""

import re
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

import generate_reader_framework as g

MARKUP_SPANS = re.compile(
    r"\{\{[^{}]*\}\}"      # {{..}}
    r"|<<[^<>]*>>"          # <<..>>
    r"|\[\[[^\[\]]*\]\]"    # [[..]]
    r"|\(\([^()]*\)\)"      # ((..))
)


def mask_annotated(text: str) -> str:
    """Blank out every annotated span, keeping string length/offsets stable."""
    return MARKUP_SPANS.sub(lambda m: " " * len(m.group(0)), text)


def inflections(base: str):
    """Best-effort surface forms for a German noun base (singular, no article)."""
    forms = {base}
    low_last = base[-1]
    # plural/case suffixes
    for suf in ("e", "en", "n", "er", "ern", "es", "s", "nen"):
        forms.add(base + suf)
    # weak/n-declension already covered by +n/+en above
    # -in feminine plural: Kollegin -> Kolleginnen (base already ends 'in')
    if base.endswith("in"):
        forms.add(base + "nen")
    return forms


def build_target_registry():
    """noun base (casefold) -> (home_story, gender, surface_forms)"""
    reg = {}
    for s in g.STORIES:
        for gender, noun, english in s["targets"]:
            key = noun.strip()
            reg[key.casefold()] = {
                "base": key,
                "home": s["number"],
                "gender": gender,
                "forms": inflections(key),
            }
    return reg


def main():
    reg = build_target_registry()
    # cumulative-introduced tracking: a noun is "in play" from its home story onward
    findings = []
    for s in g.STORIES:
        story_no = s["number"]
        for p_idx, para in enumerate(s["paragraphs"], 1):
            plain = mask_annotated(para)
            for key, info in reg.items():
                if info["home"] > story_no:
                    continue  # not introduced yet, not expected to appear
                for form in info["forms"]:
                    pattern = r"\b" + re.escape(form) + r"\b"
                    for m in re.finditer(pattern, plain):
                        start = max(0, m.start() - 30)
                        end = min(len(plain), m.end() + 30)
                        context = para[start:end].replace("\n", " / ")
                        findings.append(
                            (story_no, p_idx, info["base"], info["home"], form, context)
                        )

    findings.sort(key=lambda x: (x[0], x[1]))
    print(f"Total candidate un-annotated target-noun occurrences: {len(findings)}\n")
    for story_no, p_idx, base, home, form, context in findings:
        tag = "NEW" if home == story_no else f"repeat(from S{home})"
        print(f"S{story_no} p{p_idx} [{tag}] base={base!r} matched={form!r}")
        print(f"    ...{context}...")


if __name__ == "__main__":
    main()
