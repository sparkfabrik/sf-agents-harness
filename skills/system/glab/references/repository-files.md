# Repository files

There is no `glab` subcommand for fetching file contents from a repository. Use `glab api` with the GitLab Repository Files API. This is the correct approach whenever a user shares a GitLab file URL or asks to read a file from a GitLab project -- **never** use WebFetch or curl, because GitLab instances (especially self-hosted ones) require authentication.

## Recognizing file URLs

GitLab file URLs follow these patterns:

| URL pattern                            | Meaning                               |
| -------------------------------------- | ------------------------------------- |
| `.../<project>/-/raw/<branch>/<path>`  | Raw file content                      |
| `.../<project>/-/blob/<branch>/<path>` | File viewer (same file, different UI) |
| `.../<project>/-/tree/<branch>/<path>` | Directory listing                     |

When you see any of these, extract the **hostname**, **project path**, **branch**, and **file path**, then use `glab api`.

**Example** -- parsing a real URL:

```
URL: https://gitlab.example.com/team/infra/platform/-/raw/main/deploy/docker-compose.yml?ref_type=heads

  hostname: gitlab.example.com
  project:  team/infra/platform
  branch:   main
  file:     deploy/docker-compose.yml
```

Ignore query parameters like `?ref_type=heads` -- they are UI artifacts, not needed for the API.

## Fetching a file

File paths in the API endpoint must be **URL-encoded** (slashes become `%2F`):

```bash
# File at root (no slashes in path -- no encoding needed):
GITLAB_HOST=gitlab.example.com glab api \
  "projects/team%2Finfra%2Fplatform/repository/files/.gitlab-ci.yml/raw?ref=main"

# File in a subdirectory (slashes must be encoded):
# deploy/docker-compose.yml → deploy%2Fdocker-compose.yml
GITLAB_HOST=gitlab.example.com glab api \
  "projects/team%2Finfra%2Fplatform/repository/files/deploy%2Fdocker-compose.yml/raw?ref=main"
```

The `/raw` suffix returns the file content directly as plain text. Without `/raw`, the API returns JSON with base64-encoded content -- use `/raw` unless you need the metadata.

When you're **inside the target repo's git clone**, the `:id` placeholder is resolved automatically:

```bash
glab api "projects/:id/repository/files/.gitlab-ci.yml/raw?ref=main"
```

## Browsing a directory

```bash
# List files in a directory
GITLAB_HOST=gitlab.example.com glab api \
  "projects/team%2Finfra%2Fplatform/repository/tree?ref=main&path=deploy" \
  | jq '.[].name'

# Recursive listing (use recursive=true)
glab api "projects/:id/repository/tree?ref=main&recursive=true" | jq '.[].path'
```

## Cross-project file access

When the user references a file from a **different project** than the one you're currently in, you must URL-encode the full project path (slashes as `%2F`) and set `GITLAB_HOST`:

```bash
# Reading a file from another project on the same instance:
GITLAB_HOST=gitlab.example.com glab api \
  "projects/other-team%2Fshared-configs/repository/files/templates%2F.gitlab-ci.yml/raw?ref=main"
```

---
