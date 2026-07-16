---
name: drupal-qa
description: Fix Drupal code quality issues (PHPCS, PHPMD, PHPStan, CSpell) following SparkFabrik standards without
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

### 2. PHPStan Fixes: Use the Shared Error Catalogue

The canonical, fully worked catalogue of PHPStan level 8 errors and their fixes lives in the `drupal-php-standards` skill, in `references/phpstan-common-errors.md`. Read it before fixing any PHPStan error. The rules most often needed while fixing QA failures:

- **Inherited methods** (catalogue §12): when overriding a method from Drupal core or contrib (`PluginBase`, `ContainerFactoryPluginInterface::create()`, `DeriverInterface::getDerivativeDefinitions()`), use `@phpstan-param` / `@phpstan-return` under `{@inheritdoc}` instead of regular `@param` / `@return`, so the annotations do not conflict with parent documentation.
- **`static` vs concrete return type** (catalogue §11): when `create()` returns `new ClassName()` and PHPStan reports `return.type`, change the return type from `static` to the concrete class name and make the class `final`. Do not make the class `final` when it is designed to be extended or already has subclasses; in that case keep `static` and return `new static()`.
- **Parameter contravariance** (catalogue §6): when PHPStan reports `method.childParameterType`, do not narrow the native type. Add a `@phpstan-param` with the parent's broader type (e.g. `array<array-key, mixed>` where the parent declares `array`).

### 3. Type Assertions Over Ignores
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

### 4. Refactor Complex Code
When PHPMD reports high cyclomatic complexity, never add `@SuppressWarnings(PHPMD.CyclomaticComplexity)`. Extract focused methods instead; see the strategies and worked example in Step 4 of the Workflow below.

### 5. When Suppressions Are Acceptable

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

### Plugin Configuration Arrays and Derivers
For `@phpstan-param` / `@phpstan-return` annotations on plugin constructors, `create()` factory methods, and `getDerivativeDefinitions()`, follow the inherited-methods rule in Core Principle 2 and the worked examples in the `drupal-php-standards` catalogue (`references/phpstan-common-errors.md`, §11 and §12).

## Questions to Ask User

When encountering these situations, **ALWAYS ask the user**:

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