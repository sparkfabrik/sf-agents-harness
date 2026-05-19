---
name: drupal-php-standards
description: >
  Write PHP code that passes all QA checks (PHPCS, PHPStan level 8, PHPMD, CSpell) on the first try.
  This project enforces strict coding standards via GrumPHP with zero-tolerance thresholds.
  Use this skill whenever you are writing or modifying PHP code in a Drupal module, theme, or
  any .php/.module/.install/.inc/.theme file. Even for small changes — a one-line hook, a new
  service method, a migration plugin — always apply these rules. The goal is to never trigger a
  QA failure at commit time. If you are *fixing* existing QA failures after the fact, use the
  drupal-qa skill instead; this skill is about getting it right from the start.
---

# Writing QA-Compliant PHP for Drupal 11

This project runs four PHP quality tools via GrumPHP with **zero tolerance** — a single
violation from any tool blocks the commit. This skill ensures you write code that passes
all four checks on the first attempt.

The four tools and what they care about:

| Tool        | Focus                                | Level                                                        |
|-------------|--------------------------------------|--------------------------------------------------------------|
| **PHPCS**   | Code style and formatting            | Drupal + PreviousNextDrupal + SparkFabrikCS + DrupalPractice |
| **PHPStan** | Static type analysis                 | Level 8 (strictest) with `phpstan-strict-rules`              |
| **PHPMD**   | Code complexity and design           | All rulesets except cleancode                                |
| **CSpell**  | Spelling in identifiers and comments | en-US + Italian dictionary                                   |

## Suppression Prohibition

**All forms of QA suppression are forbidden when writing code.**

This is not a preference — it is a hard constraint. Never emit any of the
following:

| Form                    | Example                                           | Forbidden because                          |
|-------------------------|---------------------------------------------------|--------------------------------------------|
| PHPStan inline ignore   | `// @phpstan-ignore-next-line`                    | Masks a type or logic error                |
| PHPStan scoped ignore   | `// @phpstan-ignore method.notFound`              | Same                                       |
| PHPMD docblock suppress | `@SuppressWarnings("PHPMD.CyclomaticComplexity")` | Hides design problems                      |
| PHPCS inline disable    | `// phpcs:ignore` / `// phpcs:disable`            | Hides style violations                     |
| Global PHPStan baseline | `ignoreErrors:` entry in `phpstan.neon`           | Silently accepts broken types project-wide |

> **Design principle:** if the code you are about to write would need a
> suppression
> annotation to pass QA, the code is wrong. Write it differently.

Think through QA compliance before writing — not after. The sections below give
you the patterns to do this.
The `references/phpstan-common-errors.md` reference lists every frequent error
class with a clean fix.

**The only valid use of `@phpstan-param` / `@phpstan-return`** is for inherited
Drupal core / contrib methods where you need to narrow types without conflicting
with the parent docblock. This is type annotation, not suppression — see the
patterns in `references/phpstan-common-errors.md` sections 6 and 12.

If you reach a situation where you genuinely cannot write clean code that passes
QA, **stop and tell the user**.
See the `drupal-qa` skill for the exact protocol.

## File Boilerplate

Every PHP file must start with:

```php
<?php

declare(strict_types=1);
```

No space around `=` in the declare statement. This is enforced by
`SlevomatCodingStandard.TypeHints.DeclareStrictTypes`.

## Formatting Rules

### Indentation and Line Length

- 2-space indentation (no tabs)
- Lines should stay under 80 characters where practical

### Trailing Commas

Always use trailing commas in multi-line function calls, declarations, and arrays.
This is enforced by `SlevomatCodingStandard.Functions.RequireTrailingCommaInCall`
and `RequireTrailingCommaInDeclaration`.

```php
// Correct
$this->entityTypeManager->getStorage(
    'node',
);

public function __construct(
    private readonly Connection $database,
    private readonly LoggerInterface $logger,
) {}

$items = [
    'first',
    'second',
];
```

