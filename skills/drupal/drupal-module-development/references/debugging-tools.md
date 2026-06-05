# Debugging Tools & Troubleshooting

## Table of Contents

1. [Logs](#logs)
2. [Core Debugging & Information Commands](#core-debugging--information-commands)
3. [Cache Debugging](#cache-debugging)
4. [Configuration Debugging](#configuration-debugging)
5. [Module/Theming Debugging](#moduletheming-debugging)
6. [Database & Entity Debugging](#database--entity-debugging)
7. [Development & Error Reproduction](#development--error-reproduction)
8. [Performance & Query Debugging](#performance--query-debugging)
9. [Performance Profiling](#performance-profiling)
10. [Troubleshooting Common Issues](#troubleshooting-common-issues)

---

## Logs

Logs are exported using the Monolog module to the standard output of the container. Monolog configuration is defined in `src/drupal/web/sites/default/pkg_drupal.services.yml`.
Drupal watchdog module IS NOT installed in this project.

Use `docker compose logs -f drupal-php` to view logs in real time.

## Core Debugging & Information Commands

| Command             | Purpose                                                                | Why it's useful for debugging                                                  |
| ------------------- | ---------------------------------------------------------------------- | ------------------------------------------------------------------------------ |
| `drush status`      | Shows Drupal root, site path, database connection, Drush version, etc. | Quickly verify that Drush is pointing to the correct site and DB is connected. |
| `drush core-status` | Same as above but more detailed in newer versions.                     |                                                                                |

## Cache Debugging

| Command                            | Purpose                                                                         |
| ---------------------------------- | ------------------------------------------------------------------------------- |
| `drush cache:rebuild` / `drush cr` | Rebuilds all caches (equivalent to "drush cc all" in D7).                       |
| `drush cache:get <bin>:<cid>`      | Retrieve a specific cache item (e.g., `drush cache:get config:core.extension`). |
| `drush cache:clear <bin>`          | Clear only one cache bin (render, config, discovery, etc.).                     |

## Configuration Debugging

| Command                                 | Purpose                                                                   |
| --------------------------------------- | ------------------------------------------------------------------------- |
| `drush config:get <name>`               | Show a single configuration value (e.g., `drush config:get system.site`). |
| `drush config:set <name> <key> <value>` | Temporarily change a config value without using the UI.                   |
| `drush config:export` / `drush cex`     | Export active config to sync directory.                                   |
| `drush config:import` / `drush cim`     | Import config -- very useful to test if config issues cause errors.       |
| `drush config:delete <name>`            | Remove a config object (helps when orphaned config causes fatal errors).  |

## Module/Theming Debugging

| Command                                                                                                                    | Purpose                                                        |
| -------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------- |
| `drush pm:list --type=module --status=enabled`                                                                             | List enabled modules.                                          |
| `drush pm:enable <module>` / `drush en <module>`                                                                           | Enable a module.                                               |
| `drush pm:uninstall <module>` / `drush puninstall <module>`                                                                | Fully uninstall a module (removes config and data).            |
| `drush pm:uninstall` without arguments: interactive mode is excellent for disabling suspected problematic modules quickly. |                                                                |
| `drush theme:debug` (Drupal 9.4+)                                                                                          | Lists all theme suggestions for a given route or render array. |

## Database & Entity Debugging

| Command                 | Purpose                                                                                                                                                            |
| ----------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `drush sql:connect`     | Outputs the CLI command to connect to the DB (useful for manual queries).                                                                                          |
| `drush sql:query`       | Run arbitrary SQL.                                                                                                                                                 |
| `drush entity:info`     | Show entity type definitions (useful when entity schema errors occur).                                                                                             |
| `drush php`             | Opens an interactive PHP shell with Drupal bootstrapped (like `drush php:eval`).                                                                                   |
| `drush php:eval "code"` | Execute arbitrary PHP code in Drupal context (great for quick debugging). Example: `drush php:eval "dpm(\Drupal::state()->get('system.cron_last'));"` (with Devel) |

## Development & Error Reproduction

| Command                                                                  | Purpose                                                                 |
| ------------------------------------------------------------------------ | ----------------------------------------------------------------------- |
| `drush php:eval "var_dump(function_exists('my_problematic_function'));"` | Quick test if a function exists or what it returns.                     |
| `drush state:edit` / `drush state:get/set/delete`                        | Inspect or override Drupal state values (often used by broken modules). |
| `drush variable:get/set/delete` (D7 only)                                | Legacy equivalent of state commands.                                    |
| `drush twig:debug`                                                       | Turn Twig debugging on/off and verify template suggestions.             |
| `drush eval` (alias of php:eval)                                         | Same as above.                                                          |

## Performance & Query Debugging

| Command                                                                     | Purpose                                                           |
| --------------------------------------------------------------------------- | ----------------------------------------------------------------- |
| `drush sql:query --db-prefix`                                               | See queries with table prefixes expanded (helps reading raw SQL). |
| Enable Devel + `drush kint` or `dpm()` in code: instant output in terminal. |                                                                   |

## Performance Profiling

```bash
# Performance analysis
drush cr                     # Rebuild caches
drush sql:query "EXPLAIN ANALYZE SELECT ..."  # Query analysis
drush site:status           # System status check

# Use Webprofiler module for detailed profiling
# Access at http://127.0.0.1:8888/admin/config/development/devel/webprofiler
```

## Troubleshooting Common Issues

### Performance Issues

```bash
# Identify slow queries
drush sql:query "SELECT * FROM watchdog WHERE type = 'php' ORDER BY wid DESC LIMIT 10"

# Check cache settings
drush config:get system.performance
```

### Module/Theme Development Issues

```bash
drush cr

# Service not found
drush config:get core.extension

# Twig template not loading
drush cr

# Cron issues
drush cron
drush watchdog:show --type=cron
```
