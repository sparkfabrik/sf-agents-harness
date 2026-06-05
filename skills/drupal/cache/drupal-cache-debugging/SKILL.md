---
name: drupal-cache-debugging
description: Drupal cache debugging techniques and troubleshooting workflows. Use when asked about X-Drupal-Cache headers interpretation, finding max-age 0 sources, WebProfiler usage, cache hit/miss analysis, stale content debugging, or performance profiling cache-related issues.
---

# Drupal Cache Debugging

Systematic approaches to identify and resolve caching issues.

## When to Use

- Pages not caching for anonymous users
- X-Drupal-Dynamic-Cache shows UNCACHEABLE
- Content is stale after edits
- Need to find source of max-age:0
- Performance profiling cache effectiveness

## Debug Headers Setup

```php
// settings.local.php
$settings['http.response.debug_cacheability_headers'] = TRUE;
```

**Warning:** Disable in production - headers can exceed 16KB.

## Headers Reference

| Header                    | Values                   | Meaning                |
| ------------------------- | ------------------------ | ---------------------- |
| `X-Drupal-Cache`          | HIT/MISS                 | Page Cache (anonymous) |
| `X-Drupal-Dynamic-Cache`  | HIT/MISS/UNCACHEABLE     | Dynamic Page Cache     |
| `X-Drupal-Cache-Tags`     | Space-separated tags     | All cache tags         |
| `X-Drupal-Cache-Contexts` | Space-separated contexts | Applied contexts       |
| `X-Drupal-Cache-Max-Age`  | Seconds or -1            | Effective max-age      |

## Examples

### Example 1: Quick Health Check

**Input:** "How do I quickly check if caching is working?"

**Output:**

```bash
# Anonymous user - should hit Page Cache
curl -sI https://site.com/ | grep -iE 'x-drupal|cache-control'

# Expected output:
# X-Drupal-Cache: HIT
# Cache-Control: max-age=3600, public

# Authenticated user - should hit Dynamic Cache
curl -sI -H "Cookie: SESSabc=xyz" https://site.com/ | grep X-Drupal-Dynamic-Cache

# Expected output:
# X-Drupal-Dynamic-Cache: HIT
```

### Example 2: Debug Page Not Caching (Anonymous)

**Input:** "Anonymous pages always show X-Drupal-Cache: MISS"

**Output:**

```bash
# Step 1: Check for session cookies being set
curl -sI https://site.com/ | grep -i set-cookie
# If you see SESS* or SSESS* → Something creates session for anonymous

# Step 2: Check if Page Cache module is enabled
drush pm:list | grep page_cache

# Step 3: Search for kill switch usage
grep -r "page_cache_kill_switch" web/modules/custom/

# Step 4: Check for session-creating code
grep -r "getSession\|session_start\|\$_SESSION" web/modules/custom/
```

### Example 3: Debug UNCACHEABLE Response

**Input:** "X-Drupal-Dynamic-Cache shows UNCACHEABLE, how do I fix it?"

**Output:**

```bash
# Step 1: Enable debug headers
# settings.local.php: $settings['http.response.debug_cacheability_headers'] = TRUE;

# Step 2: Check max-age
curl -sI https://site.com/ | grep X-Drupal-Cache-Max-Age
# If 0 → Something set max-age:0

# Step 3: Find the source with Xdebug
# Set conditional breakpoint in core/lib/Drupal/Core/Cache/Cache.php
# Method: mergeMaxAges()
# Condition: $a === 0 || $b === 0
# Check stack trace when it hits
```

### Example 4: Debug Stale Content After Edit

**Input:** "I edited a node but old content still shows"

**Output:**

```bash
# Step 1: Clear caches and verify still stale
drush cr
curl -sI https://site.com/node/1 | grep X-Drupal-Cache
# If still HIT with old content → Tags not invalidating

# Step 2: Check cache tags on response
curl -sI https://site.com/node/1 | grep X-Drupal-Cache-Tags
# Should include: node:1

# Step 3: Manually invalidate and test
drush cache-tag-invalidate node:1
curl https://site.com/node/1 | grep "expected new content"

# Step 4: If using Varnish/CDN, check purge queue
drush p:queue-stats
```

### Example 5: Find max-age:0 Source with Temporary Logging

**Input:** "I can't use Xdebug, how else can I find max-age:0?"

**Output:**

