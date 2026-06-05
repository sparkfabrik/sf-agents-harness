---
name: drupal-cache-tags
description: Drupal cache tags implementation guide. Use when asked about cache tag naming conventions, entity tags, list tags, custom tags, tag invalidation strategies, or debugging tag-based cache invalidation issues. Covers node:ID, config:name, entity_list patterns.
---

# Drupal Cache Tags

Cache tags enable targeted cache invalidation across all cache bins when underlying data changes.

## When to Use

- Implementing cache invalidation for custom content
- Adding dependencies to render arrays
- Debugging why content doesn't update after edits
- Creating custom tag schemes for external data

## Tag Naming Conventions

| Type        | Pattern                   | Examples                                            |
| ----------- | ------------------------- | --------------------------------------------------- |
| Entity      | `entity_type:id`          | `node:1`, `user:5`, `taxonomy_term:42`              |
| Entity list | `entity_type_list`        | `node_list`, `user_list`                            |
| Bundle list | `entity_type_list:bundle` | `node_list:article`, `node_list:page`               |
| Config      | `config:config_name`      | `config:system.site`, `config:views.view.frontpage` |
| Custom      | `module:identifier`       | `weather:location:milan`, `stock:AAPL`              |

## Step-by-Step: Adding Cache Tags

1. Identify data dependencies in your render array
2. Get tags from entities via `$entity->getCacheTags()`
3. Add tags to `#cache` property
4. For custom data, define meaningful tag names
5. Invalidate tags when data changes

## Examples

### Example 1: Basic Entity Tags

**Input:** "I'm rendering a node title, how do I add cache tags?"

**Output:**

```php
$build['title'] = [
  '#markup' => $node->getTitle(),
  '#cache' => [
    'tags' => $node->getCacheTags(), // Returns ['node:123']
  ],
];
```

### Example 2: Multiple Dependencies

**Input:** "My block shows node info plus site name, what tags do I need?"

**Output:**

```php
use Drupal\Core\Cache\Cache;

$build = [
  '#markup' => $node->getTitle() . ' | ' . $config->get('name'),
  '#cache' => [
    'tags' => Cache::mergeTags(
      $node->getCacheTags(),         // ['node:123']
      ['config:system.site']          // Site name dependency
    ),
  ],
];
```

### Example 3: List Tags for Views/Listings

**Input:** "I have a custom block listing recent articles, what tags should I use?"

**Output:**

```php
$build = [
  '#theme' => 'item_list',
  '#items' => $article_titles,
  '#cache' => [
    'tags' => ['node_list:article'], // Invalidates when ANY article changes
  ],
];
```

### Example 4: Custom Service with Caching

**Input:** "I'm caching computed data based on a node, how do I set it up?"

**Output:**

```php
public function getComputedData(int $nid): array {
  $cid = 'my_module:computed:' . $nid;
  $cache = \Drupal::cache('data');

  if ($cached = $cache->get($cid)) {
    return $cached->data;
  }

  $data = $this->expensiveComputation($nid);
  $cache->set($cid, $data, Cache::PERMANENT, [
    'node:' . $nid,           // Invalidate when node changes
    'my_module:computed',     // Custom tag for bulk invalidation
  ]);

  return $data;
}
```

### Example 5: Programmatic Invalidation

**Input:** "External API data changed, how do I invalidate related caches?"

**Output:**

```php
use Drupal\Core\Cache\Cache;

// Invalidate all caches tagged with these tags (cross-bin)
Cache::invalidateTags(['my_module:external_api', 'my_module:weather']);

// Entity saves automatically invalidate - no manual call needed
$node->save(); // Automatically invalidates node:ID and node_list tags
```

### Example 6: Block with Entity Dependency

**Input:** "My block depends on the current node, how do I add tags dynamically?"

**Output:**

```php
class RelatedContentBlock extends BlockBase {

  public function build() {
    $node = \Drupal::routeMatch()->getParameter('node');
    return [
      '#markup' => $this->getRelatedContent($node),
    ];
  }

  public function getCacheTags() {
    $tags = parent::getCacheTags();
    $node = \Drupal::routeMatch()->getParameter('node');
    if ($node) {
      $tags = Cache::mergeTags($tags, $node->getCacheTags());
    }
    return $tags;
  }
}
```

## Common Mistakes

| Mistake                    | Problem                                | Fix                                                    |
| -------------------------- | -------------------------------------- | ------------------------------------------------------ |
| `my_module:all`            | Too broad, invalidates everything      | Use specific IDs: `my_module:item:123`                 |
| Missing list tags          | New content doesn't appear in listings | Add `entity_type_list` tag                             |
| Forgetting config          | Theme changes don't reflect            | Add `config:block.block.X`                             |
| Manual entity invalidation | Redundant, Drupal handles it           | Remove manual `Cache::invalidateTags()` on entity save |

## Debugging

```bash
# Enable debug headers
$settings['http.response.debug_cacheability_headers'] = TRUE;

# Check X-Drupal-Cache-Tags header in response
curl -sI https://site.com/node/1 | grep X-Drupal-Cache-Tags

# Invalidate specific tag via drush
drush cache-tag-invalidate node:1
```
