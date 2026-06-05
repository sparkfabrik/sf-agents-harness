---
name: drupal-cache-contexts
description: Drupal cache contexts implementation guide. Use when asked about request-based cache variations, user.roles vs user context, URL contexts, language contexts, custom cache contexts, or cache context hierarchy. Helps prevent cache explosion from overly broad contexts.
---

# Drupal Cache Contexts

Cache contexts define request-dependent cache variations. Analogous to HTTP `Vary` header.

## When to Use

- Content varies by user role or permissions
- Content changes based on URL parameters
- Multi-language sites with localized content
- Theme-dependent rendering
- Preventing cache explosion from overly broad contexts

## Available Contexts

| Context                        | Variations           | Use Case                            |
| ------------------------------ | -------------------- | ----------------------------------- |
| `user`                         | Per-user (AVOID)     | Truly personalized content only     |
| `user.roles`                   | Per-role combination | Role-based visibility               |
| `user.permissions`             | Per-permission set   | Permission-based content            |
| `url.path`                     | Per-path             | Path-dependent content              |
| `url.query_args:key`           | Per-parameter        | Sort, filter, pagination            |
| `languages:language_interface` | Per-language         | Translated content                  |
| `theme`                        | Per-theme            | Theme-specific rendering            |
| `session`                      | Per-session          | Session data (triggers placeholder) |

## Context Hierarchy

```
user (AVOID - per-user cache explosion)
├── user.is_super_user (2 variations only)
├── user.roles (per role combination)
│   └── user.roles:editor (has specific role?)
└── user.permissions (per permission set)
```

**Rule:** Always use the most specific context possible.

## Examples

### Example 1: Role-Based Content

**Input:** "I show different content to editors vs anonymous users"

**Output:**

```php
$build = [
  '#markup' => $this->getRoleBasedContent(),
  '#cache' => [
    'contexts' => ['user.roles'],
  ],
];
```

### Example 2: Per-User Content (Use Sparingly)

**Input:** "I need to show the user's own profile info"

**Output:**

```php
// WARNING: Creates cache entry per user - use lazy_builder instead
$build = [
  '#markup' => $user->getDisplayName(),
  '#cache' => [
    'contexts' => ['user'], // High cardinality!
  ],
];

// BETTER: Use lazy builder for per-user content
$build = [
  '#lazy_builder' => ['my_module.lazy:userName', []],
  '#create_placeholder' => TRUE,
];
```

### Example 3: URL Query Parameters

**Input:** "My listing supports ?sort=date and ?sort=title parameters"

**Output:**

```php
$sort = \Drupal::request()->query->get('sort', 'date');

$build = [
  '#theme' => 'item_list',
  '#items' => $this->getSortedItems($sort),
  '#cache' => [
    'contexts' => ['url.query_args:sort'],
  ],
];
```

### Example 4: Language-Dependent Content

**Input:** "I render translated labels in my block"

**Output:**

```php
$build = [
  '#markup' => $this->t('Welcome'),
  '#cache' => [
    'contexts' => ['languages:language_interface'],
  ],
];
```

### Example 5: Combined Contexts

**Input:** "Content varies by role AND language"

**Output:**

```php
$build = [
  '#markup' => $this->getLocalizedRoleContent(),
  '#cache' => [
    'contexts' => [
      'user.roles',
      'languages:language_interface',
    ],
  ],
];
```

### Example 6: Custom Cache Context

**Input:** "I need to vary cache by a custom HTTP header"

**Output:**

```yaml
# my_module.services.yml
services:
  cache_context.custom_header:
    class: Drupal\my_module\Cache\CustomHeaderContext
    arguments: ["@request_stack"]
    tags:
      - { name: cache.context }
```

```php
namespace Drupal\my_module\Cache;

use Drupal\Core\Cache\CacheableMetadata;
use Drupal\Core\Cache\Context\CacheContextInterface;

class CustomHeaderContext implements CacheContextInterface {

  public static function getLabel() {
    return t('Custom header');
  }

  public function getContext() {
    $request = $this->requestStack->getCurrentRequest();
    return $request->headers->get('X-Custom-Header', 'default');
  }

  public function getCacheableMetadata() {
    return new CacheableMetadata();
  }
}
```

```php
// Usage
$build['#cache']['contexts'][] = 'custom_header';
```

### Example 7: Block with Cache Contexts

**Input:** "My block shows different actions based on permissions"

**Output:**

```php
class ActionBlock extends BlockBase {

  public function build() {
    $actions = [];
    if (\Drupal::currentUser()->hasPermission('edit content')) {
      $actions[] = 'Edit';
    }
    return ['#markup' => implode(', ', $actions)];
  }

  public function getCacheContexts() {
    return Cache::mergeContexts(
      parent::getCacheContexts(),
      ['user.permissions']
    );
  }
}
```

## Common Mistakes

| Mistake                      | Impact                                 | Solution                  |
| ---------------------------- | -------------------------------------- | ------------------------- |
| Using `user` for role checks | Cache explosion (1 entry per user)     | Use `user.roles`          |
| Using `session` directly     | Triggers auto-placeholder              | Use lazy builder          |
| Missing context              | Same cached content for all variations | Add appropriate context   |
| Too broad context            | Unnecessary cache variations           | Use most specific context |

## Auto-Placeholdering

These contexts trigger automatic placeholdering in Dynamic Page Cache:

```yaml
# services.yml - default conditions
renderer.config:
  auto_placeholder_conditions:
    contexts:
      - "session"
      - "user"
```

Content with these contexts is replaced with a placeholder and rendered separately.

## Debugging

```bash
# Enable debug headers
$settings['http.response.debug_cacheability_headers'] = TRUE;

# Check applied contexts
curl -sI https://site.com/ | grep X-Drupal-Cache-Contexts
# Output: X-Drupal-Cache-Contexts: languages:language_interface theme url.path user.permissions
```
