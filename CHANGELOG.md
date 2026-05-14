# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
This project has no semantic versioning — the latest commit is the current version.
Changes are grouped by date.

## [Unreleased]

## [2026-05-14]

### Added

- `the-analyst`, `the-builder`, and `the-reviewer` system agents: add domain analysis, test-driven implementation, and read-only review profiles for both Copilot and OpenCode, plus a manual eval matrix for distribution checks
### Added

- `sf-commit-convention` skill (`skills/system/`): enforce SparkFabrik commit message and branch naming conventions -- adaptive format detection from git log history (conventional, legacy, Jira-style, custom) with most-recent-commit-wins for mixed logs and user prompt for unrecognizable histories, commit-msg hook error parsing for automatic format recovery, mandatory issue references in commit footers only (`Refs:`/`Closes:` trailers with fully qualified project path, never bare `#N` or in the subject line), branch naming (`feat/<issue>-<desc>`, `fix/<issue>-<desc>`, etc.), lowercase `Assisted-by` AI trailer on every commit, and non-interactive git operation guidance (avoid `-i`/`--interactive` flags, editors, and TTY-dependent commands)
- `skill-creator` custom section: document `opencode run` as an alternative to `claude -p` for running skill evals, including OpenCode JSON event schema and skill-trigger detection pattern; enforce `github-copilot/gpt-4.1` as default model for evals to avoid premium model costs
- `gh` and `glab` skills: warn about accidental issue auto-linking -- wrap `#N` in backticks when used as examples rather than intentional references
- `drupal-major-upgrade-validation` skill (`skills/drupal/`): validate Drupal major version upgrades (e.g., D10 to D11) by capturing a browser-automation baseline on the stable branch, applying the upgrade, re-running the same tests, and producing a structured comparison report with per-page status, console error diffs, and screenshot references

### Changed

- README: Removed VS Code Insiders requirement for `chat.useAgentSkills` directive -- Agent Skills are now available in the standard VS Code release
- `glab` skill: require fully-qualified references (`group/project#N`, `group/project!N`) in all written content (descriptions, comments, notes) to prevent broken cross-project links

### Fixed

- `glab` skill: document `-f` vs `-F` flag difference for `glab api` — `-f key=@file` sends the literal string while `-F key=@file` reads the file content; using the wrong flag silently corrupts note/description updates

## [2026-04-13]

### Added

- `glab` skill: group-level API patterns (list projects in a group, subgroups, descendant projects) in both SKILL.md and `references/api-patterns.md`

### Fixed

- `glab` skill: document `--paginate` concatenation pitfall -- paginated responses produce invalid JSON (`[...][...]`) that breaks `jq`; added `jq -s 'add'` workaround with examples

## [2026-04-11]

### Added

- `config/catalog.json`: machine-readable short descriptions for all system skills and agents, consumed by `sparkdock-agents-status` for a DESCRIPTION column in the terminal table -- includes JSON Schema (`config/catalog.schema.json`) for editor support and validation
- `sf-create-agentsmd` skill: discovery-driven AGENTS.md generator and reviewer for non-pkg projects -- inspects project structure, languages, package managers, task runners, Docker setup, and CI config, then generates or audits an AGENTS.md with supply chain safety (live registry checks, 5-day release quarantine), tiered command safety policy, git workflow conventions, and OpenSpec change management
- `AGENTS.md`: distribution section documenting the sparkdock sync pipeline (`skills/system/` and `agents/system/` to developer workstations via `sjust sf-agents-refresh`)

### Removed

- `create-agentsmd` skill: removed generic upstream skill (from `github/awesome-copilot`) -- superseded by `sf-create-agentsmd` which includes discovery-driven generation, supply chain safety, command safety policy, and monorepo considerations

## [2026-04-09]

### Added

- `auto-format-doc` skill: auto-format files after creating or modifying them using external formatters managed by Just recipes (`sjust` on macOS, `ajust` on Linux) -- supports Markdown via Prettier with try-Just-then-npx fallback chain (`format-md` recipe preferred, `npx prettier@3` when it fails), format-check support, and warn-and-continue error handling
- `auto-format-doc` skill: 6 eval scenarios (create, edit, multi-file, implicit trigger, fallback-on-recipe-failure, check-without-writing)

## [2026-04-08]

### Fixed

- `glab` skill: document correct state filtering for `glab issue list` and `glab mr list` -- `glab` uses `--closed`/`--all` flags, not `--state` (which is a `gh` flag and fails with "Unknown flag")

### Added