### Blank Line Before return and continue

Always insert a blank line before `return` and `continue` when they follow
a statement. This is the single custom sniff from SparkFabrikCS.

```php
public function process(string $value): string {
    $result = \trim($value);

    return $result;  // blank line above
}
```

No blank line is needed when `return` is the very first statement in a block:

```php
if ($value === NULL) {
    return '';  // first statement — no blank line needed
}
```

### No Blank Line After Opening Brace

```php
public function example(): void {
    $x = 1;  // no blank line between brace and first statement
}
```

### Multi-Line Constructor Signatures

When a constructor exceeds 80 characters, break it across multiple lines
(enforced by `SlevomatCodingStandard.Classes.RequireMultiLineMethodSignature`
with `minLineLength: 80` targeting `__construct`).

### Use Statement Ordering

`use` import statements must be sorted alphabetically.
Enforced by `SlevomatCodingStandard.Namespaces.AlphabeticallySortedUses`.

### Fully Qualified Global Functions

Always prefix global PHP functions with a backslash: `\array_map()`, `\count()`,
`\sprintf()`, `\trim()`, `\is_array()`, `\str_starts_with()`, etc.
Enforced by `SlevomatCodingStandard.Namespaces.FullyQualifiedGlobalFunctions`.

### Null-Safe Operator

Use the null-safe operator `?->` instead of null-check-then-call patterns.
Enforced by `SlevomatCodingStandard.ControlStructures.RequireNullSafeObjectOperator`.

```php
// Wrong
$value = $entity !== NULL ? $entity->label() : NULL;

// Right
$value = $entity?->label();
```

### TRUE, FALSE and NULL must be uppercase

Enforced by `Generic.PHP.UpperCaseConstant.Found`.

```php
// Wrong
if ($value === null) {
    return false;
}
// Right
if ($value === NULL) {
    return FALSE;
}
```

### Static Closures

Closures that don't reference `$this` must be declared `static`.
Enforced by `SlevomatCodingStandard.Functions.StaticClosure`.

```php
// Wrong
$mapped = \array_map(function ($item) {
    return $item->id();
}, $items);

// Right
$mapped = \array_map(static function ($item) {
    return $item->id();
}, $items);
```

## Class Structure Ordering

The project enforces a strict member ordering via
`SlevomatCodingStandard.Classes.ClassStructure`. Every class must arrange
its members in this sequence:

1. **Trait `use` statements**
2. **Enum cases** (if applicable)
3. **Public constants**
4. **Other constants** (protected, private)
5. **Properties** (all visibilities)
6. **Constructor**
7. **PHPUnit setUp / @before methods** (in test classes)
8. **All public methods**
9. **All other methods** (protected, private)
10. **Magic methods** (`__toString`, `__get`, etc.)

Getting this wrong produces a `ClassStructure` error. Typical mistake:
putting a private helper method above a public method.

## Return Type Hints

Return type hints are required on all methods and functions.
Enforced by `SlevomatCodingStandard.TypeHints.ReturnTypeHint`.

## Documentation Rules

The project **disables** most mandatory docblock rules. You do NOT need:
- Class docblocks (`Drupal.Commenting.ClassComment.Missing` is off)
- Function docblocks (`Drupal.Commenting.FunctionComment.Missing` is off)
- File docblocks (`Drupal.Commenting.FileComment.Missing` is off)
- Variable comments (`Drupal.Commenting.VariableComment.Missing` is off)

Add docblocks when they provide genuine value — complex parameters, non-obvious
return types, usage examples. Avoid useless `{@inheritdoc}` comments (flagged
by `SlevomatCodingStandard.Commenting.UselessInheritDocComment`).

When you do write docblocks for methods that **override a parent**, use `@phpstan-param`
and `@phpstan-return` instead of `@param`/`@return` to avoid conflicting with the
parent's documentation. See the PHPStan section for details.

## Blacklisted Debug Statements

The pre-commit hook blocks these patterns via `git_blacklist`:

