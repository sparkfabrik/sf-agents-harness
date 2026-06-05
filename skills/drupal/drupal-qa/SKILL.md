---
name: drupal-qa
description:
  Fix Drupal code quality issues (PHPCS, PHPMD, PHPStan, CSpell) following SparkFabrik standards without
  using suppressions or ignores unless absolutely necessary.
---

# SparkFabrik Drupal QA Skill

## Purpose

Fix Drupal code quality issues (PHPCS, PHPMD, PHPStan, CSpell) following SparkFabrik standards without using suppressions or ignores unless absolutely necessary.

## When to Use

Use this skill when:

- Pre-commit hooks fail with QA errors
- You need to fix code quality issues in Drupal modules
- `make drupal-qa` reports errors
- User explicitly requests QA fixes

## Core Principles

### 1. Fix, Don't Suppress

**ALWAYS prefer fixing the actual issue over suppressing warnings.**

❌ **BAD**: Add `@SuppressWarnings(PHPMD.CyclomaticComplexity)`
✅ **GOOD**: Refactor method to reduce complexity

❌ **BAD**: Add `// @phpstan-ignore-next-line`
✅ **GOOD**: Add proper type assertions or fix the actual type issue

❌ **BAD**: Add global ignoreErrors in phpstan.neon
✅ **GOOD**: Fix each issue individually with proper types

### 2. PHPStan Annotations for Inherited Methods

When inheriting from Drupal core classes or interfaces (like `ContainerFactoryPluginInterface`, `PluginBase`, `ProcessPluginBase`, `DeriverInterface`), use `@phpstan-param` and `@phpstan-return` instead of regular `@param` and `@return` to avoid conflicting with parent documentation:

❌ **BAD**:

```php
/**
 * Constructs a MyPlugin plugin.
 *
 * @param array<string, mixed> $configuration
 *   The plugin configuration.
 * @param string $plugin_id
 *   The plugin ID.
 */
public function __construct(array $configuration, $plugin_id, $plugin_definition) {
  parent::__construct($configuration, $plugin_id, $plugin_definition);
}
```

✅ **GOOD**:

```php
/**
 * {@inheritdoc}
 *
 * @phpstan-param array<string, mixed> $configuration
 *   The plugin configuration.
 * @phpstan-param string $plugin_id
 *   The plugin ID.
 * @phpstan-param mixed $plugin_definition
 *   The plugin definition.
 */
public function __construct(array $configuration, $plugin_id, $plugin_definition) {
  parent::__construct($configuration, $plugin_id, $plugin_definition);
}
```

**When to use `@phpstan-*`:**

- In `__construct()` for plugins extending base classes like `PluginBase`
- In `create()` for plugins implementing `**ContainerFactoryPluginInterface**`
- In `getDerivativeDefinitions()` for classes implementing `DeriverInterface`
- Any method from custom module sources that overrides a parent method from Drupal core or contrib modules

### 3. Fix `static` Return Type Errors with Concrete Class Names

When PHPStan reports a `return.type` error like:

```
Method Drupal\luiss_migrate\Plugin\migrate\Deriver\LuissPageRichAccordionParagraphDeriver::create() should return
         static(Drupal\luiss_migrate\Plugin\migrate\Deriver\LuissPageRichAccordionParagraphDeriver) but returns
         Drupal\luiss_migrate\Plugin\migrate\Deriver\LuissPageRichAccordionParagraphDeriver.
         🪪  return.type
```

This happens when a method returns `new ClassName()` instead of `new static()`, or when using `new static()` in a non-final class. The fix is to:

1. **Change the return type from `static` to the concrete class name**
2. **Make the class `final`**

❌ **BAD**: Suppress the error

```php
// @phpstan-ignore-next-line return.type
public static function create(...): static {
  return new MyClass(...);
}
```

❌ **BAD**: Keep using `static` return type

```php
class MyDeriver extends DeriverBase {
  public static function create(ContainerInterface $container, $base_plugin_id): static {
    return new MyDeriver();
  }
}
```

