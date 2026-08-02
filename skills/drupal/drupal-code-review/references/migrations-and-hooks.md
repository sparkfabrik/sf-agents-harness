# Migrations, update & deploy hooks

Detail for checklist items 10 and 11. Update/deploy hooks and migrations run against real
production data, so the team reviews them for safety, naming, and progress reporting.

## Batch large data changes

- A `hook_update_N` / `hook_post_update_NAME` that loops over many entities must use the
  Batch API (the `$sandbox` protocol), not a single synchronous loop, or it hits the PHP
  timeout on real datasets.
- Report progress with `$sandbox['message']` so the operator sees what is happening.

> Content updates are better handled through Batch.
> You can use `$sandbox['message']` to print out batch information.

## Name update/deploy hooks descriptively

- Give the update a name that says what it does, following the Drupal convention:
  `mymodule_post_update_0001_publish_migrated_content`.
- Follow the correct `hook_update_N` numbering for the Drupal core version in use.

> Give the content update a descriptive name, e.g. `mymodule_post_update_0001_publish_content`.
> Use numbering that follows the Drupal convention for update hooks (this is D11).

## Guard writes and translations

- Guard entity writes with `isNew()`: initialize data only on new entities, so a redeploy
  does not overwrite values an editor already configured.
- Before touching a translation, check `hasTranslation($langcode)` to avoid failures and
  useless error reports; log skips rather than crashing.

> Before `setData`, check `isNew` and only initialize when new.
> Add `if ($node->hasTranslation($language->getId()))` before, and log when skipping.

## Prefer the migration system's own tools

- Migrations have built-in logging: use `migrate:messages` (drush) rather than a custom
  logging implementation.
- Do not reload a taxonomy term and re-query when the referenced entities are already
  available in the source row.
- Check field assignment and language handling in the migration definition; a wrong
  language or field mapping is a common migration bug.

> Migrations have their own logging (`migrate:messages` drush command) — prefer it over a custom implementation.

## Test against production data

- Post-update and deploy hooks that transform content should be tested against a copy of
  the production database before merge, not only on a clean local.
