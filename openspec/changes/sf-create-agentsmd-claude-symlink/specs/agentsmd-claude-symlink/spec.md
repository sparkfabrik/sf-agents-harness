## ADDED Requirements

### Requirement: Auto-create CLAUDE.md alias at project root

The `sf-create-agentsmd` skill SHALL ensure a `CLAUDE.md` symlink to the root `AGENTS.md` exists at the project root after handling the root `AGENTS.md` in either Scaffold mode (no prior AGENTS.md) or Pkg-managed mode (root AGENTS.md already present, project additions targeted at `.agents/AGENTS.project.md`).

The symlink target SHALL be the relative path `AGENTS.md` (not an absolute path), so the link survives clones, moves, and worktrees.

The skill SHALL surface the action taken (created, skipped, or warned) in its post-action summary.

#### Scenario: Fresh scaffold with no CLAUDE.md present

- **WHEN** the skill scaffolds a new root `AGENTS.md` in a project where no `CLAUDE.md` exists at the root
- **THEN** the skill SHALL create a symlink at `<root>/CLAUDE.md` pointing to the relative target `AGENTS.md`
- **THEN** the skill SHALL report the action in its post-action summary (e.g. "Created CLAUDE.md → AGENTS.md symlink at project root.")

#### Scenario: Pkg-managed project with existing root AGENTS.md but no CLAUDE.md

- **WHEN** the skill is invoked in a pkg-managed project (`fs-pkg.json` present), the root `AGENTS.md` already exists, and `<root>/CLAUDE.md` does not exist
- **THEN** the skill SHALL create a symlink at `<root>/CLAUDE.md` pointing to the relative target `AGENTS.md`, independently of whether project additions are also written to `.agents/AGENTS.project.md`

#### Scenario: Idempotent run with matching symlink

- **WHEN** `<root>/CLAUDE.md` already exists as a symlink whose target resolves to the root `AGENTS.md`
- **THEN** the skill SHALL leave the symlink untouched and SHALL NOT print a warning

### Requirement: Preserve any pre-existing CLAUDE.md

The skill SHALL never overwrite, delete, or replace an existing `CLAUDE.md` file or symlink whose target differs from `AGENTS.md`. When such a file is present, the skill SHALL skip symlink creation and SHALL warn the user so the conflict can be reconciled manually.

#### Scenario: Existing CLAUDE.md is a regular file

- **WHEN** `<root>/CLAUDE.md` exists as a regular (non-symlink) file
- **THEN** the skill SHALL NOT modify or delete the file
- **THEN** the skill SHALL warn the user (e.g. "CLAUDE.md already exists at project root as a regular file. Skipping symlink creation — reconcile manually if needed.")

#### Scenario: Existing CLAUDE.md is a symlink to a different target

- **WHEN** `<root>/CLAUDE.md` exists as a symlink whose target is not the root `AGENTS.md`
- **THEN** the skill SHALL NOT modify or delete the symlink
- **THEN** the skill SHALL warn the user identifying the current target so the user can reconcile manually

### Requirement: Prompt with default No for non-root AGENTS-style files

When the AGENTS-style file handled in the run is NOT the project root `AGENTS.md` — for example a monorepo subproject `AGENTS.md`, `.agents/AGENTS.project.md`, or an alternate filename — the skill MUST ask the user whether to create a `CLAUDE.md` alias alongside that file. The default answer SHALL be **No**. The skill SHALL create the symlink only when the user explicitly confirms.

When the user confirms, the same existing-file rules from "Preserve any pre-existing CLAUDE.md" apply at the prompted location.

#### Scenario: User declines for monorepo subproject AGENTS.md

- **WHEN** the skill generates a subproject `AGENTS.md` (e.g. `packages/api/AGENTS.md`) and asks whether to create a sibling `CLAUDE.md` alias
- **AND** the user accepts the default (No) or explicitly declines
- **THEN** the skill SHALL NOT create any symlink and SHALL proceed without warning

#### Scenario: User confirms for non-root path

- **WHEN** the skill prompts for a `CLAUDE.md` alias next to a non-root AGENTS-style file and the user explicitly answers Yes
- **AND** no `CLAUDE.md` exists at that sibling location
- **THEN** the skill SHALL create a symlink at that location with the relative target equal to the sibling AGENTS-style filename actually generated (e.g. `AGENTS.md` or `AGENTS.project.md`)

#### Scenario: User confirms but a conflicting CLAUDE.md exists at the target location

- **WHEN** the user explicitly answers Yes for a non-root location and a `CLAUDE.md` (regular file, or symlink pointing elsewhere) already exists at that location
- **THEN** the skill SHALL skip creation and warn the user, mirroring the root-level conflict behavior
