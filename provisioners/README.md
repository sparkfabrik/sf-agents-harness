# Provisioners

Provisioners are executable scripts that install agent integrations which
**cannot** be distributed as static files through the normal skill/agent sync.

The standard sync (`skills/system/`, `agents/system/`) copies inert Markdown to
the workstation. Some tools instead ship their agent integration **inside a CLI
binary** and generate it on demand. Vendoring a snapshot of that output drifts
from the installed CLI. A provisioner solves this by generating the integration
from the locally installed tool on every sync, so it always matches the binary.

## Contract

Every provisioner is a single executable script under `provisioners/` that
accepts one verb:

| Verb        | Behavior                                                           |
| ----------- | ------------------------------------------------------------------ |
| `sync`      | Generate and (re)deploy the integration. Idempotent. Default verb. |
| `status`    | Report what is installed (versions, linked resources). Read-only.  |
| `uninstall` | Remove only what this provisioner created. Never touch user files. |

Rules every provisioner must follow:

- **Idempotent** — safe to re-run on every sync.
- **No `brew`/`sudo` in `sync`** — `sf-harness-sync` is fast and sudo-free. If a
  CLI is missing, log a hint pointing to `sjust sf-harness-upgrade` and exit `0`
  so the harness sync is never blocked. CLI installation belongs in the ansible
  upgrade path.
- **No `$HOME` pollution** — stage any tool workspace under
  `~/.cache/sparkdock/`, then symlink the results into the global tool dirs.
- **Own only what you create** — never overwrite a real (non-symlink) file the
  user placed in a target directory.

## How sparkdock runs them

`sf-harness-sync` clones this repo into `~/.cache/sparkdock/agent-skills`, then
copies skills and agents. A generic runner in `bin/sparkdock-agents-sync`
executes each provisioner after the file-copy phase:

```bash
# After sync_skills / sync_agents / cleanup, in main():
if [[ -d "${CACHE_DIR}/provisioners" ]]; then
    for p in "${CACHE_DIR}/provisioners"/*.sh; do
        [[ -x "${p}" ]] || continue
        "${p}" sync
    done
fi
```

`harness-status.sh` does the same with the `status` verb. This is a one-time,
tool-agnostic hook: adding a new provisioned tool means dropping one script
here, with no further sparkdock changes.

> **Trust boundary.** This hook makes sparkdock execute scripts from this repo on
> every workstation during sync. Anyone who can merge here can run code on all
> machines. Provisioners run as the user (no sudo) and are gated by code review.

## Available provisioners

| Script        | Tool     | What it installs                                                |
| ------------- | -------- | --------------------------------------------------------------- |
| `openspec.sh` | OpenSpec | OpenSpec skills + `/opsx:*` commands + guard hook for Claude Code |

### `openspec.sh`

Generates OpenSpec skills and commands from the installed `openspec` CLI into a
staging workspace under `~/.cache/sparkdock/openspec`, then symlinks them into
Claude Code's global directories: `~/.claude/skills/openspec-*` and
`~/.claude/commands/opsx`.

Symlinks mean a later `openspec update` of the staging area is picked up with no
redeploy. The CLI must be installed separately (via `sf-harness-upgrade`); if it
is absent, `sync` logs a hint and exits cleanly.

It also installs a guard hook: `hooks/openspec-guard.sh` is copied to
`~/.claude/hooks/` and registered in `~/.claude/settings.json` on the
`UserPromptSubmit` and `PreToolUse` events. The guard blocks OpenSpec slash
commands, the `openspec` CLI, and OpenSpec skills when the current directory has
no `openspec/` folder. Registration is idempotent and preserves any other hooks;
`uninstall` removes the entries and the script. Requires `jq` (skipped with a
warning if absent).

Run manually:

```bash
provisioners/openspec.sh sync       # generate + link
provisioners/openspec.sh status     # show version + linked counts
provisioners/openspec.sh uninstall  # remove the symlinks
```
