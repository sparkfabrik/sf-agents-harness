---
name: drupal-lazy-builders
description: Drupal lazy builders and placeholder implementation. Use when asked about #lazy_builder render array property, TrustedCallbackInterface, auto-placeholdering, BigPipe integration, personalized content caching, or how to make user-specific content cacheable.
---

# Drupal Lazy Builders

Lazy builders defer rendering of dynamic/personalized content, enabling page caching while preserving dynamic elements.

## When to Use

- Displaying user-specific data (name, cart, notifications)
- Content with `session` or `user` cache context
- Fixing UNCACHEABLE pages caused by max-age:0
- Improving authenticated user performance

## How It Works

```
Page renders → Placeholder inserted → Page cached →
Request → Cached page served → Placeholder replaced with fresh content
```

## Argument Restrictions

**Only scalar types allowed:** `string`, `int`, `float`, `bool`, `NULL`
**Not allowed:** Objects, arrays, closures

## Examples

### Example 1: Basic User Greeting

**Input:** "I want to show 'Hello [username]' without breaking page cache"

**Output:**

```php
// In your render array:
$build['greeting'] = [
  '#lazy_builder' => [
    'my_module.lazy_builders:userGreeting',
    [\Drupal::currentUser()->id()],  // Pass user ID, not user object!
  ],
  '#create_placeholder' => TRUE,
];
```

```yaml
# my_module.services.yml
services:
  my_module.lazy_builders:
    class: Drupal\my_module\LazyBuilders
    arguments: ["@entity_type.manager"]
```

```php
<?php
// src/LazyBuilders.php
namespace Drupal\my_module;

use Drupal\Core\Security\TrustedCallbackInterface;
use Drupal\Core\Entity\EntityTypeManagerInterface;

class LazyBuilders implements TrustedCallbackInterface {

  protected EntityTypeManagerInterface $entityTypeManager;

  public function __construct(EntityTypeManagerInterface $entity_type_manager) {
    $this->entityTypeManager = $entity_type_manager;
  }

  public static function trustedCallbacks() {
    return ['userGreeting'];  // MUST list all lazy builder methods
  }

  public function userGreeting(int $uid): array {
    $user = $this->entityTypeManager->getStorage('user')->load($uid);

    return [
      '#markup' => t('Hello @name!', ['@name' => $user->getDisplayName()]),
      '#cache' => [
        'contexts' => ['user'],
        'tags' => ['user:' . $uid],
      ],
    ];
  }
}
```

### Example 2: Shopping Cart Count

**Input:** "Show cart item count in header without breaking cache"

**Output:**

```php
$build['cart'] = [
  '#lazy_builder' => [
    'my_module.lazy_builders:cartCount',
    [session_id()],  // Session-based, will be placeholdered
  ],
  '#create_placeholder' => TRUE,
];
```

```php
public static function trustedCallbacks() {
  return ['cartCount'];
}

public function cartCount(string $session_id): array {
  $count = $this->cartService->getItemCount($session_id);

  return [
    '#markup' => t('@count items', ['@count' => $count]),
    '#cache' => [
      'contexts' => ['session'],
      'max-age' => 0,  // OK here - isolated to placeholder only
    ],
  ];
}
```

### Example 3: Fix UNCACHEABLE Page

**Input:** "My page is UNCACHEABLE because of a timestamp, how do I fix it?"

**Output:**

```php
// BEFORE - breaks page cache:
$build['timestamp'] = [
  '#markup' => 'Generated: ' . date('Y-m-d H:i:s'),
  '#cache' => ['max-age' => 0],  // Makes entire page UNCACHEABLE!
];

// AFTER - isolate with lazy builder:
$build['timestamp'] = [
  '#lazy_builder' => ['my_module.lazy_builders:timestamp', []],
  '#create_placeholder' => TRUE,
];
```

```php
public function timestamp(): array {
  return [
    '#markup' => 'Generated: ' . date('Y-m-d H:i:s'),
    '#cache' => ['max-age' => 0],  // Now only affects this placeholder
  ];
}
```

### Example 4: Pass Multiple Arguments

**Input:** "I need to pass node ID and view mode to my lazy builder"

**Output:**

```php
$build['related'] = [
  '#lazy_builder' => [
    'my_module.lazy_builders:relatedContent',
    [$node->id(), 'teaser', $limit],  // All must be scalar!
  ],
  '#create_placeholder' => TRUE,
];
```