- `glab` skill: three new eval cases for issue/MR state filtering (open issues, closed issues, all MRs) testing that agents use `--closed`/`--all` instead of the invalid `--state` flag

## [2026-04-02]

### Added

- `githuman` skill: review AI-generated code before committing via GitHuman Docker instances managed by Just recipes (`sjust` on macOS, `ajust` on Linux). Synced from [mcollina/githuman-skills](https://github.com/mcollina/githuman-skills) with frontmatter description override and custom sections that override upstream `npx githuman` examples with sjust/ajust command mapping, infrastructure conventions, and troubleshooting — upstream rules files are the authoritative reference
- `githuman` skill: 8 eval scenarios (review, list/cleanup, troubleshooting, inline comments, resolve-and-commit, todos, export, selective staging) enforcing Just recipe usage, plus 20 trigger evals for description auto-triggering tests

## [2026-03-31]

### Added

- `agentic-security-audit` skill: structured audit for AI agent configurations, instruction files, and LLM integration code -- two-phase workflow (discovery + LLM-driven review) mapped to the OWASP Top 10 for Agentic Applications (ASI01-ASI10), with reference files for OWASP agentic patterns and instruction file audit methodology across tools (Copilot, Cursor, OpenCode, Aider, MCP)

### Changed

- `code-security-audit` skill: renamed from `security-audit` to `code-security-audit` to clearly differentiate from `agentic-security-audit` (code security vs AI integration security)
- `code-security-audit` skill: restructured from two-phase to five-phase workflow (Discovery, Generate Containers, Native Scans, Docker Scans, Manual Review) with PHP/Drupal support, per-stack Docker container generation, and an expanded tool matrix spanning multiple container types
- `code-security-audit` skill: pin all 17 scanner versions in Dockerfile templates with SHA-256 checksum verification for binary downloads (trivy, gitleaks, grype, syft, gosec, local-php-security-checker); replace `curl | sh` and `@latest` install patterns with versioned release URLs; add staleness check and version recording to the audit workflow

## [2026-03-29]

### Fixed

- `glab` skill: document that `glab mr close`, `glab issue close`, `glab mr reopen`, and `glab issue reopen` do not accept `--message` -- close/reopen with an explanation requires a separate `note` command first

### Added

- `glab` skill: two new eval cases for close-with-explanation scenarios (MR and issue)
- `playwright-cli` skill: fix npx fallback to use correct package name `@playwright/cli` instead of deprecated `playwright-cli`

## [2026-03-28]

### Fixed

- `glab` skill: warn against `glab ci view` (requires interactive TTY, always fails in agent contexts) and document `glab ci get` as the correct non-interactive alternative for fetching pipeline details
- `glab` skill: fix `glab ci artifact` documentation (wrong syntax and missing deprecation notice)

### Added

- `glab` skill: two new eval cases for pipeline detail retrieval, testing that agents avoid TTY commands and use correct flag syntax

## [2026-03-24]

### Added

- `code-security-audit` skill: two-phase security audit workflow for web applications and APIs -- Phase 1 runs automated open-source scanners (semgrep, trivy, gosec, govulncheck, npm audit, bandit), Phase 2 guides a manual deep review across 10 OWASP-aligned categories with structured findings and a final report template
- `code-security-audit` skill: Go security reference (`references/go-security.md`) covering SQL injection, command injection, path traversal, XSS in templates, cookie security, server hardening, open redirect, HMAC timing attacks, race conditions, and gosec rules
- `code-security-audit` skill: Node.js/frontend security reference (`references/nodejs-security.md`) covering DOM XSS, prototype pollution, SQL/NoSQL injection, path traversal, SSRF, dependency security, Express hardening, CSP, and semgrep rules

## [2026-03-23]

### Added

- `skill-creator` skill: non-Claude agent guidance with bundled script compatibility table and correct terminology mapping for OpenCode/Copilot CLI
- `glab` skill: three new eval cases for squash/merge-behavior flag correctness on MR creation vs merge

### Fixed

- `glab` skill: document `--squash-before-merge` flag for `glab mr create` and warn against using `--squash` (which only works on `glab mr merge`)

## [2026-03-22]

### Added

- `glab` skill: repository files section -- fetch file contents, browse directories, and handle cross-project file access via `glab api` instead of WebFetch/curl
- `glab` skill: three new eval cases for repository file URL scenarios (raw file, blob, tree)
- `gh`, `glab` skills: MR/PR titles must follow the Conventional Commits format (`<type>[(scope)]: <description>`)
- `gh`, `glab` skills: new eval case for Conventional Commits title format in MR/PR creation
- `create-agentsmd` skill: prompt for generating an AGENTS.md file for a repository. Synced from [github/awesome-copilot](https://github.com/github/awesome-copilot)
- GitHub Actions workflow to validate the upstream skills manifest and verify synced skills are up to date

### Changed

- `glab` skill: "Before you start" section now explicitly calls out file URLs (`/-/raw/`, `/-/blob/`, `/-/tree/`) as GitLab resources that require `glab api`
- `glab` skill: updated description to mention repository files and file URLs for better auto-triggering

## [2026-03-21]

### Changed

- `playwright-cli` skill: proactively detect whether `playwright-cli` binary is installed and fall back to `npx playwright-cli` when not found

### Fixed

- `gh`, `glab` skills: AI attribution header now uses blockquote format (`) instead of bare text with `---` separator -- fixes double-separator rendering issues and provides consistent visual distinction on both GitHub and GitLab
- `gh`, `glab` skills: added heredoc warning about single-quoted delimiters suppressing variable expansion in attribution header

## [2026-03-20]

### Added

- `skill-creator` skill: create, iterate, and benchmark agent skills with eval-driven workflows. Synced from [anthropics/skills](https://github.com/anthropics/skills)
- `doc-coauthoring` skill: structured workflow for co-authoring documentation, proposals, and technical specs. Synced from [anthropics/skills](https://github.com/anthropics/skills)
- `gh` skill: GitHub CLI skill for issues, pull requests, Actions, releases, search, PR review comment replies, safety protocol, and API patterns reference with 12 eval scenarios
- `README.md`: skills table and `AGENTS.md` rule to keep it updated when adding/removing skills
- `playwright-cli` skill: browser automation skill synced from [microsoft/playwright-cli](https://github.com/microsoft/playwright-cli), with custom output file conventions (screenshots, PDFs, videos, traces directed to `.playwright-cli/` instead of project root)
- Generic upstream skill sync: `scripts/sync-skill.sh` replaces per-skill sync scripts; `config/upstream-skills.json` manifest with JSON schema declares all upstream skills; `.github/workflows/sync-skills.yml` runs weekly auto-sync

### Changed

- Moved sync manifest and schema from `scripts/` to `config/`

### Removed

- `scripts/sync-playwright-cli.sh` and `.github/workflows/sync-playwright-cli.yml` replaced by generic sync mechanism

### Fixed

- `glab` skill: AI attribution examples now use explicit two-step username capture pattern instead of hardcoded placeholder

## [2026-03-18]

### Added

- `glab` skill: file upload workflow documentation (curl-based workaround for glab api multipart limitation, OAuth vs PAT auth header guidance)
- `glab` skill: two new eval cases for file upload scenarios (image to MR, PDF to issue)
- `AGENTS.md`: git workflow rules requiring feature branches and pull requests

### Changed

- `glab` skill: clarified `-F key=@file` in api-patterns.md to warn it reads as string, not multipart

## [2026-03-07]

### Added

- `the-architect` agent: conversational AI oracle for discovery, brainstorming, architecture, and general knowledge (Copilot and OpenCode profiles)
- `SYSTEM.md`: catalog of system agents and skills with directory conventions, install paths, and available resources

## [2026-03-06]

### Changed

- `glab` skill: prioritize GitLab URL detection in skill description to ensure automatic triggering when users paste GitLab links

### Added

- `glab` skill: explicit instruction to never use WebFetch/curl on GitLab URLs (added to "Before you start" section)
- `glab` skill: eval for GitLab URL-based MR explanation scenario
- `glab` skill: automatic issue template selection when creating issues (fetches templates from the project and asks the user to choose)
- `glab` skill: eval for issue template selection workflow

## [2026-03-05]

### Added

- `glab` skill: instruct agent to always declare comment/note authorship on behalf of the user

### Fixed

- `glab` skill: document `id` vs `iid` milestone pitfall to prevent 404 API errors

### Changed

- `glab` skill: moved from `skills/gitlab/` to `skills/system/` category
- `glab` skill: streamlined milestone `id`/`iid` section for clarity

## [2026-03-04]

### Added

- `glab` skill: initial implementation of the `glab` CLI skill for GitLab operations

### Changed

- `glab` skill: moved from `skills/` root to `skills/gitlab/` category

## [2026-01-08]

### Added

- Initial project commit with repository structure
- LICENSE file
- GitHub Actions workflow for Claude
- README improvements
