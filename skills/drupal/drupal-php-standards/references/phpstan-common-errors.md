# PHPStan Level 8 + Strict Rules: Common Errors Reference

This reference catalogs the most frequent PHPStan errors encountered in this
project, with concrete before/after examples. The SKILL.md covers the
principles; this file has the full error messages and detailed fixes.

## Table of Contents

1. [No value type specified in iterable type array](#1-no-value-type-specified-in-iterable-type-array)
2. [Construct empty() is not allowed](#2-construct-empty-is-not-allowed)
3. [Only booleans are allowed in if condition](#3-only-booleans-are-allowed-in-if-condition)
4. [in_array() requires parameter #3 to be set](#4-in_array-requires-parameter-3-to-be-set)
5. [Short ternary operator is not allowed](#5-short-ternary-operator-is-not-allowed)
6. [Parameter is not contravariant](#6-parameter-is-not-contravariant)
7. [Return type is not covariant](#7-return-type-is-not-covariant)
8. [Does not call parent constructor](#8-does-not-call-parent-constructor)
9. [Readonly property already assigned](#9-readonly-property-already-assigned)
10. [@SuppressWarnings has invalid value](#10-suppresswarnings-has-invalid-value)
11. [Return type static vs concrete class](#11-return-type-static-vs-concrete-class)
12. [@phpstan-param for inherited methods](#12-phpstan-param-for-inherited-methods)

---

## 1. No value type specified in iterable type array

**Error:** `Function x() has parameter $y with no value type specified in iterable type array.`

PHPStan level 8 requires all array parameters and return types to declare
what they contain. A bare `array` type is not acceptable.

### Simple arrays (one type of element)

```php
// Error
function process(array $items): void {

// Fix — specify key and value types
/**
 * @phpstan-param array<array-key, string> $items
 */
function process(array $items): void {
```

### Associative arrays with known keys

```php
// Fix — use array shape syntax for known structures
/**
 * @phpstan-param array{name: string, age: int, email?: string} $user
 */
function createUser(array $user): void {
```

### Nested arrays (Drupal render arrays, form structures)

When the structure is known, describe it precisely:

```php
/**
 * @phpstan-param array{data?: string|array{preview?: string|array{'#access'?: bool}}} $variables
 */
function preprocess(array $variables): void {
    if (!isset($variables['data']) || !\is_array($variables['data'])) {
        return;
    }

    $data = &$variables['data'];

    if (!isset($data['preview']) || !\is_array($data['preview'])) {
        return;
    }

    if (isset($data['preview']['#access']) && $data['preview']['#access'] === FALSE) {
        unset($data['preview']);
    }
}
```

When the structure is too complex or truly dynamic, use the escape hatch:

```php
/**
 * @phpstan-param array<array-key, mixed> $variables
 */
function preprocess(array $variables): void {
```

**Why not level 9?** Level 9+ requires strict handling of `mixed` — you can
only pass `mixed` to another `mixed`. Using `array<array-key, mixed>` at
level 8 gives you a workable escape hatch that level 9 would close.

**Best practice:** If you find yourself writing deeply nested array shape
annotations, consider whether a DTO class would be clearer. A class with typed
properties gives you actual enforcement, not just documentation.

---

## 2. Construct empty() is not allowed

**Error:** `Construct empty() is not allowed. Use more strict comparison.`

`empty()` is a loose comparison that treats `null`, `false`, `0`, `''`, `'0'`,
and `[]` all as "empty." The strict rules ban it because it hides bugs where
`0` or `'0'` are valid values.

```php
// Error
if (empty($variable)) {

// Fix — be explicit about what "empty" means for your case
// If checking for null or empty string:
if ($variable === null || $variable === '') {

// If checking for null only:
if ($variable === null) {

// If checking for empty array:
if ($variable === []) {

// If checking for falsy (and you've thought about it):
if ($variable === null || $variable === false || $variable === '') {
```

---

## 3. Only booleans are allowed in if condition

**Error:** `Only booleans are allowed in an if condition, mixed given.`

PHP's loose type coercion lets you write `if ($variable)` when `$variable`
is a string or mixed. The strict rules require an explicit boolean expression.

```php
// Error
if ($variables['data']) {

// Fix — explicit comparison
if ($variables['data'] === TRUE) {

// Or for existence + non-empty:
if (isset($variables['data']) && $variables['data'] !== '') {

// For checking non-null:
if ($variables['data'] !== NULL) {
```

This also applies to negation:

```php
// Error
if (!$value) {

// Fix
if ($value === NULL) {
// or
if ($value === FALSE) {
// or
if ($value === '' || $value === NULL) {
```

---

## 4. in_array() requires parameter #3 to be set

**Error:** `Call to function in_array() requires parameter #3 to be set.`

The `$strict` parameter defaults to `false`, meaning `in_array()` uses loose
comparison (`==`). The strict rules require explicit `true`.

```php
// Error
\in_array($value, $allowed);

// Fix
\in_array($value, $allowed, true);
```

Same requirement applies to:

- `\array_search($needle, $haystack, true)`
- `\array_keys($array, $search_value, true)` (when using the search parameter)
- `\base64_decode($string, true)`

---

## 5. Short ternary operator is not allowed

**Error:** `Short ternary operator is not allowed. Use null coalesce operator if applicable or consider using long ternary.`

The short ternary `$a ?: $b` uses PHP's loose boolean evaluation. A value
of `0`, `'0'`, or `''` would bypass to the fallback, which is often a bug.

```php
// Error
$name = $input ?: 'default';

// Fix — use null coalesce (strict null check)
$name = $input ?? 'default';

// Fix — use full ternary with explicit condition
$name = ($input !== '' && $input !== null) ? $input : 'default';
```

Use `??` when you only want to replace `null`. Use a full ternary when you
need to exclude other specific values.

---

## 6. Parameter is not contravariant

**Error:** `Parameter #1 $x (SpecificType) of method Child::method() should be contravariant with parameter $x (BroaderType) of method Parent::method().`

A child class method's parameters must accept the same type or broader than
the parent's. Narrowing the type breaks the Liskov Substitution Principle:
any code that calls the parent's method with a valid argument must also work
when given the child class.

```php
// Error — child narrows Animal to Mammal
class AnimalFeeder {
    public function feed(Animal $animal): void {}
}

class MammalFeeder extends AnimalFeeder {
    public function feed(Mammal $animal): void {}  // Violation!
}
```

In Drupal, this most commonly appears when a parent declares `array` and
the child uses `array<string, mixed>`:

```php
// Error — child's @param is more specific than parent
/**
 * @param array<string, mixed> $base_plugin_definition
 */
public function getDerivativeDefinitions($base_plugin_definition): array {

// Fix — use @phpstan-param with the parent's broader type
/**
 * {@inheritdoc}
 *
 * @phpstan-param array<array-key, mixed> $base_plugin_definition
 */
public function getDerivativeDefinitions($base_plugin_definition): array {
```

---

## 7. Return type is not covariant

**Error:** `Return type (BroaderType) of method Child::method() is not covariant with return type (SpecificType) of method Parent::method().`

A child class method's return type must be the same or narrower than the
parent's. Widening it breaks LSP: callers expecting the parent's specific
return type would get something less specific.

```php
// Error — child widens Book to Product
class BookFactory {
    public function create(): Book { return new Book(); }
}

class GenericFactory extends BookFactory {
    public function create(): Product { return new Product(); }  // Violation!
}
```

Fix by returning the same type or a subtype of the parent's return type.

---

## 8. Does not call parent constructor

**Error:** `ChildClass::__construct() does not call parent constructor from ParentClass.`

When extending a class that has a constructor, the child must call
`parent::__construct()`. This is especially common with Drupal plugin
attributes extending `AttributeBase`.

```php
// Error — no parent::__construct() call
final class MyAttribute extends AttributeBase {
    public function __construct(
        public readonly string $id,
        public readonly ?TranslatableMarkup $label,
    ) {}
}

// Fix — call parent constructor
final class MyAttribute extends AttributeBase {
    public function __construct(
        string $id,  // NOT promoted — see next section
        public readonly ?TranslatableMarkup $label,
    ) {
        parent::__construct($id);
    }
}
```

---

## 9. Readonly property already assigned

**Error:** `Readonly property ClassName::$id is already assigned.`

This happens when you use constructor promotion (`public readonly`) for a
parameter that you also pass to `parent::__construct()`. The parent
assigns the property, and then the promotion tries to assign it again.

```php
// Error — $id is promoted AND forwarded to parent
final class MyAttribute extends AttributeBase {
    public function __construct(
        public readonly string $id,  // Promoted → assigns $this->id
        public readonly ?TranslatableMarkup $label,
    ) {
        parent::__construct($id);  // Parent also assigns $this->id → Error!
    }
}

// Fix — don't promote the parameter that the parent needs
final class MyAttribute extends AttributeBase {
    public function __construct(
        string $id,  // Plain parameter, not promoted
        public readonly ?TranslatableMarkup $label,
    ) {
        parent::__construct($id);  // Parent handles the assignment
    }
}
```

The rule: if a parent constructor accepts and stores a value, don't use
constructor promotion for that parameter in the child. Only promote
parameters that are unique to the child class.

---

## 10. @SuppressWarnings has invalid value

**Error:** `PHPDoc tag @SuppressWarnings has invalid value ((PHPMD.UnusedFormalParameter)): Unexpected token ".UnusedFormalParameter)", expected ')' at offset 156`

PHPStan parses docblocks and trips on the unquoted `PHPMD.UnusedFormalParameter`
because the dot is unexpected syntax. Wrap it in double quotes:

```php
// Error
/**
 * @SuppressWarnings(PHPMD.UnusedFormalParameter)
 */

// Fix
/**
 * @SuppressWarnings("PHPMD.UnusedFormalParameter")
 */
```

This applies to all PHPMD suppression annotations:

- `@SuppressWarnings("PHPMD.CyclomaticComplexity")`
- `@SuppressWarnings("PHPMD.NPathComplexity")`
- `@SuppressWarnings("PHPMD.ExcessiveMethodLength")`
- etc.

---

## 11. Return type static vs concrete class

**Error:** `Method ClassName::create() should return static(ClassName) but returns ClassName.`

When a parent method declares `static` as its return type and you return
`new ClassName()`, PHPStan flags the mismatch. Fix by making the class
`final` and using the concrete class name as the return type:

```php
// Error
class MyPlugin extends ProcessPluginBase {
    public static function create(...): static {
        return new MyPlugin(...);  // Returns ClassName, not static
    }
}

// Fix — final class + concrete return type
final class MyPlugin extends ProcessPluginBase {
    public static function create(...): MyPlugin {
        return new MyPlugin(...);
    }
}
```

If the class cannot be `final` (it's designed to be extended), use
`new static()` instead:

```php
class MyBasePlugin extends ProcessPluginBase {
    public static function create(...): static {
        return new static(...);  // Returns the actual class at runtime
    }
}
```

---

## 12. @phpstan-param for inherited methods

When overriding methods from Drupal core or contrib, use `@phpstan-param`
instead of `@param` for type annotations. This tells PHPStan the precise
types without creating a conflict with the parent's existing docblock.

Common cases:

```php
// Plugin constructor
/**
 * @phpstan-param array<string, mixed> $configuration
 * @phpstan-param string $plugin_id
 * @phpstan-param mixed $plugin_definition
 */
public function __construct(
    array $configuration,
    $plugin_id,
    $plugin_definition,
    private readonly Connection $database,
) {
    parent::__construct($configuration, $plugin_id, $plugin_definition);
}

// Factory method
/**
 * @phpstan-param array<string, mixed> $configuration
 */
public static function create(
    ContainerInterface $container,
    array $configuration,
    $plugin_id,
    $plugin_definition,
): MyPlugin {

// Deriver
/**
 * @phpstan-param array<array-key, mixed> $base_plugin_definition
 * @phpstan-return array<string, array<string, mixed>>
 */
public function getDerivativeDefinitions($base_plugin_definition): array {

// Process plugin transform
/**
 * @phpstan-return string|list<array{id: int, revision_id: int}>
 */
public function transform(
    mixed $value,
    MigrateExecutableInterface $migrate_executable,
    Row $row,
    string $destination_property,
): mixed {
```

Use `@phpstan-param` whenever the method comes from a parent class in Drupal
core or contrib. For methods you define yourself, regular `@param` is fine.
