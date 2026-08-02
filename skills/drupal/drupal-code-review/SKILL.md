---
name: drupal-code-review
description: 'Review a Drupal merge request or diff using a frequency-ranked checklist mined from 900+ real human code-review comments across production Drupal projects. Covers dependency injection vs static \Drupal calls, config/YAML dependencies, cache tags and render metadata, entity access checks, Twig/SDC theming, i18n with t() and msgctxt, update and post_update hooks, migrations, phpcs/phpstan nullable typing, composer patches, and team conventions (patch naming, secrets via CI variables). Use whenever reviewing, or asked to review, Drupal PHP/module/theme/twig/yml code, a Drupal MR or PR, or a .module/.install/.theme/.twig/.yml diff. Trigger on: "review Drupal", "Drupal MR review", "Drupal merge request", "revisione codice Drupal", "review this .module/.install/.theme", "Drupal code review", "check Drupal config yml", "Drupal cache tags", "dependency injection review".'
---

# Drupal code review

Review a Drupal change against the patterns experienced reviewers actually raise. The
checklist below is frequency-ranked from 906 real human review findings across
production Drupal projects (2020-2026). Items are **general Drupal 9/10/11 correctness**
unless the final section marks them as team conventions.

## How to use

Run this against a Drupal MR or diff. Walk the changed `.php`, `.module`, `.install`,
`.theme`, `.twig`, and `.yml` files and check each item. Report findings with file and
line, most impactful first. For the three deep areas (config, cache, migrations) the
one-line check here points to a `references/` file with the detail.

Scope note: report every finding, including low-confidence ones, with a severity you
assign. A reviewer or a later pass filters; your job here is coverage.

## Checklist

### 1. Naming & clarity (most frequent)

Names must be precise, correctly spelled, and consistent. Flag typos in class, method,
field, and variable names, misleading terms, and generic names that hide intent. Typos
in field or config-key names cause silent breakage, not just noise.

> non sarebbe più corretto Download**Ext**FileSearchController ?
> There's a small typo in the field name: `hightlight` -> `highlight`

### 2. Dependency injection & service usage

No `\Drupal::` static calls inside classes: inject the service through the constructor.
Use `create()` / `#[Autowire]` and constructor property promotion with `readonly`.
Remove injected services that are no longer used, and drop the matching entry from
`*.services.yml`.

> config manager not used in this class. let's drop it entirely.
> Ora che non iniettiamo più questa dipendenza, questa puoi toglierla

### 3. Config / YAML management

Keep config dependencies honest: add dependencies for modules the config actually uses,
and remove config for modules or fields no longer present. Stale or missing dependencies
break import or silently disable views and actions after deploy. See
[references/config-yaml.md](references/config-yaml.md).

> Capire come mai è stata rimossa la dipendenza a questo modulo visto che ne fa uso

### 4. phpcs / phpstan / coding standards

Use precise, nullable-aware return types: `?array` or `array|null` when a method can
return null, not a bare `array`. Accurate types make static analysis useful and force
callers to handle null.

> Qui ci può stare che venga restituito un null. Scriviamo comunque `?array`.

### 5. Twig / theming

Keep Twig and SDC templates declarative. Push derived values, string transforms, and
redundant checks into component properties or a preprocess hook, not inline template
logic. Logic in Twig duplicates preprocess and drifts from the parent's data.

> Questo non credo serva, possiamo usare la proprietà del titolo diretto
> Spostiamo la trasformazione della stringa esatta dal template del SDC al template Drupal

### 6. Error handling / exceptions

Guard null and missing values; wrap risky operations in try/catch. Do not assume an
entity, array key, or field always exists. Unhandled absence crashes or silently loses
data in production.

> Questo potrebbe essere null se uno dei `crumbs` non è un node.
> Mettiamo questo codice in un try catch, così da gestire eventuali errori.

### 7. Security / access / permissions

Do not derive access from `accessCheck(FALSE)` on an entity query without a written
justification. Bypassing access checks can leak entities the current user should not see
(group-restricted content), defeating Drupal permissions silently.

> non sono sicuro di questo `accessCheck` settato a `FALSE`. se il singolo componente ha un gruppo view diverso dal current user, tecnicamente non dovrebbe uscire tra i risultati, no?

### 8. Cache tags / render arrays / invalidation

Prefer `addCacheableDependency($object)` over hand-listing individual cache tags,
contexts, or max-age. Passing the whole object captures all three together, so cache
metadata stays complete as the source entity's dependencies change. See
[references/cache-and-render.md](references/cache-and-render.md).

> invece di aggiungere il singolo cache tag, aggiungiamo l'intera dipendenza dell'oggetto (che potrebbe portare con se anche contexts o max age custom.) `->addCacheableDependency(...)`

### 9. Translation / i18n

Wrap user-facing strings in `t()` or the `trans` filter, including strings returned by
helpers if not already translated. Use `msgctxt` to disambiguate duplicate source
strings in `.po` files.

> Please use the `t` filter on this string, so it can be translated.
> già esiste questa stringa a riga 450. Conviene aggiungerne una nuova ma con il context tipo: msgctxt "Articles for magazine"

### 10. Update / deploy hooks

Use the Batch API in `hook_update_N` / `hook_post_update_NAME` when touching large
content sets, and report progress with `$sandbox['message']`. Unbatched loops hit the
PHP timeout on real datasets. See [references/migrations-and-hooks.md](references/migrations-and-hooks.md).

> L'update dei contenuti meglio se gestito tramite Batch.
> i think you can use `$sandbox['message']` to printout batch information

### 11. Migrations

In deploy/install code, guard entity writes with `isNew()`: only initialize data on new
entities. Unconditional `setData()` clobbers values an editor already configured in
production.

> prima di invocare `setData` dobbiamo fare un check con `isNew`. solo se new, inizializziamo così.

### 12. Composer / patches

Before bumping a Drupal dev/test dependency, verify its transitive constraints are
satisfiable across every required package. Do not just regenerate the lock and hope; an
upgrade blocked upstream is a blocker to flag, not to patch around.

> drupal-extension ^6 is not installable: no valid solution exists until the driver ships a compatible release upstream.

## Team conventions

These are project/team-specific, separate from general Drupal correctness. Flag, do not
hard-fail. Adapt them to your own team; the examples below are one team's rules.

- **Patches follow a house naming pattern.** When adding a patch to a project, name it
  per the team convention, not an ad-hoc filename.
- **Secrets are never hardcoded.** Credentials and API keys are injected as CI variables
  and read as environment variables across environments; they are not committed to
  config or code.
- **Prefer backporting shared fixes to the base image or chart** over per-project
  one-offs when the logic belongs in shared infrastructure.

## Provenance

Distilled from 906 real human review findings across production Drupal projects
(2020-2026), tagged into 12 recurring themes and synthesized into the checklist above.
