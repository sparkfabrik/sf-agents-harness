# drupal.org api-d7 + git.drupalcode.org API reference

All endpoints verified working unauthenticated via `curl` (2026-07). Append `.json` to api-d7 resources. Responses are paged (`page=N` param, ~50 items/page); `self`/`last` links in the envelope tell you the page count.

## Contents

- [Resolve a project](#resolve-a-project)
- [List / filter issues](#list--filter-issues)
- [Issue field reference (status, priority, category codes)](#issue-field-reference)
- [Read an issue + comments](#read-an-issue--comments)
- [Resolve patch file attachments](#resolve-patch-file-attachments)
- [git.drupalcode.org GitLab API](#gitdrupalcodeorg-gitlab-api)
- [What does NOT work](#what-does-not-work)

## Resolve a project

```bash
# Contrib module (also: type=project_theme, project_distribution)
curl -s "https://www.drupal.org/api-d7/node.json?type=project_module&field_project_machine_name=<machine_name>"
# → list[0].nid is the project nid, list[0].title the human name
```

Drupal core is `type=project_core`, machine name `drupal`, **nid 3060** (stable, hardcode it).

Useful project fields: `field_project_machine_name`, `field_project_type` (full/sandbox), `field_maintenance_status`, `field_development_status`, `field_project_has_issue_queue`, `taxonomy_vocabulary_44` (maintenance status term), `field_supporting_organizations`.

## List / filter issues

```bash
curl -s "https://www.drupal.org/api-d7/node.json?type=project_issue&field_project=<nid>&sort=changed&direction=DESC"
```

Extra filters, combinable: `field_issue_status=<code>`, `field_issue_version=<e.g. 5.0.x-dev>`, `field_issue_category=<code>`, `field_issue_priority=<code>`, `title=<EXACT title>` (exact match only — no substring/full-text; use WebSearch for that).

## Issue field reference

`field_issue_status`:

| Code | Meaning | Code | Meaning |
|---|---|---|---|
| 1 | Active | 13 | Needs work |
| 2 | Fixed (recently) | 14 | Reviewed & tested (RTBC) |
| 3 | Closed (duplicate) | 15 | Patch (to be ported) |
| 4 | Postponed | 16 | Postponed (needs more info) |
| 5 | Closed (won't fix) | 17 | Closed (outdated) — rare |
| 6 | Closed (works as designed) | 18 | Closed (outdated) |
| 7 | Closed (fixed) | 19 | Closed (cannot reproduce) |
| 8 | Needs review | | |

Trust order for a fix: 7/2 (fixed — find the release) > 14 (RTBC) > 8 (needs review) > 13 (needs work — read comments for what's broken) > 1 (active).

`field_issue_priority`: 400 Critical, 300 Major, 200 Normal, 100 Minor.
`field_issue_category`: 1 Bug, 2 Task, 3 Feature request, 4 Support request, 5 Plan.

Other useful issue fields: `field_issue_version`, `field_issue_component`, `field_issue_related` (linked issues — follow duplicate chains), `field_issue_files` (attachments), `comment_count`, `changed` (unix ts — staleness check), `url` (canonical issue URL).

## Read an issue + comments

```bash
# Single issue by nid
curl -s "https://www.drupal.org/api-d7/node.json?type=project_issue&nid=<nid>"

# All comments, chronological. Comment N on the web page = Nth item in this list
# (matters for patch naming: #<nid>_CM<N>.patch)
curl -s "https://www.drupal.org/api-d7/comment.json?node=<nid>"
# → list[].comment_body.value (HTML), list[].name (author), list[].created
```

Comments hold the actual solutions: workarounds, "patch in #12 works on 10.3", re-rolls, duplicate pointers. Parse the HTML body (strip tags is fine).

## Resolve patch file attachments

`field_issue_files` entries reference file entities, not URLs:

```bash
# field_issue_files[i].file.id → fid
curl -s "https://www.drupal.org/api-d7/file/<fid>.json"
# → .name (e.g. "2313309-toolbar-language.patch") and .url (direct download, not challenge-blocked)
```

## git.drupalcode.org GitLab API

Standard GitLab v4, public read, no token. Project path is always `project%2F<machine_name>` (URL-encoded `project/<machine_name>`).

```bash
BASE="https://git.drupalcode.org/api/v4/projects/project%2F<machine_name>"
curl -s "$BASE"                                        # default_branch, last_activity_at
curl -s "$BASE/merge_requests?state=all&per_page=20"   # MRs; iid, state, title, source_branch, web_url
curl -s "$BASE/merge_requests/<iid>/notes"             # MR discussion
curl -s "$BASE/releases"                               # tagged releases + notes
curl -s "$BASE/repository/tree?ref=<branch>"           # browse files
curl -s "$BASE/repository/files/<url-enc-path>/raw?ref=<branch>"  # read a file
```

MR titles usually embed the d.o issue nid ("Issue #3529537: ..."), linking the two systems.

Direct MR diff download (for patching): `https://git.drupalcode.org/project/<name>/-/merge_requests/<iid>.diff` (also `.patch` for mail-format).

## What does NOT work

- `curl` on any `www.drupal.org/...` **HTML** page (issue pages, project pages, `/project/issues/search/...`): returns a JS "Client Challenge" stub. Use api-d7 or WebSearch instead.
- api-d7 full-text search: `title=` is exact-match. Keyword discovery = WebSearch `site:drupal.org <keywords>`.
- drupal.org's own search UI via curl: challenge-blocked like all HTML.
