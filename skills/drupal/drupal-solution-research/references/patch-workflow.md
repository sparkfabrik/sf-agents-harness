# Applying a patch — SparkFabrik convention

Patches are managed with [cweagans/composer-patches](https://github.com/cweagans/composer-patches) and stored **locally in the repo**, never referenced by remote URL (remote patch files can change or disappear; a vendored copy is reproducible).

## Prerequisites (verify, don't assume)

1. `cweagans/composer-patches` present in the project's `composer.json`.
2. `composer.json` `extra` contains at least:
   ```json
   "extra": {
     "patches-file": "composer.patches.json"
   }
   ```
3. Patches folder exists: `src/drupal/addons/patches/` (adjust if the project layout differs).

## Patch file naming

**From drupal.org** — `#<NID>_<CM|MR><id>.patch`:

- `<NID>`: issue node id (in the issue URL: `.../issues/1234567` → `1234567`)
- `CM<id>`: patch attached to comment number `<id>` (comment number = position in the chronological comment list from `comment.json?node=<NID>`)
- `MR<id>`: patch is a merge request; `<id>` is the MR iid

Examples: `#1234567_CM13.patch`, `#3529537_MR57.patch`

**Self-authored** — `#<issue-tracker ID>.patch` where the ID comes from the project's own tracker (GitLab/Jira/GitHub issue number).

## Download commands

```bash
# From an issue comment attachment (URL resolved via api-d7 file/<fid>.json)
curl -s -o "src/drupal/addons/patches/#<NID>_CM<n>.patch" "https://www.drupal.org/files/issues/<file>.patch"

# From a merge request
curl -s -o "src/drupal/addons/patches/#<NID>_MR<iid>.patch" "https://git.drupalcode.org/project/<name>/-/merge_requests/<iid>.diff"
```

## composer.patches.json entry

File sits at repo root, same level as the top-level `composer.json`:

```json
{
  "drupal/<module>": {
    "#<NID>_<CM|MR><id>: <d.o issue title>": "src/drupal/addons/patches/#<NID>_<CM|MR><id>.patch"
  },
  "drupal/core": {
    "#<tracker-id>: <issue title>": "src/drupal/addons/patches/#<tracker-id>.patch"
  }
}
```

The description key format is `#<ref>: <issue title>` — the title makes `composer install` output self-explanatory.

## After adding

Applying requires a composer operation (`composer install`/`update` re-applies patches). In SparkFabrik Drupal projects composer runs inside the container and dependency-modifying commands need user confirmation — hand the final `composer` step to the user unless they already approved it.
