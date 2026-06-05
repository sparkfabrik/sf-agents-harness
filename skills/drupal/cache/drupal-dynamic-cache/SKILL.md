---
name: drupal-dynamic-cache
description: Dynamic Page Cache and BigPipe module behavior in Drupal. Use when asked about authenticated user caching, auto-placeholdering, lazy builders, BigPipe streaming, X-Drupal-Dynamic-Cache header, or why content shows UNCACHEABLE status. Covers interaction between caching layers.
---

# Dynamic Page Cache & BigPipe

These modules cache pages for authenticated users while handling personalized content via placeholders.

## When to Use

- Improving performance for logged-in users
- Debugging UNCACHEABLE responses
- Implementing personalized content that doesn't break caching
- Understanding BigPipe streaming behavior

## How Dynamic Page Cache Works

```
Request → Check cache
├── HIT: Serve cached structure → Replace placeholders → Response
└── MISS: Render page → Auto-placeholder dynamic parts → Cache → Response
```

## Response Headers

| Header                   | Values        | Meaning                  |
| ------------------------ | ------------- | ------------------------ |
| `X-Drupal-Dynamic-Cache` | `HIT`         | Served from cache        |
|                          | `MISS`        | Rendered and cached      |
|                          | `UNCACHEABLE` | Cannot cache (max-age:0) |

## Auto-Placeholder Conditions

Content is automatically placeholdered when:

- `max-age: 0`
- Cache context `user` or `session`
- `#create_placeholder` is TRUE

## Examples

### Example 1: Check Dynamic Cache Status

**Input:** "How do I know if Dynamic Page Cache is working?"

**Output:**

```bash
# Check response header
curl -sI -H "Cookie: SESS123=abc" https://site.com/ | grep X-Drupal-Dynamic-Cache

# Expected results:
# X-Drupal-Dynamic-Cache: HIT    → Working, served from cache
# X-Drupal-Dynamic-Cache: MISS   → First request, now cached
# X-Drupal-Dynamic-Cache: UNCACHEABLE → Problem! Something has max-age:0
```

### Example 2: Debug UNCACHEABLE Response

**Input:** "My page shows UNCACHEABLE, how do I fix it?"

**Output:**

```php
// Enable debug headers to see what's wrong
// settings.local.php
$settings['http.response.debug_cacheability_headers'] = TRUE;

// Check headers:
// X-Drupal-Cache-Max-Age: 0  → Something set max-age:0

// Common culprits:
// 1. Block with max-age:0
// 2. Form without lazy builder
// 3. Custom module not setting cache metadata

// Find the source with Xdebug breakpoint:
// File: Cache.php, Method: mergeMaxAges(), Condition: $a === 0 || $b === 0
```

### Example 3: Lazy Builder for User Content

**Input:** "I need to show user-specific data without breaking cache"

**Output:**

```php
// DON'T do this - breaks page caching:
$build['greeting'] = [
  '#markup' => 'Hello ' . $user->getDisplayName(),
  '#cache' => ['contexts' => ['user']], // Page becomes per-user!
];

// DO this - use lazy builder:
$build['greeting'] = [
  '#lazy_builder' => ['my_module.lazy:userGreeting', [$user->id()]],
  '#create_placeholder' => TRUE,
];
```

```php
// LazyBuilders service
class LazyBuilders implements TrustedCallbackInterface {

  public static function trustedCallbacks() {
    return ['userGreeting'];
  }

  public function userGreeting(int $uid): array {
    $user = User::load($uid);
    return [
      '#markup' => 'Hello ' . $user->getDisplayName(),
      '#cache' => [
        'contexts' => ['user'],
        'tags' => ['user:' . $uid],
      ],
    ];
  }
}
```

### Example 4: BigPipe Streaming

**Input:** "How does BigPipe work with placeholders?"

**Output:**