```php
public function relatedContent(int $nid, string $view_mode, int $limit): array {
  $node = $this->entityTypeManager->getStorage('node')->load($nid);
  // ... render related content

  return [
    '#theme' => 'item_list',
    '#items' => $items,
    '#cache' => [
      'tags' => ['node:' . $nid, 'node_list'],
    ],
  ];
}
```

### Example 5: Handle Array Arguments

**Input:** "I need to pass an array of IDs to my lazy builder"

**Output:**

```php
// WRONG - arrays not allowed:
['my_service:method', [[1, 2, 3]]]  // ❌ Will fail

// CORRECT - serialize to string:
$ids = [1, 2, 3];
$build['items'] = [
  '#lazy_builder' => [
    'my_module.lazy_builders:multipleItems',
    [implode(',', $ids)],  // Pass as comma-separated string
  ],
  '#create_placeholder' => TRUE,
];
```

```php
public function multipleItems(string $ids_string): array {
  $ids = array_filter(explode(',', $ids_string));
  $nodes = $this->entityTypeManager->getStorage('node')->loadMultiple($ids);
  // ... render items
}
```

### Example 6: Block with Lazy Builder

**Input:** "My block shows user-specific content, how do I make it cacheable?"

**Output:**

```php
class UserNotificationsBlock extends BlockBase {

  public function build() {
    // Don't render user content directly in build()
    return [
      '#lazy_builder' => [
        'my_module.lazy_builders:notifications',
        [\Drupal::currentUser()->id()],
      ],
      '#create_placeholder' => TRUE,
    ];
  }

  // Block itself is cacheable
  public function getCacheMaxAge() {
    return Cache::PERMANENT;
  }

  public function getCacheContexts() {
    // No user context needed here - lazy builder handles it
    return parent::getCacheContexts();
  }
}
```

### Example 7: Debug Lazy Builder Issues

**Input:** "My lazy builder isn't being called, how do I debug?"

**Output:**

```php
// Common issues:

// 1. Missing TrustedCallbackInterface
class LazyBuilders {  // ❌ Missing interface
}

class LazyBuilders implements TrustedCallbackInterface {  // ✓ Correct
  public static function trustedCallbacks() {
    return ['myMethod'];  // Must list the method!
  }
}

// 2. Wrong service name
'wrong_service:method'  // Check services.yml spelling

// 3. Object argument
['service:method', [$node]]  // ❌ Pass $node->id() instead

// 4. Check placeholder in HTML source:
// Look for: data-big-pipe-placeholder-id="callback=my_module..."
```

### Example 8: Lazy Builder in Twig

**Input:** "Can I use lazy builder directly in Twig template?"

**Output:**

```php
// In preprocess or controller, add to variables:
$variables['user_greeting'] = [
  '#lazy_builder' => ['my_module.lazy_builders:greeting', [$uid]],
  '#create_placeholder' => TRUE,
];
```

```twig
{# In template #}
<div class="greeting">
  {{ user_greeting }}
</div>
```

## Render Element Restrictions

Lazy builder elements can **only** contain:

```php
$build['lazy'] = [
  '#lazy_builder' => [...],      // Required
  '#create_placeholder' => TRUE, // Optional
  '#cache' => [...],             // Optional
  '#weight' => 10,               // Optional
];

// NOT allowed alongside #lazy_builder:
// '#markup', '#theme', '#type', '#prefix', '#children', etc.
```

## Common Mistakes

| Mistake                               | Error               | Fix                        |
| ------------------------------------- | ------------------- | -------------------------- |
| Object argument                       | Serialization error | Pass ID, load in callback  |
| Array argument                        | Runtime error       | Use `implode()`            |
| Missing `trustedCallbacks()`          | Security exception  | Implement interface method |
| Method not in `trustedCallbacks()`    | Security exception  | Add method to array        |
| Other properties with `#lazy_builder` | Render error        | Remove extra properties    |

## Debugging

```bash
# Check if BigPipe is processing placeholders
# Look in HTML source for:
# <div data-big-pipe-placeholder-id="callback=...">

# Disable BigPipe temporarily to test
drush pm:uninstall big_pipe

# Check Drupal logs for lazy builder errors
drush watchdog:show --type=php
```