- `var_dump(...)` / `die(...)` / `dpm(...)` / `error_log(...)`
- `var_export(...)` / `print_r($var)` (though `print_r($var, TRUE)` is allowed)
- `console.log(...)`

Never leave debug statements in committed code.

---

## PHPStan Level 8

PHPStan runs at level 8 with `phpstan-strict-rules`, `phpstan-deprecation-rules`,
and `mglaman/phpstan-drupal`. This means:

- All parameters and return types must be fully typed
- No `mixed` leaking without explicit handling
- Deprecated API usage is flagged
- Drupal-specific patterns (services, hooks, entity API) are understood

### Type Annotations for Inherited Methods

When overriding a method from Drupal core or a contrib base class, use
`@phpstan-param` and `@phpstan-return` rather than plain `@param`/`@return`.
This tells PHPStan the precise types without conflicting with the parent's
docblock.

This is critical for:
- Plugin constructors extending `PluginBase`, `ProcessPluginBase`, etc.
- `create()` factory methods from `ContainerFactoryPluginInterface`
- `getDerivativeDefinitions()` from `DeriverInterface`
- Any overridden method where you need tighter types than the parent declares

```php
/**
 * {@inheritdoc}
 *
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
```

### Parameter Contravariance

When PHPStan reports `method.childParameterType`, the child method has a more
specific parameter type than the parent. Fix it with `@phpstan-param` using the
parent's broader type:

```php
/**
 * {@inheritdoc}
 *
 * @phpstan-param array<array-key, mixed> $base_plugin_definition
 */
public function getDerivativeDefinitions($base_plugin_definition): array {
```

### Return Type: `static` vs Concrete

When a method returns `new ClassName()` but the parent's return type is `static`,
PHPStan flags `return.type`. Fix by making the class `final` and using the
concrete class name as the return type:

```php
final class MyPlugin extends ProcessPluginBase implements ContainerFactoryPluginInterface {
    public static function create(
        ContainerInterface $container,
        array $configuration,
        $plugin_id,
        $plugin_definition,
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

Use `final` on any class that isn't explicitly designed to be extended. This is
the project convention for leaf services, hook classes, plugins, and handlers.

### Type Narrowing with Assertions

When working with Drupal's loosely-typed APIs, use `assert()` to narrow types
rather than `@phpstan-ignore-next-line`:

```php
$storage = $this->entityTypeManager->getStorage('node');
assert($storage instanceof NodeStorageInterface);
$node = $storage->load($nid);
```

### Null Safety

Always handle nullable returns explicitly:

```php
$statement = $query->execute();
if ($statement === NULL) {
    return [];
}
$results = $statement->fetchAll();
```

### Array Type Annotations

PHPStan level 8 requires specific array types — plain `array` without type
parameters triggers "no value type specified in iterable type array". Always
specify what the array contains:

```php
/** @var array<string, mixed> */
/** @var list<int> */
/** @var array<int, array{id: int, name: string}> */
```

For simple one-dimensional arrays:

```php
/**
 * @phpstan-param array<array-key, string> $items
 */