```html
<!-- Initial HTML sent immediately: -->
<div
  data-big-pipe-placeholder-id="callback=my_module.lazy%3AuserGreeting&args[0]=5"
>
  <span class="placeholder">Loading...</span>
</div>

<!-- Later, streamed via script tag: -->
<script type="application/vnd.drupal-ajax">
  [{"command":"insert",
    "selector":"[data-big-pipe-placeholder-id='callback=my_module.lazy%3AuserGreeting&args[0]=5']",
    "data":"Hello John!"}]
</script>

<!-- JavaScript replaces placeholder content automatically -->
```

### Example 5: Force Placeholder Creation

**Input:** "I want to placeholder content even without user context"

**Output:**

```php
$build['dynamic'] = [
  '#lazy_builder' => ['my_module.lazy:dynamicContent', []],
  '#create_placeholder' => TRUE, // Force placeholder regardless of contexts
];
```

### Example 6: Configure Auto-Placeholder Conditions

**Input:** "How do I customize what gets auto-placeholdered?"

**Output:**

```yaml
# services.yml
parameters:
  renderer.config:
    auto_placeholder_conditions:
      max-age: 0
      contexts:
        - "session"
        - "user"
        - "my_custom_context" # Add custom context
      tags: [] # Tags that trigger placeholder (usually empty)
```

### Example 7: BigPipe Requirements

**Input:** "BigPipe isn't working, what could be wrong?"

**Output:**

```yaml
# Check server configuration:

# Nginx - disable buffering (auto-handled via X-Accel-Buffering header)
location ~ \.php$ {
  # BigPipe sends: X-Accel-Buffering: no
  # Nginx respects this automatically
}

# Apache - works by default

# Common issues:
# 1. Output buffering in PHP - check ob_start() calls
# 2. Reverse proxy buffering - configure Varnish/CDN
# 3. JavaScript disabled - falls back to non-streaming
```

```bash
# Verify BigPipe is enabled
drush pm:list | grep big_pipe
```

### Example 8: Anonymous vs Authenticated Caching

**Input:** "Explain the caching difference between anonymous and logged-in users"

**Output:**

```
Anonymous User:
┌─────────────────────────────────────────┐
│ Page Cache → HIT → Full page served     │
│ (Dynamic Page Cache skipped)            │
│ No placeholders, no BigPipe             │
└─────────────────────────────────────────┘

Authenticated User:
┌─────────────────────────────────────────┐
│ Page Cache → SKIP (has session cookie)  │
│ Dynamic Page Cache → HIT/MISS           │
│ Placeholders replaced via BigPipe       │
└─────────────────────────────────────────┘
```

```php
// Check with curl:
// Anonymous
curl -sI https://site.com/ | grep X-Drupal
// X-Drupal-Cache: HIT

// Authenticated (with session cookie)
curl -sI -H "Cookie: SESSabc=xyz" https://site.com/ | grep X-Drupal
// X-Drupal-Dynamic-Cache: HIT
```

## Common Mistakes

| Mistake                        | Impact                   | Solution                         |
| ------------------------------ | ------------------------ | -------------------------------- |
| max-age:0 without lazy builder | Page UNCACHEABLE         | Use `#lazy_builder`              |
| `user` context on blocks       | Per-user cache entries   | Use `user.roles` or lazy builder |
| Disabling Dynamic Page Cache   | Slow authenticated pages | Fix underlying max-age issues    |
| Object args to lazy builder    | Runtime error            | Use scalar values only           |

## Debugging Checklist

```bash
# 1. Check Dynamic Cache status
curl -sI -H "Cookie: SESS=x" https://site.com/ | grep X-Drupal-Dynamic-Cache

# 2. Enable debug headers
# settings.local.php: $settings['http.response.debug_cacheability_headers'] = TRUE;

# 3. Check max-age
curl -sI https://site.com/ | grep X-Drupal-Cache-Max-Age

# 4. Verify BigPipe module
drush pm:list | grep big_pipe
```
