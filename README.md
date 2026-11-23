# Runtime contract

Bohrium Playground Period 4 submission — challenge `challenge-96263d10` (track: `academic-writing`).

This repository holds the complete skill package for the challenge: the skill
definition, its executable entry point and all supporting scripts. No precomputed
answers, private data or credentials are included.

## Skill

- Name: `academic-template-conformance`
- Summary: Extract itemised formatting requirements from a journal or thesis template, audit and text-level fix a manuscript (heading hierarchy, numbering, captions, reference entries) for conformance, inventory content units, and report per-item evidence with locators in /app/output/result.json. Use when a task asks whether and how a paper should be adapted to a submission template.

## Contents

| File |
|------|
| `SKILL.md` |
| `scripts/run_skill.py` |
| `README.md` |

## How to run

```bash
python scripts/run_skill.py --case /input/case.json --output /app/output/result.json
```

The entry point is `SKILL.md`; input/output contracts, error handling and a minimal
usage example are documented there.

## Notes

- Pure Python standard library; no network access required.
- The result JSON keeps the input case id, the main results, per-item evidence,
  a run status and an uncertainty section.
