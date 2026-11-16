# Upstream

This skill is vendored from
[anthropics/skills](https://github.com/anthropics/skills/tree/main/skills/skill-creator)
(Apache License 2.0, see `LICENSE.txt`). It no longer syncs automatically.

The upstream commit it is based on is recorded as `base_sha` in
`config/vendored-skills.json` in the
[sf-agents-harness](https://github.com/sparkfabrik/sf-agents-harness) repository.
A weekly workflow opens an issue when upstream changes. Backport what is useful
by hand, then update `base_sha`.

## Local changes

- `SKILL.md`: adds the "Cost limits" section (lite mode by default, opt-in full
  eval mode, at most 3 concurrent subagents on `sonnet`, no Workflow tool), runs
  eval subagents in small batches, researches inline, and documents the lower
  description optimizer defaults. Includes the "Non-Claude coding agents" section.
- `scripts/run_eval.py`, `scripts/run_loop.py`: default to 2 workers, 1 run per
  query, 2 iterations, and the `sonnet` model.
- `scripts/improve_description.py`: defaults to the `sonnet` model.
