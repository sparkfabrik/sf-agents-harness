---

## SparkFabrik notes

These notes adapt `glab stack` to SparkFabrik's self-hosted GitLab and conventions. Read the `glab` skill first; everything there (host targeting, safety tiers, attribution) applies to stack operations too.

### Self-hosted GitLab CE

`glab stack` is a client-side feature: it chains merge requests by **branch targeting** (each MR targets the source branch of the one below it), not the Premium "Merge Request Dependencies" API. It works on GitLab Free and on self-hosted Community Edition.

Stack commands act on the repository's configured remote. For a repo on a self-hosted GitLab instance, confirm the remote (or `GITLAB_HOST`) points there before running `glab stack sync`, exactly as described in the `glab` skill. A misconfigured host silently pushes branches and opens MRs against the wrong instance.

### Commit messages and MR titles

`glab stack save -m "<message>"` turns the message into both a commit subject and the title of the MR opened on sync. Write it as a Conventional Commit (`feat(scope): ...`, `fix: ...`) per the SparkFabrik commit convention. Each diff in the stack is one logical change, so one well-formed conventional subject per `save` keeps the stack's MRs consistent with the rest of our history.

### Attribution and issue references

MRs opened by `glab stack sync` are AI-authored artifacts. Apply the same rules as the `glab` skill: include the `:robot:` attribution header in each MR description and reference the related issue with a fully qualified path (`group/project#42`). Write descriptions in plain prose, never in a terse or caveman style.

### Agent rules (reaffirmed)

- Always pass `-m` to `save` and `amend`; without it these commands open an interactive prompt and hang.
- Never run `glab stack move` or `glab stack reorder` from an agent — both require an interactive TUI or editor. Tell the user to run them directly.
- Navigate with `first` / `last` / `prev` / `next` and switch stacks with an explicit name; do not rely on interactive selection.
