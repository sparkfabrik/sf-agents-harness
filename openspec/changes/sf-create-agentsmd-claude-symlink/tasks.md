## 1. SKILL.md Updates

- [x] 1.1 Add a new section **Step 4: Ensure CLAUDE.md alias** after the existing Step 3 in `skills/system/sf-create-agentsmd/SKILL.md`, covering: default auto-create for root AGENTS.md, the four existing-file cases (absent, regular file, matching symlink, mismatched symlink), explicit prompt with default No for non-root paths, and the relative-target rule.
- [x] 1.2 Update **Mode Detection** section so the pkg-managed branch (cases a/b/c) notes that the CLAUDE.md alias step (Step 4) still runs against the existing root AGENTS.md, independently of `.agents/AGENTS.project.md` handling.
- [x] 1.3 Update **Monorepo Considerations** with one bullet noting that the CLAUDE.md alias step is offered (default No) for subproject AGENTS.md files.
- [x] 1.4 Reference Step 4 in the post-action summary guidance so the action taken (created / skipped+warned / idempotent no-op) is reported.

## 2. Evals

- [x] 2.1 Add eval `scaffold-creates-claude-symlink` to `skills/system/sf-create-agentsmd/evals/evals.json` covering: scaffold mode in a clean dir creates root AGENTS.md AND root CLAUDE.md symlink to AGENTS.md.
- [x] 2.2 Add eval `existing-claude-md-warns` to `skills/system/sf-create-agentsmd/evals/evals.json` covering: a pre-existing regular `CLAUDE.md` is preserved and the skill warns.
- [x] 2.3 Add eval `subdir-asks-before-symlink` to `skills/system/sf-create-agentsmd/evals/evals.json` covering: non-root AGENTS.md request prompts the user for the alias with default No.

## 3. Validation

- [x] 3.1 Run `openspec validate sf-create-agentsmd-claude-symlink` and resolve any errors.
- [x] 3.2 Run `openspec show sf-create-agentsmd-claude-symlink` and confirm the rendered proposal, specs, design, and tasks read coherently.
- [x] 3.3 Manually rehearse the four end-to-end scenarios from the verification section of the plan (scaffold, existing regular CLAUDE.md, pkg-managed, non-root prompt) against a scratch directory.
