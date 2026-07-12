# SF Agents Harness

## Project Overview

Catalog of reusable skills, agents and prompts for AI coding assistants. Inspired by [github/awesome-copilot](https://github.com/github/awesome-copilot).

This content is largely AI-generated and experimental.

## Repository Structure

```
.
├── agents/           # Agent definitions (.agent.md files)
├── skills/           # Agent Skills folders (each with SKILL.md and optional bundled assets)
```

## Distribution

This repository is the **upstream source** for system skills and agent profiles
distributed to developer workstations via [sparkdock](https://github.com/sparkfabrik/sparkdock).

The sync is managed by `sparkdock-agents-sync` and triggered with:

```bash
sjust sf-agents-refresh          # sync all skills and agents
sjust sf-agents-refresh --force  # overwrite local modifications
sjust sf-agents-status           # show installed resources and update status
```

### What gets synced

| Source (this repo)               | Install target               | Description                              |
| -------------------------------- | ---------------------------- | ---------------------------------------- |
| `skills/system/<name>/`          | `~/.agents/skills/<name>/`   | Agent skills (SKILL.md + bundled assets) |
| `agents/system/<name>/copilot/`  | `~/.copilot/agents/`         | GitHub Copilot agent profiles            |
| `agents/system/<name>/opencode/` | `~/.config/opencode/agents/` | OpenCode agent profiles                  |

The sync is SHA-tracked via a manifest at `~/.cache/sparkdock/sf-skills-manifest.json`.
Local modifications are detected and preserved unless `--force` is used.

### Implications for contributors

- **Skills and agents created here reach all team members** via `sjust sf-agents-refresh`.
- Test changes locally before merging — they will be distributed automatically.
- The `skills/system/` and `agents/system/` directories are the distribution source of truth.
- Non-system skills (e.g., `skills/drupal/`) are not synced and exist only in this repo.

## File Formats

### Agent Files (\*.agent.md)

- Must have `description` field (wrapped in single quotes)
- File names should be lowercase with words separated by hyphens
- Recommended to include `tools` field
- Strongly recommended to specify `model` field

```markdown
---
name: "agent-name"
description: "Short description of what the agent does"
tools: ["tool1", "tool2"]
model: "gpt-4o"
---

# Agent Title

Instructions and context for the agent...
```

### Agent Skills (skills/\*/SKILL.md)

- Each skill is a folder containing a `SKILL.md` file
- SKILL.md must have `name` field (lowercase with hyphens, matching folder name)
- SKILL.md must have `description` field (wrapped in single quotes)
- Folder names should be lowercase with words separated by hyphens
- Skills can include bundled assets (scripts, templates, data files)

```markdown
---
name: skill-name
description: "Short description for when to use this skill"
---

# Skill Title

Content with examples, commands, code snippets...
```

## Code Style

- Use proper front matter with required fields
- Keep descriptions concise and informative
- Wrap description field values in single quotes
- Use lowercase file names with hyphens as separators
- Write in English
- Keep documentation dry and practical
- Avoid excessive emojis or AI-slop language
- Include working examples

## Adding New Resources

### For Agents

1. Create the `.agent.md` file with proper front matter
2. Add the file to the appropriate directory under `agents/`
3. Test with GitHub Copilot
4. **Update `SYSTEM.md`** — if the agent belongs to `system/`, add or remove it from the "Available agents" list
5. **Update `config/catalog.json`** — add or update the short description in the `agents` section

System agents (`agents/system/`) support multiple tools (Copilot, OpenCode). Each tool gets its own file in a subfolder, but the prompt body must be kept identical across tools — only the YAML frontmatter differs to match each tool's configuration format. There is no shared standard yet.

### For Skills

1. Create a new folder under `skills/<technology>/`
2. Add a `SKILL.md` file with proper front matter
3. Add any bundled assets (scripts, templates, data) to the skill folder
4. Test with GitHub Copilot
5. **Update `SYSTEM.md`** — if the skill belongs to `system/`, add or remove it from the "Available skills" list
6. **Update `config/catalog.json`** — add or update the short description in the `skills` section
7. **Update `README.md`** — add or remove the skill from the skills table

## Git Workflow

- **Never push directly to `main`.** Always create a feature branch and open a pull request.
- **Verify your branch before every commit.** Run `git branch --show-current` and confirm you are on the correct feature branch — not `main`, not a stale branch from a previous task. This is especially important after branch switches (e.g., smoke tests, rebases, stash pop). Never assume you are on the right branch.
- Branch naming: `feat/`, `fix/`, `chore/`, `test/` prefixes with kebab-case description (e.g., `feat/glab-file-uploads`, `fix/skill-jq-flag`).
- Commit messages: conventional commits (`feat:`, `fix:`, `chore:`, `test:`, `docs:`).
- Always update `CHANGELOG.md` when making user-facing changes (see Changelog section below).

## Upstream Skill Sync

Some system skills are synced from external GitHub or GitLab repositories. The
sync mechanism uses a JSON manifest (`config/upstream-skills.json`) and a generic
sync script (`scripts/sync-skill.sh`).

### How it works

1. `upstream-skills.json` declares each upstream skill: the source repo, branch,
   path inside the repo, and optional frontmatter overrides.
2. `sync-skill.sh` downloads repo tarballs (one per unique repo), extracts each
   skill directory, patches the SKILL.md frontmatter if overrides are declared,
   appends `custom-sections.md` if present, and writes the result to
   `skills/system/<name>/`.
3. Local-only files (`custom-sections.md`, `evals/`) are preserved across syncs.
4. A weekly GitHub Actions workflow (`.github/workflows/sync-skills.yml`) runs
   `./scripts/sync-skill.sh --all` and opens a PR if anything changed.

### Usage

```bash
./scripts/sync-skill.sh <name>           # sync a single skill
./scripts/sync-skill.sh <name> --check   # dry-run: exit 1 if stale
./scripts/sync-skill.sh --all            # sync all skills from manifest
./scripts/sync-skill.sh --all --check    # dry-run for all skills
```

Requires `jq` and `curl`.

### Adding a new upstream skill

1. Add an entry to `config/upstream-skills.json` (see schema below).
2. Run `./scripts/sync-skill.sh <name>` to pull the skill.
3. Optionally create `skills/system/<name>/custom-sections.md` with local additions.
4. Update `SYSTEM.md`, `README.md`, `config/catalog.json`, and `CHANGELOG.md`.

### Manifest schema (`upstream-skills.json`)

The manifest format is defined by `config/upstream-skills.schema.json`. Each entry
in the `skills` array has the following fields:

| Field                   | Type   | Required | Description                                                                                                                           |
| ----------------------- | ------ | -------- | ------------------------------------------------------------------------------------------------------------------------------------- |
| `name`                  | string | yes      | Skill name (`lowercase-with-hyphens`). Must match the target folder under `skills/system/`.                                           |
| `host`                  | string | no       | Upstream host: `github.com` (default) or a GitLab host such as `gitlab.com`. Selects the tarball URL scheme.                          |
| `repo`                  | string | yes      | Repository path. `owner/repo` for GitHub; may include nested groups for GitLab (for example `gitlab-org/cli`).                        |
| `ref`                   | string | no       | Branch or tag to sync from. Defaults to `main`.                                                                                       |
| `path`                  | string | yes      | Path to the skill directory inside the repo.                                                                                          |
| `frontmatter_overrides` | object | no       | YAML frontmatter fields to patch in the upstream SKILL.md. Only listed fields are replaced; all other upstream fields are kept as-is. |

Example entry:

```json
{
  "name": "playwright-cli",
  "repo": "microsoft/playwright-cli",
  "ref": "main",
  "path": "skills/playwright-cli",
  "frontmatter_overrides": {
    "description": "Custom description optimized for auto-triggering keywords."
  }
}
```

When `frontmatter_overrides` is omitted, the upstream SKILL.md frontmatter is
used as-is.

## Changelog

This project maintains a `CHANGELOG.md` using the [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) format.
There is no semantic versioning — the latest commit is always the current version. This is a rolling project: every merge to `main` is immediately released, so there is no unreleased state. Changes are grouped by date, not by version. Do not use an `[Unreleased]` section; the top of the file is always a dated section.

**Every time you make changes to this repository, you must update `CHANGELOG.md`:**

- Add your entry under a dated section (`[YYYY-MM-DD]`, ISO 8601) matching today's date. Create the section at the top of the list if none exists for today; otherwise append to the existing one. Dated sections are ordered newest first.
- Use the standard Keep a Changelog categories: `Added`, `Changed`, `Deprecated`, `Removed`, `Fixed`, `Security`. Within a date, order the categories as listed here.
- Write entries from the perspective of a consumer of the skill/agent (what changed, not how).
- Keep it concise: 1-2 entries per skill/agent per date section. Consolidate related changes into a single entry rather than listing each sub-feature separately.

## References

- [AGENTS.md specification](https://agents.md/)
- [Agent Skills specification](https://agentskills.io/specification)
- [VS Code custom instructions](https://code.visualstudio.com/docs/copilot/customization/custom-instructions)
- [GitHub Awesome Copilot](https://github.com/github/awesome-copilot)