```php
// Temporarily modify core/lib/Drupal/Core/Cache/Cache.php
// Add to mergeMaxAges() method:

public static function mergeMaxAges($a, $b) {
  // TEMPORARY DEBUG - REMOVE AFTER FINDING ISSUE
  if ($a === 0 || $b === 0) {
    $trace = debug_backtrace(DEBUG_BACKTRACE_IGNORE_ARGS, 10);
    $simplified = array_map(function($t) {
      return ($t['class'] ?? '') . '::' . ($t['function'] ?? '') . ' in ' . ($t['file'] ?? '');
    }, $trace);
    \Drupal::logger('cache_debug')->warning('max-age:0 merge: @trace', [
      '@trace' => implode("\n", $simplified),
    ]);
  }
  // END TEMPORARY DEBUG

  return min($a, $b);
}

// Then check logs:
// drush watchdog:show --type=cache_debug
```

### Example 6: Enable Render Debug Comments

**Input:** "How do I see cache info per render element in HTML?"

**Output:**

```yaml
# development.services.yml
parameters:
  twig.config:
    debug: true
  renderer.config:
    debug: true
```

```html
<!-- HTML output will include: -->
<!-- THEME DEBUG -->
<!-- THEME HOOK: 'node' -->
<!-- FILE NAME SUGGESTIONS: ... -->
<!-- CACHE TAGS: node:1 node_view -->
<!-- CACHE CONTEXTS: user.permissions languages -->
<!-- CACHE MAX-AGE: -1 -->
```

### Example 7: WebProfiler Analysis

**Input:** "How do I use WebProfiler for cache debugging?"

**Output:**

```bash
# Install Devel and WebProfiler
composer require drupal/devel
drush en devel webprofiler

# Access the profiler toolbar at bottom of page (admin users)
# Click "Cache" panel to see:
# - Cache hit/miss counts per bin
# - All collected cache tags
# - Applied cache contexts
# - Timeline of cache operations
```

### Example 8: Database Cache Inspection

**Input:** "How do I inspect cache entries directly in database?"

**Output:**

```sql
-- Check render cache entries for a node
SELECT cid, expire, tags
FROM cache_render
WHERE cid LIKE '%node%'
LIMIT 10;

-- Find entries with specific tag
SELECT cid, created, expire
FROM cache_render
WHERE tags LIKE '%node:123%';

-- Count entries per cache bin
SELECT 'cache_render' as bin, COUNT(*) as entries FROM cache_render
UNION ALL
SELECT 'cache_page', COUNT(*) FROM cache_page
UNION ALL
SELECT 'cache_dynamic_page_cache', COUNT(*) FROM cache_dynamic_page_cache;
```

### Example 9: Drush Cache Commands

**Input:** "What drush commands help with cache debugging?"

**Output:**

```bash
# Full cache rebuild
drush cr

# Clear specific bin
drush cache:clear render
drush cache:clear page
drush cache:clear dynamic_page_cache
drush cache:clear discovery

# Invalidate specific tag
drush cache-tag-invalidate node:1
drush cache-tag-invalidate "config:system.site"

# Get cache item programmatically
drush php:eval "print_r(\Drupal::cache('render')->get('entity_view:node:1:full'));"

# List all cache bins
drush php:eval "print_r(array_keys(\Drupal::getContainer()->getParameter('cache_bins')));"
```

## Debugging Decision Tree

```
Page not caching?
├── Anonymous user?
│   ├── X-Drupal-Cache: MISS always?
│   │   └── Check for session cookies, kill switch
│   └── X-Drupal-Cache: HIT but stale?
│       └── Check cache tags, invalidation
└── Authenticated user?
    ├── X-Drupal-Dynamic-Cache: UNCACHEABLE?
    │   └── Find max-age:0 source
    ├── X-Drupal-Dynamic-Cache: MISS always?
    │   └── Check if module enabled, cache bin working
    └── Dynamic Cache working but slow?
        └── Check for missing lazy builders on personalized content
```

## Common Issues Quick Reference

| Symptom                  | Likely Cause     | First Check                    |
| ------------------------ | ---------------- | ------------------------------ |
| Always MISS (anonymous)  | Session created  | `curl -I` for Set-Cookie       |
| Always UNCACHEABLE       | max-age:0        | X-Drupal-Cache-Max-Age header  |
| Stale after edit         | Missing tags     | X-Drupal-Cache-Tags header     |
| Per-user cache explosion | `user` context   | X-Drupal-Cache-Contexts header |
| BigPipe not streaming    | Server buffering | Check Nginx/Apache config      |