public function process(array $items): void {
```

For complex nested structures (like Drupal render arrays or form structures),
you can describe the shape precisely:

```php
/**
 * @phpstan-param array{data?: string|array{preview?: string|array{'#access'?: bool}}} $variables
 */
```

Or use the escape hatch when the structure is too complex to describe:

```php
/**
 * @phpstan-param array<array-key, mixed> $variables
 */
```

When you find yourself writing deeply nested array shape annotations, consider
whether a DTO class would be clearer. Classes give you actual type enforcement
rather than just documentation.

### Strict Comparisons and Boolean Conditions

PHPStan strict rules ban several loose PHP patterns:

**No `empty()`** — it's a loose comparison that conflates `null`, `false`, `0`,
`''`, and `[]`. Use explicit checks instead:

```php
// Wrong
if (empty($variable)) {

// Right — check what you actually mean
if ($variable === NULL || $variable === '') {
```

**Only booleans in `if` conditions** — a `mixed` or `string` in an `if` won't
pass. Be explicit:

```php
// Wrong
if ($variables['data']) {

// Right
if (isset($variables['data']) && $variables['data'] !== '') {
```

**`in_array()` requires strict mode** — always pass `true` as the third
parameter. Same for `array_search()`, `array_keys()` with a search value,
and `base64_decode()`:

```php
// Wrong
\in_array($value, $allowed);

// Right
\in_array($value, $allowed, true);
```

**No short ternary (`?:`)** — it uses loose boolean evaluation. Use the null
coalesce operator `??` or a full ternary with an explicit condition:

```php
// Wrong (loose boolean coercion)
$name = $input ?: 'default';

// Right (null coalesce — strict null check)
$name = $input ?? 'default';

// Right (explicit condition when you need non-null, non-empty)
$name = ($input !== '' && $input !== NULL) ? $input : 'default';
```

### Contravariance and Covariance

PHPStan enforces the Liskov Substitution Principle:

- **Parameters are contravariant**: a child class method can accept a broader
  type than the parent, but never a narrower one. If the parent takes `Animal`,
  the child cannot restrict to `Mammal`.
- **Return types are covariant**: a child class method can return a narrower
  type than the parent, but never a broader one. If the parent returns `Book`,
  the child cannot widen to `Product`.

In practice this most often appears with Drupal plugin base classes where the
parent uses `array` and you want `array<string, mixed>`. Fix it with
`@phpstan-param` using the parent's broader type (see "Parameter Contravariance"
above).

### Parent Constructor Calls

When extending a class, the child constructor must call `parent::__construct()`.
A common trap with Drupal plugin attributes: if you declare a parameter as
`public readonly` (constructor promotion) and also pass it to the parent, you
get "Readonly property is already assigned." The fix is to drop the promotion
on the parameter that's forwarded to the parent:

```php
// Wrong — $id is promoted AND passed to parent
final class MyAttribute extends AttributeBase {
    public function __construct(
        public readonly string $id,  // promoted to property
        public readonly ?TranslatableMarkup $label,
    ) {
        parent::__construct($id);  // Error: $id already assigned
    }
}

// Right — $id is NOT promoted, just forwarded
final class MyAttribute extends AttributeBase {
    public function __construct(
        string $id,  // plain parameter, not promoted
        public readonly ?TranslatableMarkup $label,
    ) {
        parent::__construct($id);
    }
}
```

### @SuppressWarnings Syntax

When you need `@SuppressWarnings(PHPMD.UnusedFormalParameter)` in a docblock,
always use double quotes around the value. Without quotes, PHPStan parses the
dot as unexpected syntax and reports `phpDoc.parseError`:

```php
// Wrong — causes PHPStan phpDoc.parseError
/**
 * @SuppressWarnings(PHPMD.UnusedFormalParameter)
 */

// Right
/**
 * @SuppressWarnings("PHPMD.UnusedFormalParameter")
 */
```

### Common PHPStan Errors Reference

For a comprehensive catalog of PHPStan level 8 + strict rules errors with
detailed examples and fixes, see `references/phpstan-common-errors.md`.
Consult that reference when you encounter a specific PHPStan error you're
unsure how to fix.

---

## PHPMD Rules

PHPMD checks code complexity and design. The project uses all rulesets
except `cleancode`, with some customized thresholds.

### Complexity Limits

| Metric                   | Limit         | What it means                      |
|--------------------------|---------------|------------------------------------|
| Cyclomatic complexity    | 10 (default)  | Max branches/conditions per method |
| NPath complexity         | 200 (default) | Max execution paths per method     |
| Too many fields          | 18            | Max properties per class           |
| Too many public methods  | 12            | (ignoring get/set/is prefixes)     |
| Coupling between objects | 20            | Max unique classes referenced      |
| Number of children       | 25            | Max classes extending this one     |

When a method's complexity exceeds the limit, **refactor** — don't suppress.
Extract private helper methods, use early returns, apply guard clauses:

```php
// Instead of one method with CC=15:
public function transform($value, MigrateExecutableInterface $migrate_executable, Row $row, string $destination_property): mixed {
    $data = $this->extractData($row);

    return $this->buildResult($data);
}

private function extractData(Row $row): array {
    // focused extraction logic
}

private function buildResult(array $data): mixed {
    // focused building logic
}
```

### Naming Rules

| Rule                     | Constraint                                                                        |
|--------------------------|-----------------------------------------------------------------------------------|
| Short method name        | Minimum 2 characters                                                              |
| Long class name          | Maximum 60 characters (subtracting Controller/Service/Interface/Manager suffixes) |
| Short/Long variable name | **Not enforced** (excluded)                                                       |
| CamelCase parameters     | **Not enforced by PHPMD** (excluded) — but snake_case is required (see below)     |
| CamelCase variables      | **Not enforced by PHPMD** (excluded) — but snake_case is required (see below)     |

### Variable and Parameter Naming — snake_case Required

PHPMD does not enforce a naming convention for variables and parameters (the
CamelCase rules are excluded). **This project requires snake_case** for:

- **Local variables**: `$my_variable`, `$node_ids`, `$field_value`
- **Function and method parameters**: `$entity_type`, `$destination_property`

**Class properties stay camelCase** — this includes constructor-promoted
properties injected via dependency injection:

```php
// ✅ Correct — properties are camelCase, local vars and params are snake_case
final class NodeProcessor {

    public function __construct(
        private readonly EntityTypeManagerInterface $entityTypeManager,
        private readonly LoggerInterface $logger,
    ) {}

    public function process(string $bundle_name, int $batch_size): void {
        $node_storage = $this->entityTypeManager->getStorage('node');
        $node_ids = $node_storage->getQuery()
            ->accessCheck(FALSE)
            ->condition('type', $bundle_name)
            ->range(0, $batch_size)
            ->execute();

        foreach ($node_ids as $node_id) {
            $this->logger->info('Processing node @id', ['@id' => $node_id]);
        }
    }

}

// ❌ Wrong — camelCase local variables and parameters
final class NodeProcessor {

    public function process(string $bundleName, int $batchSize): void {
        $nodeStorage = $this->entityTypeManager->getStorage('node');
        $nodeIds = $nodeStorage->getQuery()
            ->accessCheck(FALSE)
            ->condition('type', $bundleName)
            ->range(0, $batchSize)
            ->execute();

        foreach ($nodeIds as $nodeId) {
            $this->logger->info('Processing node @id', ['@id' => $nodeId]);
        }
    }

}
```

**Edge cases:**

- Single-word variables need no underscore: `$node`, `$value`, `$result`
- Loop counters are fine as single letters: `$i`, `$k`, `$v`
- Variables matching Drupal core interface signatures keep whatever case
  the interface uses (e.g., `$plugin_id`, `$plugin_definition`)

### Unused Code

- Unused local variables are flagged, **except** in foreach loops
- Unused private methods and properties are flagged
- Unused formal parameters: use `@SuppressWarnings("PHPMD.UnusedFormalParameter")`
  only when the parameter is required by a hook or interface signature you cannot
  change. This is the one suppression that is routinely acceptable.

---

## CSpell

CSpell checks spelling in identifiers, comments, and string literals.
Minimum word length is 4 characters. Language is en-US with Italian dictionary.

### Handling Unknown Words

When you introduce a new technical term, acronym, or domain-specific word that
CSpell would flag, add it to the project dictionary:

**File:** `src/drupal/project-dictionary.txt`

Add one word per line. Keep it alphabetically sorted.

Common categories of words to add:
- Drupal contrib module names (`metatag`, `pathauto`, `linkit`)
- External service names and acronyms
- Domain-specific Italian terms
- API endpoint names and technical jargon

The firestarter platform dictionary already includes: `behat`, `cex`, `cim`,
`drush`, `firestarter`, `langcode`, `metatag`, `oembed`, `renderable`,
`sparkfabrik`, `yamls`, and a few others.

---

## Project Code Patterns

The project follows specific conventions for different class types. Matching
these patterns ensures consistency and avoids QA issues.

### Hook Classes (Drupal 11 style)

Prefer OOP hooks with `#[Hook]` attributes over procedural `.module` functions.
Hook classes live in `src/Hook/` and are registered as autowired services.

```php
<?php

declare(strict_types=1);

namespace Drupal\my_module\Hook;

use Drupal\Core\Entity\EntityInterface;
use Drupal\Core\Hook\Attribute\Hook;
use Drupal\Core\Session\AccountInterface;
use Drupal\Core\StringTranslation\StringTranslationTrait;

final readonly class NodeHooks {

    use StringTranslationTrait;

    public function __construct(
        private MyServiceInterface $myService,
    ) {}

    #[Hook('entity_access')]
    public function checkAccess(
        EntityInterface $entity,
        string $operation,
        AccountInterface $account,
    ): AccessResultInterface {
        // implementation

        return AccessResult::neutral();
    }

}
```

Key points:
- `final readonly class` when no mutable state
- Constructor promotion with `private readonly`
- One blank line before `return`
- Trailing commas everywhere

### Services and Dependency Injection

All `*.services.yml` files use autowiring:

```yaml
services:
  _defaults:
    autoconfigure: true
    autowire: true

  Drupal\my_module\Hook\NodeHooks: ~

  Drupal\my_module\Infrastructure\Persistence\Repository\NodeRepository: ~
  Drupal\my_module\Entity\NodeRepositoryInterface:
    alias: Drupal\my_module\Infrastructure\Persistence\Repository\NodeRepository
```

For classes that need explicit service wiring (named services, logger channels):

```php
public function __construct(
    #[Autowire(service: 'logger.channel.my_module')]
    private readonly LoggerInterface $logger,
) {}
```

### Migration Process Plugins

```php
<?php

declare(strict_types=1);

namespace Drupal\my_module\Plugin\migrate\process;

use Drupal\Core\Database\Connection;
use Drupal\Core\Plugin\ContainerFactoryPluginInterface;
use Drupal\migrate\Attribute\MigrateProcess;
use Drupal\migrate\MigrateExecutableInterface;
use Drupal\migrate\ProcessPluginBase;
use Drupal\migrate\Row;
use Symfony\Component\DependencyInjection\ContainerInterface;

#[MigrateProcess('my_process')]
final class MyProcess extends ProcessPluginBase implements ContainerFactoryPluginInterface {

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

    /**
     * @phpstan-param array<string, mixed> $configuration
     */
    public static function create(
        ContainerInterface $container,
        array $configuration,
        $plugin_id,
        $plugin_definition,
    ): MyProcess {
        return new MyProcess(
            $configuration,
            $plugin_id,
            $plugin_definition,
            $container->get('database'),
        );
    }

    /**
     * @phpstan-return string|list<array{id: int, revision_id: int}>
     */
    public function transform(
        mixed $value,
        MigrateExecutableInterface $migrate_executable,
        Row $row,
        string $destination_property,
    ): mixed {
        // implementation

        return $value;
    }

}
```

### Symfony Messenger Handlers

```php
<?php

declare(strict_types=1);

namespace Drupal\my_module\Messenger;

use Symfony\Component\DependencyInjection\Attribute\Autowire;
use Symfony\Component\Messenger\Attribute\AsMessageHandler;

#[AsMessageHandler]
final readonly class MyMessageHandler {

    public function __construct(
        #[Autowire(service: 'logger.channel.my_module')]
        private LoggerInterface $logger,
        private MyRepositoryInterface $repository,
    ) {}

    public function __invoke(MyMessage $message): void {
        // implementation
    }

}
```

### Block Plugins

```php
<?php

declare(strict_types=1);

namespace Drupal\my_module\Plugin\Block;

use Drupal\Core\Block\Attribute\Block;
use Drupal\Core\Block\BlockBase;
use Drupal\Core\Plugin\ContainerFactoryPluginInterface;
use Drupal\Core\StringTranslation\TranslatableMarkup;
use Symfony\Component\DependencyInjection\ContainerInterface;

#[Block(
    id: 'my_block',
    admin_label: new TranslatableMarkup('My Block'),
)]
final class MyBlock extends BlockBase implements ContainerFactoryPluginInterface {

    /**
     * @phpstan-param array<string, mixed> $configuration
     * @phpstan-param string $plugin_id
     * @phpstan-param mixed $plugin_definition
     */
    public function __construct(
        array $configuration,
        $plugin_id,
        $plugin_definition,
        private readonly EntityTypeManagerInterface $entityTypeManager,
    ) {
        parent::__construct($configuration, $plugin_id, $plugin_definition);
    }

    /**
     * @phpstan-param array<string, mixed> $configuration
     */
    public static function create(
        ContainerInterface $container,
        array $configuration,
        $plugin_id,
        $plugin_definition,
    ): MyBlock {
        return new MyBlock(
            $configuration,
            $plugin_id,
            $plugin_definition,
            $container->get('entity_type.manager'),
        );
    }

    /**
     * @return array<string, mixed>
     */
    public function build(): array {
        return [
            '#markup' => $this->t('Hello'),
        ];
    }

}
```

### Repository Pattern

The project uses an infrastructure layer with interface aliasing:

```php
<?php

declare(strict_types=1);

namespace Drupal\my_module\Infrastructure\Persistence\Repository;

use Drupal\Core\Entity\EntityTypeManagerInterface;

final readonly class NodeRepository implements NodeRepositoryInterface {

    public function __construct(
        private EntityTypeManagerInterface $entityTypeManager,
    ) {}

    /**
     * @return list<int>
     */
    public function findPublishedByBundle(string $bundle): array {
        $storage = $this->entityTypeManager->getStorage('node');
        $ids = $storage->getQuery()
            ->accessCheck(FALSE)
            ->condition('type', $bundle)
            ->condition('status', 1)
            ->execute();

        return \array_values(\array_map('\intval', $ids));
    }

}
```

---

## Quick Checklist

Before writing any PHP, mentally run through this list:

1. `declare(strict_types=1);` at the top
2. `use` statements sorted alphabetically
3. Global functions prefixed with `\` — `\count()`, `\array_map()`, etc.
4. Trailing commas on multi-line calls, declarations, and arrays
5. Blank line before `return` and `continue`
6. Class members in correct order: traits, constants, properties, constructor, public methods, other methods, magic methods
7. Return type hints on every method
8. `@phpstan-param` / `@phpstan-return` for overridden methods
9. `final` on classes not designed for extension
10. `assert()` for type narrowing, not `@phpstan-ignore`
11. Method complexity under 10 — extract helpers if needed
12. No debug statements (`var_dump`, `die`, `error_log`, etc.)
13. New technical terms added to `src/drupal/project-dictionary.txt`
14. `static` keyword on closures that don't use `$this`
15. Null-safe operator `?->` where applicable
16. No `empty()` — use explicit comparisons (`=== null`, `=== ''`, `=== []`)
17. Only booleans in `if` conditions — no bare `if ($variable)`
18. `\in_array($v, $arr, true)` — always pass strict `true` as third param
19. No short ternary `?:` — use `??` or full ternary with explicit condition
20. Array params always typed — `array<array-key, mixed>` at minimum, not bare `array`
21. `@SuppressWarnings("PHPMD.X")` with double quotes (not unquoted)
22. Don't promote constructor params that are forwarded to `parent::__construct()`
23. Local variables and parameters use `snake_case` — class properties stay
    `camelCase`
