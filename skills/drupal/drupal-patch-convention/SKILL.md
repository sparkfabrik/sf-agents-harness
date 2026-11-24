---
name: drupal-patch-convention
description: 'Apply patches to Drupal core or contrib modules following the SparkFabrik convention — cweagans/composer-patches, locally vendored patch files, and the <NID>_CM<n>.patch / <NID>_MR<mr-iid>.patch naming scheme (<project>-<IID>_CM<note-id>.patch / <project>-<IID>_MR<mr-iid>.patch for issues that moved to GitLab work items). Use this skill whenever the user wants to apply, add, download, vendor, or remove a patch in a Drupal project: "apply this patch", "add this patch to composer", "patch this module", a drupal.org issue/comment/file URL, a git.drupalcode.org work item, or a merge request is given as a fix to install, or composer.patches.json needs editing. Also trigger when a patch fails to apply after a module update, or when reviewing whether existing patches follow the convention.'
---

# Drupal Patch Convention (SparkFabrik)

Patches are managed with [cweagans/composer-patches](https://github.com/cweagans/composer-patches) and stored **locally in the repo**, never referenced by remote URL. Remote patch files can change or disappear (drupal.org file attachments are mutable, MR diffs move as the branch grows); a vendored copy is reproducible and reviewable in the MR that introduces it.

## Prerequisites (verify, don't assume)

1. `cweagans/composer-patches` present in the project's `composer.json` (`require` or `require-dev`).
2. `composer.json` `extra` contains at least:
   ```json
   "extra": {
     "patches-file": "composer.patches.json"
   }
   ```
3. Patches folder exists: `src/drupal/addons/patches/` (adjust if the project layout differs — search for an existing `patches/` directory with `*.patch` files before creating a new one).

If a prerequisite is missing, set it up as part of the task and list every `composer.json` change prominently in the final report so the user can review or revert it:

- Add `"cweagans/composer-patches": "^1.7"` to `require`.
- Add `"patches-file": "composer.patches.json"` under `extra`.
- On Composer 2.2+, add `"cweagans/composer-patches": true` under `config.allow-plugins` (without it the plugin is silently ignored).
- Create the patches folder if absent.

The one thing you never do yourself is run `composer` — see "After adding".

## Where does the issue live?

Some projects moved their issue queue from drupal.org to GitLab work items on `git.drupalcode.org`. The naming depends on where the issue lives now:

| Signal                                                                                        | Issue lives on |
| --------------------------------------------------------------------------------------------- | -------------- |
| `www.drupal.org/project/<project>/issues/<NID>` or `www.drupal.org/node/<NID>`, not moved     | drupal.org     |
| `git.drupalcode.org/project/<project>/-/work_items/<IID>` (or `/-/issues/<IID>`)              | GitLab         |
| A shorthand ref such as `<project>#<IID>`                                                     | GitLab         |
| `drupalorg issue:show <NID>` reports `Issue <NID> moved to a GitLab work item`                | GitLab         |
| `https://www.drupal.org/api-d7/node/<NID>.json` has no `type` and returns a `new_url` instead | GitLab         |

Check a drupal.org link before naming the patch: an old link can point to an issue that has since moved. Use the `new_url` target (project and IID), not the old link.

A work item IID is only unique inside its project. Never resolve a bare number through drupal.org: the same number can be an unrelated drupal.org node or another project's work item. Always carry the project with the IID.

## Resolving issue and MR data

When the `drupalorg` CLI ([mglaman/drupalorg-cli](https://github.com/mglaman/drupalorg-cli)) is installed (`command -v drupalorg`), use it to resolve issue and MR data. `<ref>` is a drupal.org NID, a `<project>#<IID>` shorthand, or a work item URL:

- `drupalorg issue:show <ref> --format=llm`: issue title, project, and status. It follows drupal.org issues that moved to work items.
- `drupalorg mr:diff '<project-path>!<mr-iid>' --format=llm`: the MR diff, to check that it is the fix you expect. Quote the `!` in zsh.

Without the CLI, use the api-d7 and git.drupalcode.org calls in this skill (`sjust drupal-org-cli install` on macOS or `ajust drupal-org-cli install` on Linux installs it; it needs PHP 8.1 or newer). Either way, vendor the patch file with the commands in "Download commands".

For a GitLab work item, these calls work without a token unless marked:

```bash
GL="https://git.drupalcode.org/api/v4/projects/project%2F<project>"
curl -s "$GL/issues/<IID>"                          # .title for the composer key, .state, .labels, .web_url
curl -s "$GL/merge_requests/<mr-iid>/closes_issues" # confirms the MR closes the work item: match the returned "iid" against the work item's <IID>
curl -s "$GL/issues/<IID>/related_merge_requests"   # MRs linked to the work item, including ones that only mention it
curl -s "$GL/issues/<IID>/notes"                    # needs a GitLab token (401 without one)
```

`related_merge_requests` lists every MR that mentions the work item, so it does not prove that an MR is the fix; `closes_issues` does. Without a token, read note IDs through GraphQL instead of the notes endpoint. Keep `first: 50`: larger queries exceed the anonymous complexity limit. If the note is not among the first 50 discussions, ask the user for the note link.

```bash
curl -s -H 'Content-Type: application/json' https://git.drupalcode.org/api/graphql \
  -d '{"query":"{ project(fullPath: \"project/<project>\") { workItems(iids: [\"<IID>\"]) { nodes { widgets { ... on WorkItemWidgetNotes { discussions(first: 50) { nodes { notes { nodes { id url body } } } } } } } } } }"}'
# → note url ends in #note_<note-id>; id is gid://gitlab/Note/<note-id>
```

## Finding the issue from an MR link

The filename and the composer key need the issue, so an MR link alone is not enough. Look it up from the MR metadata:

- **CLI**: `drupalorg mr:show 'project/<project>!<mr-iid>' --format=json` prints `source_branch` and `closes_issues`.
- **Without the CLI** (no token needed): `curl -s "https://git.drupalcode.org/api/v4/projects/project%2F<project>/merge_requests/<mr-iid>"` returns `source_branch` and `source_project_id`.

Then, in this order:

1. **GitLab work item project**: `closes_issues` (`.../merge_requests/<mr-iid>/closes_issues`) lists the work item the MR closes; use its `iid` as `<IID>`.
2. **Issue-fork branch**: drupal.org issue-fork branches usually start with `<NID>-` (`3636212-php-8.5-using`).
3. **Issue-fork project**: when the branch does not carry the number (paragraphs !270 comes from branch `8.x-1.x`), read the source project: `curl -s "https://git.drupalcode.org/api/v4/projects/<source_project_id>"` returns `path_with_namespace` `issue/<project>-<NID>` (`issue/paragraphs-3107684`).

An MR title such as `Issue #<NID>: ...` only corroborates; titles are free text. If the signals are missing or disagree, ask the user which issue the MR belongs to. Never guess the number. Then check where that issue lives (see "Where does the issue live?") before naming the patch.

## Patch file naming

No `#` in any filename; the `#` appears only in the `composer.patches.json` key.

**Issue on drupal.org** — `<NID>_CM<n>.patch` or `<NID>_MR<mr-iid>.patch`:

- `<NID>`: issue node id (in the issue URL: `.../issues/1234567` → `1234567`)
- `CM<n>`: patch attached to comment number `<n>`. The comment number is the comment's position in the issue's full comment list, counted from 1 in creation order, System Message comments included. Fetch every page of `https://www.drupal.org/api-d7/comment.json?node=<NID>&sort=created&direction=ASC` (50 per page; follow `next` until it is null) before counting. The attached file's `timestamp` (from `api-d7/file/<fid>.json`) equals the `created` value of the comment that posted it. Do not take the number from `drupalorg issue:show --with-comments`: its `<number>` skips System Message comments.
- `MR<mr-iid>`: patch is a merge request; `<mr-iid>` is the merge request iid (the number after `/-/merge_requests/`)

Examples: `1234567_CM13.patch`, `3529537_MR57.patch`

**Issue on GitLab (work item)** — `<project>-<IID>_CM<note-id>.patch` or `<project>-<IID>_MR<mr-iid>.patch`:

- `<project>`: project machine name (`ai_context` in `git.drupalcode.org/project/ai_context/...`)
- `<IID>`: work item IID (the number after `/-/work_items/`)
- `CM<note-id>`: patch attached to a note; `<note-id>` is the GitLab note ID. Get it from a `#note_<note-id>` link, from `drupalorg issue:show <project>#<IID> --with-comments --format=json` (`comments[].id`, needs a GitLab token), or from the GraphQL call in "Resolving issue and MR data". Notes migrated from drupal.org comments link the original `www.drupal.org/files/issues/...` file: download it from there, and still name it with the note ID (not the old comment number).
- `MR<mr-iid>`: patch is a merge request; `<mr-iid>` is the merge request iid, not the work item `<IID>`

Example: `ai_context-3586692_MR380.patch`

**Self-authored** — `<issue-tracker ID>.patch` where the ID comes from the project's own tracker (GitLab/Jira/GitHub issue number).

## Download commands

```bash
# drupal.org comment attachment (URL resolved via api-d7 file/<fid>.json)
curl -s -o "src/drupal/addons/patches/<NID>_CM<n>.patch" "https://www.drupal.org/files/issues/<file>.patch"

# Merge request for a drupal.org issue
curl -s -o "src/drupal/addons/patches/<NID>_MR<mr-iid>.patch" "https://git.drupalcode.org/project/<project>/-/merge_requests/<mr-iid>.diff"

# Merge request for a GitLab work item
curl -s -o "src/drupal/addons/patches/<project>-<IID>_MR<mr-iid>.patch" "https://git.drupalcode.org/project/<project>/-/merge_requests/<mr-iid>.diff"

# GitLab work item note upload: the note links /uploads/<hash>/<file>.
# Prefix it with the numeric project id (GET /api/v4/projects/project%2F<project> → .id);
# the /project/<project>/uploads/... form returns 404.
curl -s -o "src/drupal/addons/patches/<project>-<IID>_CM<note-id>.patch" "https://git.drupalcode.org/-/project/<project-id>/uploads/<hash>/<file>.patch"

# GitLab work item note migrated from a drupal.org comment: the note links the drupal.org file
curl -s -o "src/drupal/addons/patches/<project>-<IID>_CM<note-id>.patch" "https://www.drupal.org/files/issues/<file>.patch"
```

After downloading, sanity-check the file: it must start with diff headers (`diff --git`, `---`/`+++` or `From <sha>`), not HTML — a curl that hit a challenge page or 404 still writes a file.

## composer.patches.json entry

File sits at repo root, same level as the top-level `composer.json`. All entries live under a top-level `patches` object; cweagans/composer-patches ignores a patches file without it.

```json
{
  "patches": {
    "drupal/<module>": {
      "#<NID>: <d.o issue title>": "src/drupal/addons/patches/<NID>_MR<mr-iid>.patch",
      "<project>#<IID>: <work item title>": "src/drupal/addons/patches/<project>-<IID>_CM<note-id>.patch"
    },
    "drupal/core": {
      "#<NID>: <issue title>": "src/drupal/addons/patches/<NID>_CM<n>.patch"
    }
  }
}
```

The description key is the issue reference and title only, no `CM`/`MR` suffix (that detail lives in the filename): `#<NID>: <issue title>` for drupal.org issues, `<project>#<IID>: <title>` for GitLab work items. The title makes `composer install` output self-explanatory; the key stays stable if the patch is later re-vendored from a different comment or MR of the same issue.

## After adding

Applying requires a composer operation (`composer install`/`update` re-applies patches). In SparkFabrik Drupal projects composer runs inside the container and dependency-modifying commands need user confirmation — hand the final `composer` step to the user unless they already approved it.

## Removing a patch

Remove the entry from `composer.patches.json`, delete the file from the patches folder, and hand the re-install composer step to the user. Typical reason: the fix landed in a release — verify the installed version actually contains it before removing.

## Finding the right patch

This skill covers _applying_ a patch you already have. If the patch still needs to be found — "is there a known issue for X", reading a drupal.org issue queue, comparing candidate fixes — research and choose the fix first, then apply the chosen patch with this convention.