✅ **GOOD**: Use concrete class name and make class final

```php
final class MyDeriver extends DeriverBase implements ContainerDeriverInterface {
  /**
   * {@inheritdoc}
   */
  public static function create(ContainerInterface $container, $base_plugin_id): MyDeriver {
    return new MyDeriver();
  }
}
```

```php
final class MyPlugin extends ProcessPluginBase implements ContainerFactoryPluginInterface {
  /**
   * {@inheritdoc}
   */
  public static function create(
    ContainerInterface $container,
    array $configuration,
    $plugin_id,
    $plugin_definition
  ): MyPlugin {
    return new MyPlugin(
      $configuration,
      $plugin_id,
      $plugin_definition,
      $container->get('database'),
    );
  }
}
```

**Key points:**

- Replace `static` with the concrete class name in the return type
- Add `final` to the class definition to prevent inheritance issues
- This applies to factory methods like `create()`, `createInstance()`, etc.

**When NOT to use `final`:**

- If the class is explicitly designed to be extended (base classes, abstract classes)
- If other classes in the codebase already extend it

In those rare cases where `final` is not possible, keep `static` as return type and ensure you use `new static()` instead of `new ClassName()`.

### 4. Fix Parameter Contravariance Errors

When PHPStan reports a `method.childParameterType` error like:

> Parameter #1 $base_plugin_definition (array<string, mixed>) of method MyClass::getDerivativeDefinitions() should be contravariant with parameter $base_plugin_definition (array) of method ParentClass::getDerivativeDefinitions()

