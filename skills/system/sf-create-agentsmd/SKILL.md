---
name: sf-create-agentsmd
description: 'Generate or review AGENTS.md files following team conventions. Use when bootstrapping a project, creating or reviewing AGENTS.md, or auditing agent instructions. Trigger on: "create agents.md", "review agents.md", "bootstrap agents", "audit agents.md", "sf-create-agentsmd".'
---

# SF Create AGENTS.md

You are a code agent. Your task is to generate a new AGENTS.md or review an existing one for the current repository. The AGENTS.md must follow the conventions described in this skill and be tailored to what actually exists in the project.

AGENTS.md is an open format ([agents.md specification](https://agents.md/)) that provides coding agents with the context and instructions they need to work effectively on a project. It complements README.md with agent-specific technical instructions.

## Mode Detection

Determine the mode based on what exists in the project root:

1. **Pkg-managed project** (`fs-pkg.json` exists): the root AGENTS.md is managed by the infrastructure package system — **never overwrite it**. Instead, check for `.agents/AGENTS.project.md`:

   a. **File exists and has real content** (not just whitespace or empty frontmatter): warn the user that both AGENTS.md and the project additions file are already populated. **Stop — do not generate.**

   b. **File exists but is empty**: switch to **Project Additions mode** — run the normal discovery, but generate content into `.agents/AGENTS.project.md` instead of the root AGENTS.md. Focus on project-specific additions that complement the pkg-managed base (project overview, setup specifics, code style overrides, testing commands, etc.). Do not duplicate conventions already covered by the pkg-managed AGENTS.md.

   c. **File does not exist**: check whether the root AGENTS.md references `.agents/AGENTS.project.md`. If referenced (the slot exists but the file is missing), offer to create and populate it — same as case (b). If not referenced, warn the user that this is a pkg-managed project with no project extension point and suggest they create `.agents/AGENTS.project.md` manually or update their package to include the reference.

2. **No AGENTS.md exists** → **Scaffold mode**: discover the project and generate a full AGENTS.md.

3. **AGENTS.md exists** (not pkg-managed) → **Review mode**: discover the project, compare against the existing AGENTS.md, report gaps and suggest updates.

## Step 1: Discover the Project

Before generating or reviewing anything, inspect the project to understand what is actually there. **Never assume — always verify.**

### Discovery Checklist

Inspect all of the following. For each category, note what was found.

**Task Runners**

- `Justfile` (preferred — look for recipe names with `just --list` or read the file)
- `Makefile` (fallback — look for target names)
- If neither exists, note the absence and recommend creating a Justfile

**Docker**

- `compose.yml` or `docker-compose.yml` — count the services
- `build/Dockerfile` or `Dockerfile` at project root
- `.env.dist` or `.env.example` for environment variable templates

**Languages and Package Managers**

- Python: `pyproject.toml`, `requirements.txt`, `uv.lock`, `poetry.lock`
- PHP: `composer.json`, `composer.lock`
- Node: `package.json`, `package-lock.json`, `pnpm-lock.yaml`, `yarn.lock`
- Go: `go.mod`, `go.sum`
- Rust: `Cargo.toml`, `Cargo.lock`
- Note each detected language and its package manager

**CI/CD**

- `.gitlab-ci.yml`
- `.github/workflows/`

**Linters and Formatters**

- Python: `ruff.toml`, `pyproject.toml` `[tool.ruff]` section, `.flake8`
- PHP: `.phpcs.xml`, `phpcs.xml`, `grumphp.yml`, `phpstan.neon`
- Node: `.eslintrc*`, `eslint.config.*`, `.prettierrc*`
- Go: `golangci-lint` config
- General: `.editorconfig`

**Test Suites**

- Python: `pytest.ini`, `pyproject.toml` `[tool.pytest]` section, `tests/`, `test/`
- PHP: `phpunit.xml`, `phpunit.xml.dist`, `behat.yml`
- Node: `jest.config.*`, `vitest.config.*`, `__tests__/`, `*.test.*`, `*.spec.*`
- Go: `*_test.go` files
- Rust: `#[test]` modules, `tests/` directory

**Change Management**

- `openspec/` directory (OpenSpec change management)

**Existing Documentation**

- `AGENTS.md` (triggers review mode)
- `README.md` (extract project description)
- `docs/` directory

## Step 2: Determine Execution Environment Convention

Based on discovery results, determine whether the project follows a Docker-first or local-development convention. This affects how setup, commands, and package management sections are written.

### Docker-first Convention

Apply when ANY of:

- `compose.yml` defines 2 or more services
- PHP or Drupal project (always Docker-first regardless of service count)
- Python project with databases, queues, or external services in compose

Docker-first means:

- **Never install packages or runtimes locally.** All commands run inside Docker via the task runner.
- Setup uses `just build && just install` or equivalent Docker-based commands.
- Package management commands are wrapped: `just run sh -c "cd <path> && <command>"`
- Caches are stored in a project-local directory (e.g., `.caches/`) to avoid polluting the host.

### Local Development Convention

Apply when ALL of:

- No compose.yml, OR compose.yml has only auxiliary services (database, cache)
- Language is Go, Node/npm, or Rust

Local development means:

- Local runtimes are fine. Use the system or version-managed interpreter directly.
- Task runner (`just`) wraps common operations but does not require Docker for every command.
- Docker is available for auxiliary services or integration testing, not for daily development.

## Step 3: Generate or Review

### Scaffold Mode (no AGENTS.md)

Generate a complete AGENTS.md with all applicable sections from the blueprint below.

### Review Mode (AGENTS.md exists)

1. Read the existing AGENTS.md in full.
2. Compare it against the section blueprint below.
3. Check for:
   - **Missing sections**: mandatory sections not present
   - **Stale content**: references to tools, commands, or files that no longer exist
   - **Undocumented tooling**: package managers, linters, test suites, or CI configs found in the project but not mentioned in AGENTS.md
   - **Missing supply chain safety section**: no dependency verification guidance
   - **Missing command safety policy**: no tiered command classification
   - **Task runner drift**: Makefile referenced but Justfile now exists (or vice versa)
   - **Docker conventions undocumented**: compose.yml exists but execution environment not described
   - **Missing git workflow section**: no branch naming, commit, or rebase conventions
   - **Missing OpenSpec section**: `openspec/` directory exists but not documented
4. Present the list of gaps with specific recommendations.
5. Offer to generate the missing sections, or rewrite the full AGENTS.md incorporating fixes.

## Section Blueprint

The following sections form the AGENTS.md structure. **Mandatory sections are always included.** Conditional sections are included only when their trigger condition is met.

### 1. Project Overview (mandatory)

Brief description of the project, its purpose, and key technologies. Infer from README.md or ask the user.

```markdown
## Project Overview

[Description of the project, its purpose, and architecture if complex.]

**Tech stack:** [Languages, frameworks, key libraries, infrastructure.]
```

### 2. Setup (mandatory)

How to get the project running locally. Adapt based on execution environment convention.

**Docker-first example:**

```markdown
## Setup

Everything runs in Docker. No local [language] or [package manager] required.

\`\`\`bash
just build      # Build the Docker image
just install    # Install dependencies
\`\`\`

Run `just` or `just --list` to see all available commands.
```

**Local development example:**

```markdown
## Setup

\`\`\`bash
just install    # Install dependencies
just dev        # Start development server
\`\`\`

Run `just` or `just --list` to see all available commands.
```

If no task runner exists, recommend creating a Justfile and document the raw commands in the meantime.

### 3. Key Conventions (mandatory)

Project-specific conventions that agents must follow.

**Docker-first projects** must include:

- Docker-only execution — never install packages locally
- How commands are run (e.g., `just run`, `bin/<wrapper>`, `docker compose run`)
- Cache locations (`.caches/`, etc.)
- Environment file conventions (`.env.dist` → `.env`)

**Local development projects** must include:

- Task runner usage for common operations
- Environment file conventions if applicable
- Any wrapper scripts in `bin/` or `scripts/`

### 4. Code Style (mandatory when linter configs found)

Per-language lint and format rules extracted from the actual config files. Include:

- Linter name and key rules
- Format command
- Lint check command

```markdown
## Code Style

- **[Language]**: [Linter] ([key settings])
  - [Notable rules or overrides]
- Run `just lint` before committing
```

### 5. Git Workflow (mandatory)

Always include all three subsections: commits, branching, and rebasing.

```markdown
## Git Workflow

### Commits

Follow [Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/):

\`\`\`
<type>(<scope>): <description>
\`\`\`

**Types:** `feat`, `fix`, `refactor`, `docs`, `test`, `chore`, `ci`, `perf`, `build`.
**Scope** is optional — use the affected component.

Keep the description lowercase, imperative, no period.

### Branching

- Branch naming: `feat/`, `fix/`, `chore/`, `test/`, `docs/` prefix + kebab-case description
  (e.g., `feat/add-export-csv`, `fix/broken-auth-redirect`)
- **Never push directly to `main` or `master`.** Always create a feature branch and open a pull/merge request.

### Rebasing

- Always rebase onto `main` before pushing. No merge commits.
- Use `--force-with-lease` (never `--force`) after rebasing.
- Rebase before the first push, before opening a PR/MR, and whenever the base branch advances.
```

### 6. OpenSpec Change Management (conditional: `openspec/` directory exists)

```markdown
## OpenSpec Change Management

Spec artifacts live in `openspec/changes/<name>/`, archived in `openspec/changes/archive/YYYY-MM-DD-<name>/`.

### Git workflow for specs

OpenSpec itself has no opinion on git — it is a local file workflow. We add these conventions:

1. **Always commit spec artifacts to git** — never leave proposals, designs, specs, or tasks untracked. Commit them as soon as they are created or updated.

2. **Non-trivial changes: spec-first PR/MR** — for changes that span multiple files, involve architectural decisions, or require infrastructure work:
   - Create a branch (e.g., `docs/<issue>-<name>-spec`)
   - Commit the proposal, design, specs, and tasks
   - Open a PR/MR for review ("is this the right plan?")
   - Merge the spec PR/MR **before** starting implementation
   - This creates a review checkpoint and prevents building on a wrong design

3. **Trivial changes: spec + implementation in one PR/MR** — for small, well-scoped changes (single module, clear scope), spec and code can go in the same PR/MR.

4. **Archive on merge** — when the implementation is complete, archive the change (`openspec/changes/<name>/` -> `openspec/changes/archive/YYYY-MM-DD-<name>/`) as part of that PR/MR or as an immediate follow-up. Do not leave completed changes in the active directory.
```

### 7. Package Management (mandatory when any package manager is detected)

Generate a subsection for each detected language/package manager with:

- How to add a dependency
- How to add a dev dependency
- Lock-before-install workflow

Then always include the **Dependency Safety** subsection.

**Docker-first example (Python with uv):**

```markdown
## Package Management

### Python (uv)

- Add: `just run sh -c "cd <path> && uv add <package>"`
- Dev: `just run sh -c "cd <path> && uv add --group dev <package>"`
- Lock then install: `just lock && just install`
```

**Local development example (Node with npm):**

```markdown
## Package Management

### Node (npm)

- Add: `npm install <package>`
- Dev: `npm install --save-dev <package>`
- Lock then install: `npm install` (updates lock automatically)
```

### Dependency Safety (always include when package management section exists)

This subsection is non-negotiable. Include it verbatim, adapting only the registry check commands to the detected package managers.

```markdown
### Dependency Safety

Before adding or upgrading any dependency, follow these rules:

1. **Never assume you know the latest version.** Your training data is outdated. Always verify against the live registry before adding or upgrading any package.

2. **Check the live registry** using the commands below:
```

Then include the relevant commands for each detected package manager:

**Python (PyPI):**

```bash
curl -s https://pypi.org/pypi/<package>/json | jq '{version: .info.version, requires_python: .info.requires_python}'
```

**PHP (Packagist):**

```bash
curl -s "https://repo.packagist.org/p2/<vendor>/<package>.json" | jq '[.packages["<vendor>/<package>"][] | {version, time}] | .[0:5]'
```

**Node (npm):**

```bash
curl -s https://registry.npmjs.org/<package>/latest | jq '{version: .version, engines: .engines}'
```

**Go:**

```bash
curl -s "https://proxy.golang.org/<module>/@latest" | jq .
```

**Rust (crates.io):**

```bash
curl -s "https://crates.io/api/v1/crates/<crate>" | jq '{max_stable: .crate.max_stable_version, updated: .crate.updated_at}'
```

Continue the subsection:

```markdown
3. **Use the newest stable major version** compatible with the project runtime. Check actual compatibility metadata (classifiers, `requires_python`, `require.php`, `engines.node`, etc.).

4. **Avoid releases published within the last 5 days** to reduce supply chain attack risk. Check the release date from the registry response.

5. **Always regenerate the lockfile** after changing dependency manifests, then install from the lock.
```

### 8. Testing (mandatory when test configs are found)

Document detected test suites with their commands, file locations, and patterns.

```markdown
## Testing

`just test` runs [description of what test runs].

- [Language] tests live in `[path]`.
- [Other language] tests live in `[path]`.
```

Include any integration test details, fixtures, or special requirements.

### 9. CI/CD Awareness (conditional: CI config found)

Document the CI pipeline stages, key jobs, and deployment info. Adapt to the detected CI system (GitLab CI, GitHub Actions, etc.).

```markdown
## CI/CD

The project uses [CI system] with stages: [list stages].

### Key Jobs

| Job | Stage | Purpose |
|-----|-------|---------|
| ... | ...   | ...     |
```

### 10. Command Safety Policy (mandatory)

Classify every command found in the project into three tiers. **Scan the Justfile/Makefile, compose.yml, and scripts/ directory** to populate these tiers with actual commands, not just generic examples.

```markdown
## Command Safety

### Safe (run autonomously)

These commands are read-only or non-destructive. Agents may run them freely:

- [List actual safe commands found in the project]
- Examples: `just test`, `just lint`, `git status`, `git log`, `git diff`

### Dangerous (ask user first)

These commands modify state. **Always ask for user confirmation before running:**

- [List actual dangerous commands found in the project]
- Examples: dependency changes, database mutations, `git push`, deploy commands

### Destructive (never run)

**Never execute these under any circumstances:**

- [List actual destructive commands found in the project]
- Examples: `rm -rf`, `git push --force`, database drops, teardown commands
```

### 11. Important Rules (mandatory)

Aggregated guardrails — the critical "always/never" rules for agents working on this project. Collect these from all previous sections into a single summary.

```markdown
## Important Rules

- [Rule 1 — e.g., "Never install packages locally — everything runs in Docker via `just`"]
- [Rule 2 — e.g., "Always verify library compatibility on the live registry before adding or upgrading"]
- [Rule 3 — e.g., "Use the latest stable major version of every dependency"]
- [Rule 4 — e.g., "Run `just lint` before committing"]
- [Rule 5 — e.g., "Follow conventional commits"]
- [...]
```

## Monorepo Considerations

For monorepos with multiple packages or services under `src/`:

- Place the main AGENTS.md at the repository root covering shared conventions (git workflow, command safety, supply chain safety).
- Create additional AGENTS.md files in subproject directories for package-specific instructions (language-specific linting, test commands, build steps).
- The closest AGENTS.md file takes precedence for any given location — agents read the nearest one first.
- Keep shared rules in the root file to avoid duplication across subproject files.

## Writing Guidelines

- **Be specific.** Include exact commands, not vague descriptions. Agents execute what you write.
- **Use code blocks.** Wrap all commands in backticks.
- **Stay grounded.** Only document what actually exists in the project. Do not invent tools, commands, or configurations.
- **Keep it dry.** No filler, no motivational language, no emojis. Technical instructions only.
- **Test commands.** Before including a command, verify it exists in the Justfile/Makefile or is otherwise runnable.
- **Prefer Justfile.** If both Justfile and Makefile exist, document Justfile commands. If only Makefile exists, use it but note that the project should transition to Just.
- **Adapt, do not copy.** The templates above are structural guides. Adapt every section to the specific project based on discovery results.
