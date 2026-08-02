# Config / YAML review

Detail for checklist item 3. The team reviews config YAML as carefully as code: a bad
`config/sync` export breaks import or silently changes behavior on the next deploy.

## Dependencies must match actual usage

- Add a config dependency for every module the config uses. A missing dependency breaks
  `drush config:import` or disables the view/action after deploy.
- Remove config that references a module or field no longer present. Stale config for a
  removed module fails import.
- When a dependency is removed in a diff, ask why: if the config still uses that module,
  the removal is a bug.

> Understand why the dependency on this module was removed when the config still uses it.

## Reuse existing config, do not duplicate

- Reuse a defined `core.date_format.*` instead of hardcoding a date format in PHP.
- Before adding a new image style, check whether an existing one fits; create a
  dedicated style only when the design genuinely needs it.
- Before adding a translation string, check the `.po` for an existing one; add a new
  entry with `msgctxt` context rather than a duplicate source string.

> Here we should use the date formatter `core.date_format.hour_minute.yml` for the format, not a hardcoded one.

## Form modes and display modes

- If a diff changes a `form_mode`, that form mode must be defined for every component
  that uses it, or rendering breaks.
- Entity form/view display config must stay consistent with the fields it references.

## Config drift on deploy

- Config changed through the UI that is not in `config_ignore` will be reverted by the
  next deploy. If a value is meant to be editor-managed, it belongs in `config_ignore`;
  otherwise the UI change is lost.

> If this config was changed from the UI and is not in config_ignore, the next deploy will overwrite it.

## Externalize tunables

- When calling an external service, set a default timeout and make it configurable
  rather than leaving it implicit.