This means the child method's parameter type is **more specific** than the parent's, violating the [Liskov Substitution Principle](https://en.wikipedia.org/wiki/Liskov_substitution_principle). In PHP, method parameters must be contravariant (same or broader type than parent).

**The fix**: Add a `@phpstan-param` annotation with the broader type matching the parent's signature. This tells PHPStan to use the broader type for analysis without changing the actual PHP type hint.

❌ **BAD**: Suppress or ignore

```php
// @phpstan-ignore-next-line method.childParameterType
public function getDerivativeDefinitions($base_plugin_definition): array {
```

❌ **BAD**: Change the `@param` type to be more specific than the parent

```php
/**
 * @param array<string, mixed> $base_plugin_definition
 */
public function getDerivativeDefinitions($base_plugin_definition): array {
```

✅ **GOOD**: Use `@phpstan-param` with the parent's broader type

```php
/**
 * {@inheritdoc}
 *
 * @phpstan-param array<array-key, mixed> $base_plugin_definition
 */
public function getDerivativeDefinitions($base_plugin_definition): array {
```

**Common cases where this applies:**

- `getDerivativeDefinitions($base_plugin_definition)` - parent uses `array`, child uses `array<string, mixed>`
- `transform($value, ...)` - parent uses `mixed`, child uses a more specific type
- `__construct(array $configuration, ...)` - parent uses `array`, child uses `array<string, mixed>`
- Any overridden method where you've added generic type annotations that are stricter than the parent

**How to determine the correct `@phpstan-param` type:**

1. Look at the parent class/interface parameter type
2. Use that same type (or broader) in the `@phpstan-param` annotation
3. Common broader types: `array` becomes `array<array-key, mixed>`, specific types become `mixed`

### 5. Type Assertions Over Ignores

When PHPStan complains about type narrowing, use assertions:

❌ **BAD**:

```php
// @phpstan-ignore-next-line method.notFound
$paragraph->getRevisionId();
```

✅ **GOOD**:

```php
assert($paragraph instanceof RevisionableInterface);
$revision_id = $paragraph->getRevisionId();
```

### 6. Refactor Complex Code

When PHPMD reports high cyclomatic complexity:

❌ **BAD**: Add `@SuppressWarnings(PHPMD.CyclomaticComplexity)`

✅ **GOOD**: Extract methods to reduce complexity:

```php
// Before: 20 lines, CC=15
public function transform($value, $exec, $row, $dest) {
  // ... complex logic ...
}

// After: Multiple focused methods
public function transform($value, $exec, $row, $dest) {
  $data = $this->extractData($row);
  return $this->processData($data);
}

private function extractData($row) { /* ... */ }
private function processData($data) { /* ... */ }
```

### 7. When Suppressions Are Acceptable

Only use suppressions in these specific cases:

1. **Third-party code issues** - Code you cannot modify
2. **Drupal core API limitations** - Framework constraints
3. **False positives** - After confirming with user that it's truly a false positive

**ALWAYS ask the user first** before adding any suppression.

## Workflow

### Step 1: Analyze QA Report

Run `make drupal-qa` and categorize errors:

```bash
make drupal-qa
```

Categorize by type:

- **PHPCS**: Code style (usually auto-fixable)
- **CSpell**: Unknown words (add to dictionary)
- **PHPMD**: Code complexity, unused code
- **PHPStan**: Type safety issues

You can run individual tools to speed up the process:

```bash
# Run PHPCS only
make drupal-qa phpcs

# Run CSpell only
make drupal-qa cspell

# Run PHPMD only
make drupal-qa phpmd

# Run PHPStan only
make drupal-qa phpstan
```

**NEVER** run individual tools from bin directory! **ALWAYS** use the `make drupal-qa <tool>` command to ensure proper environment variables and configuration are applied.

### Step 2: Fix PHPCS Issues

- Long lines: Wrap them properly
- Complex expressions: Simplify or break into multiple lines

### Step 3: Fix CSpell Issues

Add legitimate technical terms to dictionary:

```bash
# Edit src/drupal/project-dictionary.txt
# Add one word per line, alphabetically sorted
```

### Step 4: Fix PHPMD Issues

#### Cyclomatic Complexity

**Target**: Keep CC < 10

**Strategies**:

1. **Extract methods**: Break down complex logic
2. **Early returns**: Reduce nesting
3. **Strategy pattern**: For multiple conditions
4. **Guard clauses**: Check preconditions first

Example refactoring:

```php
// Before: CC = 15
private function processItem($item, $config) {
  if ($config['type'] === 'image') {
    if (isset($item['url'])) {
      // ... 10 more lines
    }
  } elseif ($config['type'] === 'video') {
    // ... more complex logic
  }
  // ... etc
}

// After: CC = 3
private function processItem($item, $config) {
  if ($config['type'] === 'image') {
    return $this->processImage($item);
  }
  if ($config['type'] === 'video') {
    return $this->processVideo($item);
  }
  return $this->processDefault($item);
}

private function processImage($item) { /* ... */ }
private function processVideo($item) { /* ... */ }
private function processDefault($item) { /* ... */ }
```

#### Unused Parameters

If truly unused, remove them. If needed for interface compliance, document why:

```php
// Interface requires $langcode but we don't use it yet
public function process($value, $langcode) {
  // Document: $langcode reserved for future i18n support
  return $this->doProcess($value);
}
```

### Step 5: Fix PHPStan Issues

#### Type Narrowing with Assertions

```php
// PHPStan error: Call to method on EntityInterface that doesn't exist

// Add assertion to narrow type
assert($entity instanceof ContentEntityInterface);
$entity->hasField('field_name');
```

#### Missing Iterable Types

Specify generic types:

```php
// Before: array
/** @param array $items */

// After: array with generic types
/** @param array<int, string> $items */
```

#### Null Safety

```php
// Before: Possible null pointer
$statement->fetchAll();

// After: Null check
$statement = $query->execute();
if ($statement === NULL) {
  return [];
}
$results = $statement->fetchAll();
```

#### Return Type Mismatches

Fix the return type:

```php
// Before: Returns bool|int|string but expects int|string
return is_scalar($value) ? $value : NULL;

// After: Proper type filtering
if (is_int($value) || is_string($value)) {
  return $value;
}
return NULL;
```

### Step 6: Verify Fixes

```bash
make drupal-qa
```

All checks must pass before committing.

## Common Drupal Patterns

### Entity Type Assertions

```php
/** @var \Drupal\Core\Entity\ContentEntityStorageInterface $storage */
$storage = $this->entityTypeManager->getStorage('media');

// For specific storage types
assert($storage instanceof MediaStorage);
```

### Dependency Injection

Avoid `\Drupal::` static calls in classes:

```php
// Before
$database = \Drupal::database();

// After: Inject via constructor
public function __construct(Connection $database) {
  $this->database = $database;
}

public static function create(ContainerInterface $container, ...) {
  return new static(
    $container->get('database')
  );
}
```

### Plugin Configuration Arrays

Specify types for plugin configuration using `@phpstan-param` when inheriting from Drupal core:

```php
// For __construct() overriding parent from ProcessPluginBase/PluginBase
/**
 * Constructs a MyPlugin plugin.
 *
 * @phpstan-param array<string, mixed> $configuration
 *   The plugin configuration.
 * @param string $plugin_id
 *   The plugin ID.
 * @param mixed $plugin_definition
 *   The plugin definition.
 * @param \Drupal\Core\Database\Connection $database
 *   The database connection.
 */
public function __construct(
  array $configuration,
  $plugin_id,
  $plugin_definition,
  Connection $database,
) {
  parent::__construct($configuration, $plugin_id, $plugin_definition);
}

// For create() factory method
/**
 * {@inheritdoc}
 *
 * @phpstan-param array<string, mixed> $configuration
 */
public static function create(
  ContainerInterface $container,
  array $configuration,
  $plugin_id,
  $plugin_definition
): static {
  return new static(
    $configuration,
    $plugin_id,
    $plugin_definition,
    $container->get('database'),
  );
}
```

### Deriver getDerivativeDefinitions

For DeriverInterface implementations, use `@phpstan-*` annotations:

```php
/**
 * {@inheritdoc}
 *
 * @phpstan-param array<string, mixed> $base_plugin_definition
 * @phpstan-return array<string, array<string, mixed>>
 */
public function getDerivativeDefinitions($base_plugin_definition): array {
  // Implementation
}
```

## Questions to Ask User

When encountering these situations, **ALWAYS ask the user**:
`****`

1. **High complexity that's hard to refactor**
   - "This method has CC=15. I can see it's handling complex migration logic. Would you like me to refactor it into smaller methods, or is there a reason to keep it as-is?"

2. **Unused parameters from interface**
   - "The parameter `$langcode` is required by the interface but not used. Should I: (a) implement i18n support, (b) document why it's unused, or (c) remove it if the interface allows?"

3. **Drupal core API limitations**
   - "PHPStan complains about `new static()` which is a standard Drupal plugin pattern. This appears to be a framework constraint. Should we add a baseline exception for this specific pattern?"

4. **Unclear business logic**
   - "I see complex conditional logic here but I'm not sure how to simplify it without changing behavior. Can you explain what this code does so I can refactor it properly?"

5. **Potential false positives**
   - "PHPStan reports this as an error, but it looks like the types are actually correct. Can you confirm this is a false positive before I investigate further?"

## Anti-Patterns to Avoid

### ❌ Don't: Add Global Ignores

```php
// phpstan.neon
ignoreErrors:
  - '#.*#'  // NEVER do this
```

### ❌ Don't: Suppress Without Understanding

```php
// @phpstan-ignore-next-line
$result = $entity->getField();  // Why ignore? Fix the type issue!
```

### ❌ Don't: Use Empty Catch Blocks

```php
try {
  $result = $query->execute();
} catch (\Exception) {
  // Silently failing - BAD!
}
```

### ❌ Don't: Comment Out Code

```php
// Commented code to avoid PHPMD error - BAD!
// $unused_variable = $this->calculateValue();
```

## Success Criteria

QA is complete when:

1. ✅ `make drupal-qa` passes with 0 errors
2. ✅ No suppressions added (or user explicitly approved them)
3. ✅ Code is more maintainable than before
4. ✅ All legitimate technical terms in dictionary
5. ✅ Type safety improved with assertions
6. ✅ Complex methods refactored into smaller pieces
