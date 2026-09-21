---
name: drupal-patch-convention
description: 'Apply patches to Drupal core or contrib modules following the SparkFabrik convention — cweagans/composer-patches, locally vendored patch files, and the <NID>_<CM|MR><id>.patch naming scheme. Use this skill whenever the user wants to apply, add, download, vendor, or remove a patch in a Drupal project: "apply this patch", "add this patch to composer", "patch this module", a drupal.org issue/comment/file URL or a git.drupalcode.org merge request is given as a fix to install, or composer.patches.json needs editing. Also trigger when a patch fails to apply after a module update, or when reviewing whether existing patches follow the convention.'
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

## Patch file naming

**From drupal.org** — `<NID>_<CM|MR><id>.patch` (no `#` in the filename; the `#` appears only in the `composer.patches.json` key):

- `<NID>`: issue node id (in the issue URL: `.../issues/1234567` → `1234567`)
- `CM<id>`: patch attached to comment number `<id>` — the comment number is its position in the chronological comment list from `https://www.drupal.org/api-d7/comment.json?node=<NID>` (drupal.org HTML pages are curl-blocked; the api-d7 JSON API is not)
- `MR<id>`: patch is a merge request; `<id>` is the MR iid

Examples: `1234567_CM13.patch`, `3529537_MR57.patch`

**Self-authored** — `<issue-tracker ID>.patch` where the ID comes from the project's own tracker (GitLab/Jira/GitHub issue number).

## Download commands

```bash
# From an issue comment attachment (URL resolved via api-d7 file/<fid>.json)
curl -s -o "src/drupal/addons/patches/<NID>_CM<n>.patch" "https://www.drupal.org/files/issues/<file>.patch"

# From a merge request
curl -s -o "src/drupal/addons/patches/<NID>_MR<iid>.patch" "https://git.drupalcode.org/project/<name>/-/merge_requests/<iid>.diff"
```

After downloading, sanity-check the file: it must start with diff headers (`diff --git`, `---`/`+++` or `From <sha>`), not HTML — a curl that hit a challenge page or 404 still writes a file.

## composer.patches.json entry

File sits at repo root, same level as the top-level `composer.json`:

```json
{
  "drupal/<module>": {
    "#<NID>: <d.o issue title>": "src/drupal/addons/patches/<NID>_<CM|MR><id>.patch"
  },
  "drupal/core": {
    "#<NID>: <issue title>": "src/drupal/addons/patches/<NID>_<CM|MR><id>.patch"
  }
}
```

The description key is `#<NID>: <issue title>` — issue number and title only, no `CM`/`MR` suffix (that detail lives in the filename). The title makes `composer install` output self-explanatory; the key stays stable if the patch is later re-vendored from a different comment or MR of the same issue.

## After adding

Applying requires a composer operation (`composer install`/`update` re-applies patches). In SparkFabrik Drupal projects composer runs inside the container and dependency-modifying commands need user confirmation — hand the final `composer` step to the user unless they already approved it.

## Removing a patch

Remove the entry from `composer.patches.json`, delete the file from the patches folder, and hand the re-install composer step to the user. Typical reason: the fix landed in a release — verify the installed version actually contains it before removing.

## Finding the right patch

This skill covers _applying_ a patch you already have. If the patch still needs to be found — "is there a known issue for X", reading a drupal.org issue queue, comparing candidate fixes — use the `drupal-solution-research` skill first; it ends by handing the chosen patch to this convention.
