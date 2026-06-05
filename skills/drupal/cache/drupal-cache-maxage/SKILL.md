---
name: drupal-cache-maxage
description: Drupal cache max-age configuration and behavior. Use when asked about time-based cache expiration, Cache::PERMANENT, max-age 0 issues, why Page Cache ignores max-age, or when content appears stale despite time expiration. Critical for understanding caching layer differences.
---

# Drupal Cache Max-Age

Max-age defines time-based cache validity in seconds.

## When to Use

- Caching external API data with known refresh intervals
- Time-sensitive content (countdowns, live scores)
- Understanding why anonymous pages stay cached
- Debugging UNCACHEABLE responses

## Critical Behavior

**Page Cache ignores max-age** - Only uses tags for invalidation.
**Dynamic Page Cache respects max-age** - max-age:0 causes UNCACHEABLE.
**Max-age bubbles up** - Minimum value wins across render tree.

## Max-Age Values

| Value                   | Meaning                           |
| ----------------------- | --------------------------------- |
| `0`                     | Uncacheable - DANGER: bubbles up! |
| `Cache::PERMANENT` (-1) | Forever until tag invalidation    |
| `3600`                  | 1 hour                            |
| `86400`                 | 1 day                             |

## Examples

### Example 1: External API Data

**Input:** "I fetch weather data from an API, how do I cache it for 15 minutes?"

**Output:**

```php
$build = [
  '#markup' => $this->weatherService->getCurrentWeather(),
  '#cache' => [
    'max-age' => 900, // 15 minutes
    'tags' => ['weather:current'],
  ],
];
```

### Example 2: Cache Forever Until Invalidation

**Input:** "My content only changes when the entity is edited"

**Output:**

```php
use Drupal\Core\Cache\Cache;

$build = [
  '#markup' => $node->getTitle(),
  '#cache' => [
    'max-age' => Cache::PERMANENT, // -1, forever
    'tags' => $node->getCacheTags(), // Invalidates on node save
  ],
];
```

### Example 3: Time-Sensitive Countdown

**Input:** "I show a countdown to an event, how do I handle cache?"

**Output:**

```php
public function buildCountdown(): array {
  $event_time = strtotime('2024-12-31 23:59:59');
  $remaining = $event_time - time();

  return [
    '#markup' => $this->formatCountdown($remaining),
    '#cache' => [
      // Cache for 1 minute or until event, whichever is shorter
      'max-age' => $remaining > 0 ? min($remaining, 60) : 0,
    ],
  ];
}
```

### Example 4: max-age:0 Causes Page UNCACHEABLE

**Input:** "Why does X-Drupal-Dynamic-Cache show UNCACHEABLE?"

**Output:**

```php
// PROBLEM: This makes entire page uncacheable
$build['timestamp'] = [
  '#markup' => time(),
  '#cache' => ['max-age' => 0], // Bubbles up to page!
];

// SOLUTION: Use lazy builder to isolate uncacheable content
$build['timestamp'] = [
  '#lazy_builder' => ['my_module.lazy:renderTimestamp', []],
  '#create_placeholder' => TRUE,
];
```

### Example 5: Page Cache Ignores max-age

**Input:** "I set max-age to 300 but anonymous users still see old content after 5 minutes"

**Output:**

```php
// max-age:300 does NOT work for Page Cache!
// Page Cache only respects cache tags, not max-age

// Option 1: Use cache tags and invalidate when data changes
Cache::invalidateTags(['my_module:data']);

// Option 2: Disable Page Cache for this route
// In your_module.routing.yml:
my_module.dynamic_page:
  path: '/dynamic'
  defaults:
    _controller: '\Drupal\my_module\Controller::page'
  options:
    no_cache: TRUE

// Option 3: Kill Page Cache programmatically
\Drupal::service('page_cache_kill_switch')->trigger();
```

### Example 6: Finding max-age:0 Source

**Input:** "How do I find what's setting max-age to 0?"

**Output:**

```php
// Method 1: Xdebug conditional breakpoint
// File: core/lib/Drupal/Core/Cache/Cache.php
// Method: mergeMaxAges()
// Condition: $a === 0 || $b === 0

// Method 2: Temporary debug logging
// Add to Cache::mergeMaxAges() temporarily:
if ($a === 0 || $b === 0) {
  \Drupal::logger('cache_debug')->warning(
    'max-age:0 at: @trace',
    ['@trace' => json_encode(debug_backtrace(DEBUG_BACKTRACE_IGNORE_ARGS, 5))]
  );
}
```

### Example 7: Browser Cache-Control Headers

**Input:** "How do I control browser caching separately from Drupal cache?"

**Output:**

```php
// Site-wide: Admin > Config > Development > Performance
// Sets Cache-Control header for anonymous pages

// Per-response in controller:
use Symfony\Component\HttpFoundation\Response;

public function myPage(): Response {
  $build = ['#markup' => 'Content'];
  $html = \Drupal::service('renderer')->renderRoot($build);

  $response = new Response($html);
  $response->headers->set('Cache-Control', 'public, max-age=3600');

  return $response;
}
```

## Max-Age Bubbling Behavior

```php
// Parent: max-age 3600
$build = [
  '#markup' => 'Parent',
  '#cache' => ['max-age' => 3600],
];

// Child: max-age 0
$build['child'] = [
  '#markup' => 'Child',
  '#cache' => ['max-age' => 0],
];

// Result: entire $build has effective max-age: 0
// The minimum always wins!
```

## Common Mistakes

| Mistake                           | Impact                        | Solution                      |
| --------------------------------- | ----------------------------- | ----------------------------- |
| max-age:0 in render array         | Entire page uncacheable       | Use lazy builder              |
| Relying on max-age for Page Cache | Pages never expire            | Use cache tags + invalidation |
| Short max-age on stable content   | Unnecessary re-renders        | Use tags, set PERMANENT       |
| Forgetting bubbling               | Child max-age:0 breaks parent | Audit all render elements     |

## Debugging

```bash
# Check max-age header
curl -sI https://site.com/ | grep -i 'cache-control\|x-drupal-cache-max-age'

# Clear render cache and test
drush cache:clear render
curl -sI https://site.com/node/1
```
