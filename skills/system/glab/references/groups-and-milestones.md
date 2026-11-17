# Groups, projects and milestones

Use `glab api` for these operations: no `glab` subcommand covers them.

## Group-level operations

There is no `glab` subcommand for group operations -- use `glab api` with URL-encoded group paths (slashes as `%2F`):

```bash
# List projects in a group
GITLAB_HOST=gitlab.example.com glab api \
  "groups/team%2Fsubgroup/projects" --paginate | jq -s 'add | .[].name' -r | sort

# Include descendant subgroups
GITLAB_HOST=gitlab.example.com glab api \
  "groups/team%2Fsubgroup/projects?include_subgroups=true" --paginate \
  | jq -s 'add | .[].path_with_namespace' -r
```

Placeholder variables (auto-resolved inside a git repo): `:id`, `:fullpath`, `:repo`.

## Creating groups and subgroups

There is no `glab` subcommand for group creation -- use `glab api` with `POST groups`. To create a **subgroup**, pass the parent group's numeric id via `parent_id`:

```bash
# Resolve the parent group id first (URL-encode the path, slashes as %2F):
GITLAB_HOST=gitlab.example.com glab api "groups/team%2Fresearch" | jq '.id'

# Create the subgroup under that parent:
GITLAB_HOST=gitlab.example.com glab api -X POST groups \
  -f name="AI Research" \
  -f path="ai-research" \
  -f parent_id=196 \
  -f description="Research group for PoCs." \
  -f visibility="private"
```

`name` is the human-readable display name; `path` is the URL slug (lowercase, hyphens). A subgroup's `visibility` cannot be more open than its parent (a `private` parent cannot contain a `public` subgroup). Omit `parent_id` to create a top-level group.

## Transferring a project to another namespace

Validate the target first, then transfer. `transfer_locations` returns every namespace the current user is allowed to move the project into, with both `id` and `full_path`:

```bash
# 1. List valid target namespaces:
glab api "projects/:id/transfer_locations" \
  | jq '.[] | {id, full_path}'

# 2. Transfer to the target namespace (numeric group id):
glab api -X PUT "projects/<project-id>/transfer" -f namespace=<group-id>
```

> **Method gotcha (PUT, not POST):** the historical GitLab API docs describe this endpoint as `POST /projects/:id/transfer`, but current GitLab (verified on 18.11 with glab 1.106) does not register the route for `POST` -- a `POST` returns a bare `{"error":"404 Not Found"}` while `PUT` reaches the handler. Use `PUT`. If a `PUT` unexpectedly 404s on an older instance, fall back to `POST`.

The transfer preserves the project's numeric id, history, issues, and MRs, and GitLab leaves a redirect from the old path. Two follow-ups are still required:

- **Update local git remotes** to the new `path_with_namespace` (returned in the transfer response). The old SSH/HTTPS URL keeps working via the redirect, but the canonical path has changed.
- You need **Owner** (or Maintainer, depending on instance settings) on both the project and the target namespace. If `transfer_locations` does not list your intended target, you lack the rights or the target violates a constraint (for example a visibility mismatch), and the transfer will fail.

## Milestones -- `id` vs `iid`

Always look up milestones **by title**, not by numeric ID — this avoids the `id`/`iid` confusion entirely:

```bash
# CORRECT -- lookup by title:
GITLAB_HOST=gitlab.example.com glab api "projects/group%2Frepo/milestones?title=Sprint+49"

# WRONG -- iid (project-scoped) used as path param → 404:
GITLAB_HOST=gitlab.example.com glab api "projects/group%2Frepo/milestones/58"
```

If you must use a numeric ID, use the global `id` field (not `iid`) from the API response:
`{ "id": 551, "iid": 58 }` → use `551` in the path, never `58`.

---
