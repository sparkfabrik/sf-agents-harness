# Value Objects in Drupal

## Table of Contents

1. [What Is a Value Object](#what-is-a-value-object)
2. [When to Use Value Objects in Drupal](#when-to-use-value-objects-in-drupal)
3. [Anatomy of a Value Object](#anatomy-of-a-value-object)
4. [Persistence Strategies](#persistence-strategies)
5. [Common Value Object Patterns](#common-value-object-patterns)
6. [Testing Value Objects](#testing-value-objects)

---

## What Is a Value Object

A Value Object is an immutable object defined by its attributes rather than
an identity. Two Value Objects with the same data are considered equal — like
two $10 bills are interchangeable regardless of serial number.

Six characteristics (from Eric Evans / DDD in PHP):

1. **Describes** a thing — it measures, quantifies, or describes a domain concept
2. **Immutable** — once created, it cannot be changed
3. **Conceptual Whole** — groups related attributes into a single unit
4. **Value Equality** — compared by content, not reference
5. **Replaceable** — changed by replacing the whole object
6. **Side-Effect-Free** — operations return new instances, never modify `$this`

## When to Use Value Objects in Drupal

Use a Value Object when you find yourself:

- Passing related primitives together (`$amount` + `$currency`, `$start` + `$end`)
- Validating the same format in multiple places (email, URL, ISO code)
- Performing calculations that involve multiple fields (money arithmetic)
- Wanting to prevent invalid states (negative prices, malformed codes)

**Skip Value Objects when:**

- The value is a simple scalar with no validation beyond Drupal's field constraints
- The value is only used in one place with no behavior
- You're modeling a Drupal config form with simple text/boolean fields

### Drupal Fields vs PHP Value Objects

Drupal fields already provide storage-level typing and constraints. PHP Value
Objects add **domain-level** guarantees on top:

| Concern               | Drupal Field                | PHP Value Object             |
| --------------------- | --------------------------- | ---------------------------- |
| Storage type          | Yes (varchar, int, etc.)    | No (in-memory only)          |
| Required/optional     | Yes                         | Yes (via constructor)        |
| Format validation     | Limited (maxlength, etc.)   | Full (regex, business rules) |
| Behavior (methods)    | No                          | Yes                          |
| Immutability          | No (fields are mutable)     | Yes                          |
| Testable in isolation | No (needs Drupal bootstrap) | Yes (pure PHP)               |

The two work together: Value Objects enforce rules in your domain code, and
Drupal fields handle persistence.

---

## Anatomy of a Value Object

### Basic Pattern

```php
<?php

declare(strict_types=1);

namespace Drupal\my_module\Entity\ValueObject;

/**
 * Represents a postal code with country-specific validation.
 *
 * Immutable. Self-validating. Two PostalCode objects with
 * the same code and country are considered equal.
 */
final readonly class PostalCode {

  /**
   * Private constructor — use the static factory method.
   *
   * @param string $code
   *   The postal code.
   * @param string $countryCode
   *   The ISO 3166-1 alpha-2 country code.
   */
  private function __construct(
    private string $code,
    private string $countryCode,
  ) {}

  /**
   * Create a PostalCode for a given country.
   *
   * @param string $code
   *   The postal code string.
   * @param string $countryCode
   *   Two-letter ISO country code (e.g. "US", "IT", "DE").
   *
   * @return self
   *   A new PostalCode instance.
   *
   * @throws \InvalidArgumentException
   *   If the code does not match the country format.
   */
  public static function fromString(string $code, string $countryCode): self {
    $countryCode = strtoupper($countryCode);
    $pattern = match ($countryCode) {
      'US' => '/^\d{5}(-\d{4})?$/',
      'IT' => '/^\d{5}$/',
      'DE' => '/^\d{5}$/',
      'GB' => '/^[A-Z]{1,2}\d[A-Z\d]?\s?\d[A-Z]{2}$/i',
      default => '/^.{2,10}$/',
    };
    if (!preg_match($pattern, $code)) {
      throw new \InvalidArgumentException(
        sprintf('"%s" is not a valid postal code for %s', $code, $countryCode)
      );
    }
    return new self($code, $countryCode);
  }

  public function code(): string {
    return $this->code;
  }

  public function countryCode(): string {
    return $this->countryCode;
  }

  public function toString(): string {
    return sprintf('%s (%s)', $this->code, $this->countryCode);
  }

  /**
   * Value equality — two PostalCodes are equal if they represent
   * the same code in the same country.
   */
  public function equals(self $other): bool {
    return $this->code === $other->code
      && $this->countryCode === $other->countryCode;
  }

  public function __toString(): string {
    return $this->toString();
  }

}
```

### Key Design Decisions

**Private constructor + static factory methods:** This forces callers to go
through validation. You cannot create an invalid PostalCode.

**`final readonly class`:** PHP 8.2+ makes immutability automatic. All
properties are readonly, the class cannot be extended, and there are no setters.

**`equals()` method:** Value Objects compare by content, not by reference.
Always provide an `equals()` method for domain comparisons.

**Named constructors:** Use `fromString()`, `fromArray()`, `of()` etc.
to support different input formats while keeping validation centralized.

---

## Persistence Strategies

Value Objects live in PHP memory. To persist them, convert at the repository
boundary.

### Strategy 1: Embedded Value (Recommended for Queryable Data)

Flatten the Value Object into multiple Drupal field columns.

```php
// In the repository: entity → Value Object
public function loadProduct(string $id): Product {
  $entity = $this->getStorage()->load($id);
  $price = Money::of(
    (float) $entity->get('field_price_amount')->value,
    Currency::fromCode($entity->get('field_price_currency')->value),
  );
  return new Product($entity, $price);
}

// In the repository: Value Object → entity
public function save(Product $product): void {
  $entity = $product->entity();
  $entity->set('field_price_amount', $product->price()->amount());
  $entity->set('field_price_currency', $product->price()->currency()->code());
  $entity->save();
}
```

**Drupal mapping:** Each component maps to a separate Drupal field or field
property. Queryable via entity queries.

### Strategy 2: Serialized LOB (For Complex, Non-Queryable Data)

Store the Value Object as JSON in a single text field.

```php
// Serialize
$entity->set('field_metadata', json_encode($metadata->toArray()));

// Deserialize
$data = json_decode($entity->get('field_metadata')->value, TRUE);
$metadata = Metadata::fromArray($data);
```

**When to use:** Complex nested structures that you never query by (audit data,
configuration blobs, external API response snapshots).

**Caution:** You cannot query individual properties. Schema changes require
migration of stored JSON.

### Strategy 3: Custom Field Type (For Reusable Domain Types)

Create a Drupal field type that wraps a Value Object. This is the most
Drupal-native approach but requires more boilerplate.

```php
#[FieldType(
  id: 'money',
  label: new TranslatableMarkup('Money'),
  description: new TranslatableMarkup('Stores a monetary value.'),
)]
class MoneyFieldType extends FieldItemBase {

  public static function schema(FieldStorageDefinitionInterface $definition): array {
    return [
      'columns' => [
        'amount' => ['type' => 'numeric', 'precision' => 19, 'scale' => 4],
        'currency' => ['type' => 'varchar', 'length' => 3],
      ],
    ];
  }

  public function toMoney(): Money {
    return Money::of(
      (float) $this->get('amount')->getValue(),
      Currency::fromCode($this->get('currency')->getValue()),
    );
  }

}
```

**When to use:** The Value Object is used across multiple entity types and
benefits from having a reusable field type with widget and formatter.

---

## Common Value Object Patterns

### Money (Amount + Currency)

```php
final readonly class Money {

  private function __construct(
    private float $amount,
    private Currency $currency,
  ) {}

  public static function of(float $amount, Currency $currency): self {
    return new self($amount, $currency);
  }

  public function add(self $other): self {
    $this->guardSameCurrency($other);
    return new self($this->amount + $other->amount, $this->currency);
  }

  private function guardSameCurrency(self $other): void {
    if (!$this->currency->equals($other->currency)) {
      throw new CurrencyMismatchException($this->currency, $other->currency);
    }
  }

}
```

### EmailAddress

```php
final readonly class EmailAddress {

  private function __construct(
    private string $address,
  ) {}

  public static function fromString(string $address): self {
    if (!filter_var($address, FILTER_VALIDATE_EMAIL)) {
      throw new \InvalidArgumentException(
        sprintf('"%s" is not a valid email', $address)
      );
    }
    return new self(strtolower($address));
  }

  public function equals(self $other): bool {
    return $this->address === $other->address;
  }

  public function domain(): string {
    return substr($this->address, strpos($this->address, '@') + 1);
  }

}
```

### DateRange

```php
final readonly class DateRange {

  private function __construct(
    private \DateTimeImmutable $start,
    private \DateTimeImmutable $end,
  ) {}

  public static function between(
    \DateTimeImmutable $start,
    \DateTimeImmutable $end,
  ): self {
    if ($start >= $end) {
      throw new \InvalidArgumentException('Start must be before end');
    }
    return new self($start, $end);
  }

  public function contains(\DateTimeImmutable $date): bool {
    return $date >= $this->start && $date <= $this->end;
  }

  public function overlaps(self $other): bool {
    return $this->start < $other->end && $other->start < $this->end;
  }

  public function durationInDays(): int {
    return (int) $this->start->diff($this->end)->days;
  }

}
```

### OperationOutcome (Result Pattern)

A tri-state result value object — useful for operations that can succeed,
fail, or be skipped:

```php
final readonly class OperationOutcome {

  private function __construct(
    private string $status,
    private ?\Throwable $exception = NULL,
    private bool $retryable = FALSE,
  ) {}

  public static function succeeded(): self {
    return new self('succeeded');
  }

  public static function failed(\Throwable $e, bool $retryable = FALSE): self {
    return new self('failed', $e, $retryable);
  }

  public static function skipped(): self {
    return new self('skipped');
  }

  public function isSucceeded(): bool { return $this->status === 'succeeded'; }
  public function isFailed(): bool { return $this->status === 'failed'; }
  public function isRetryable(): bool { return $this->retryable; }

}
```

---

## Testing Value Objects

Value Objects are the easiest DDD building block to test — they are pure PHP
with no dependencies.

```php
class PostalCodeTest extends TestCase {

  public function testCreatesValidUsPostalCode(): void {
    $code = PostalCode::fromString('90210', 'US');
    $this->assertSame('90210', $code->code());
    $this->assertSame('US', $code->countryCode());
  }

  public function testCreatesValidUsZipPlusFour(): void {
    $code = PostalCode::fromString('90210-1234', 'US');
    $this->assertSame('90210-1234', $code->code());
  }

  public function testRejectsInvalidUsPostalCode(): void {
    $this->expectException(\InvalidArgumentException::class);
    PostalCode::fromString('ABCDE', 'US');
  }

  public function testValueEquality(): void {
    $a = PostalCode::fromString('90210', 'US');
    $b = PostalCode::fromString('90210', 'US');
    $c = PostalCode::fromString('10001', 'US');
    $this->assertTrue($a->equals($b));
    $this->assertFalse($a->equals($c));
  }

  public function testDifferentCountriesMeansNotEqual(): void {
    $us = PostalCode::fromString('12345', 'US');
    $de = PostalCode::fromString('12345', 'DE');
    $this->assertFalse($us->equals($de));
  }

  public function testImmutability(): void {
    $code = PostalCode::fromString('90210', 'US');
    $reflection = new \ReflectionClass($code);
    $this->assertTrue($reflection->isReadOnly());
  }

}
```

### Testing Persistence Conversion

```php
class MoneyPersistenceTest extends KernelTestBase {

  public function testRoundTrip(): void {
    $original = Money::of(99.99, Currency::fromCode('EUR'));

    // Simulate saving
    $entity = Node::create(['type' => 'product']);
    $entity->set('field_price_amount', $original->amount());
    $entity->set('field_price_currency', $original->currency()->code());

    // Simulate loading
    $loaded = Money::of(
      (float) $entity->get('field_price_amount')->value,
      Currency::fromCode($entity->get('field_price_currency')->value),
    );

    $this->assertTrue($original->equals($loaded));
  }

}
```
