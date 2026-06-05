# Entities, Aggregates, and Factories in Drupal

## Table of Contents

1. [Rich Entities vs Anemic Entities](#rich-entities-vs-anemic-entities)
2. [Identity in Drupal](#identity-in-drupal)
3. [Making Drupal Entities Rich](#making-drupal-entities-rich)
4. [Aggregates](#aggregates)
5. [Aggregate Design Rules](#aggregate-design-rules)
6. [Factories](#factories)
7. [Concurrency and Consistency](#concurrency-and-consistency)

---

## Rich Entities vs Anemic Entities

In DDD, an Entity has identity, state, and **behavior**. The entity is
responsible for protecting its own invariants — the business rules that must
always be true.

### The Anemic Model Problem

Drupal's architecture makes it easy to fall into the Anemic Domain Model:
entities become data containers, and all logic lives in hooks, services, or
form handlers.

```php
// ANEMIC (common in Drupal, but problematic for complex domains):
// Logic scattered across hooks and services
function my_module_entity_presave(EntityInterface $entity): void {
  if ($entity->bundle() === 'order') {
    if ($entity->get('field_status')->value === 'accepted') {
      $entity->set('field_accepted_at', date('Y-m-d'));
      $entity->set('field_accepted_by', \Drupal::currentUser()->id());
    }
  }
}

// RICH (DDD approach):
// Logic lives on the entity itself
class Order extends ContentEntityBase implements OrderInterface {

  public function accept(AccountInterface $acceptedBy): void {
    if ($this->isAccepted()) {
      throw new OrderAlreadyAcceptedException($this->id());
    }
    $this->set('field_status', 'accepted');
    $this->set('field_accepted_at', (new \DateTimeImmutable())->format('Y-m-d'));
    $this->set('field_accepted_by', $acceptedBy->id());
  }

  public function isAccepted(): bool {
    return $this->get('field_status')->value === 'accepted';
  }

}
```

### When to Choose Which

| Approach                    | When to Use                                                                                                                                           |
| --------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Anemic** (Drupal default) | Simple CRUD, content types with no business logic beyond display                                                                                      |
| **Rich** (DDD)              | Business rules exist (state machines, calculations, validations that go beyond field constraints), complex entity interactions, external integrations |

You don't need to make every content type rich. A "Basic Page" with a title
and body is fine as anemic. An "Order" with statuses, deadlines, and approval
workflows benefits from rich domain methods.

---

## Identity in Drupal

DDD entities are identified by a unique identity that persists over time. Drupal
already handles this:

| DDD Concept           | Drupal Equivalent    | Notes                                     |
| --------------------- | -------------------- | ----------------------------------------- |
| Entity ID             | `$entity->id()`      | Auto-increment integer (surrogate ID)     |
| UUID                  | `$entity->uuid()`    | Universally unique, used for content sync |
| Identity Value Object | Not typically needed | Drupal's built-in ID system is sufficient |

**When you might want typed IDs:** If you're building a complex domain where
different entity types must never be confused (passing a node ID where a term
ID is expected), typed ID Value Objects add compile-time safety:

```php
final readonly class OrderId {
  private function __construct(private string $id) {}

  public static function fromEntity(OrderInterface $entity): self {
    return new self((string) $entity->id());
  }

  public static function fromString(string $id): self {
    return new self($id);
  }

  public function toString(): string {
    return $this->id;
  }

  public function equals(self $other): bool {
    return $this->id === $other->id;
  }
}
```

For most Drupal projects, using `string $entityId` with clear parameter naming
is sufficient. Typed IDs are worth the overhead when you have many entity types
that interact and type confusion is a real risk.

---

## Making Drupal Entities Rich

### Custom Content Entity with Domain Methods

```php
<?php

declare(strict_types=1);

namespace Drupal\my_module\Entity\Enrollment;

use Drupal\Core\Entity\ContentEntityBase;
use Drupal\Core\Entity\EntityTypeInterface;
use Drupal\Core\Field\BaseFieldDefinition;

#[ContentEntityType(
  id: 'enrollment',
  label: new TranslatableMarkup('Enrollment'),
  // ... handlers, keys, etc.
)]
class Enrollment extends ContentEntityBase implements EnrollmentInterface {

  /**
   * Enroll a student in a course.
   *
   * This is a Factory Method — creates a valid enrollment
   * with all invariants satisfied.
   *
   * @throws \Drupal\my_module\Exception\EnrollmentCapacityReachedException
   */
  public static function create(
    array $values = [],
  ): static {
    // Use parent::create for Drupal compatibility
    return parent::create($values);
  }

  /**
   * Confirm the enrollment after payment verification.
   *
   * @throws \Drupal\my_module\Exception\EnrollmentAlreadyConfirmedException
   */
  public function confirm(): void {
    if ($this->isConfirmed()) {
      throw new EnrollmentAlreadyConfirmedException(
        (string) $this->id()
      );
    }
    $this->set('status', 'confirmed');
    $this->set('confirmed_at', (new \DateTimeImmutable())->format('Y-m-d\TH:i:s'));
  }

  /**
   * Cancel the enrollment with a reason.
   */
  public function cancel(string $reason): void {
    if ($this->isCancelled()) {
      return; // Idempotent
    }
    $this->set('status', 'cancelled');
    $this->set('cancellation_reason', $reason);
    $this->set('cancelled_at', (new \DateTimeImmutable())->format('Y-m-d\TH:i:s'));
  }

  public function isConfirmed(): bool {
    return $this->get('status')->value === 'confirmed';
  }

  public function isCancelled(): bool {
    return $this->get('status')->value === 'cancelled';
  }

  public function isPending(): bool {
    return $this->get('status')->value === 'pending';
  }

  /**
   * Business rule: enrollment can only be confirmed if pending.
   */
  public function canBeConfirmed(): bool {
    return $this->isPending();
  }

}
```

### Adapter Pattern for Contrib Entities

You can't modify Drupal core entities (Node, User, Term), but you can wrap
them with domain interfaces using the Adapter Pattern:

```php
// Domain interface — what the domain needs
interface TaggableContentInterface {
  public function getTags(): array;
  public function hasTag(string $tagId): bool;
}

// Adapter — wraps a Drupal Node to implement the domain interface
class NodeTaggableAdapter implements TaggableContentInterface {

  public function __construct(
    private readonly NodeInterface $node,
  ) {}

  public function getTags(): array {
    if (!$this->node->hasField('field_tags')) {
      return [];
    }
    return array_map(
      fn($item) => (string) $item->target_id,
      iterator_to_array($this->node->get('field_tags')),
    );
  }

  public function hasTag(string $tagId): bool {
    return in_array($tagId, $this->getTags(), TRUE);
  }

}
```

The Adapter pattern lets you add domain interfaces to entities you don't
control. The core Node knows nothing about your domain concept of "taggable
content"; the adapter adds that capability without modifying core.

---

## Aggregates

An Aggregate is a cluster of entities and value objects treated as a single
unit for data consistency. The **Aggregate Root** is the entry point — all
access to child entities goes through it.

### Drupal's Natural Aggregates

Drupal already has implicit aggregate patterns:

| Aggregate Root | Children           | Why It's an Aggregate                                                     |
| -------------- | ------------------ | ------------------------------------------------------------------------- |
| Node           | Paragraphs         | Paragraphs don't exist independently; they're saved/deleted with the node |
| Webform        | WebformSubmissions | Submissions belong to a specific form                                     |
| Menu           | MenuLinkContent    | Links exist within a menu structure                                       |
| Order          | LineItems          | Line items are meaningless without their order                            |

### When to Model Aggregates Explicitly

Model aggregates explicitly when you need to enforce **business invariants**
across the root and its children:

```php
class Forum extends ContentEntityBase implements ForumInterface {

  private const MAX_POSTS_PER_DAY = 50;

  /**
   * Publish a post within this forum.
   *
   * The forum is the Aggregate Root — it controls post creation
   * and enforces the daily posting limit.
   */
  public function publishPost(
    string $authorId,
    string $content,
    PostRepositoryInterface $postRepository,
  ): Post {
    if ($this->isClosed()) {
      throw new ForumClosedException((string) $this->id());
    }

    $todayCount = $postRepository->countByForumAndDate(
      (string) $this->id(),
      new \DateTimeImmutable('today'),
    );

    if ($todayCount >= self::MAX_POSTS_PER_DAY) {
      throw new DailyPostLimitReachedException(self::MAX_POSTS_PER_DAY);
    }

    return Post::create([
      'forum_id' => $this->id(),
      'author_id' => $authorId,
      'content' => $content,
    ]);
  }

}
```

---

## Aggregate Design Rules

From Vaughn Vernon's "Effective Aggregate Design" (cited in DDD in PHP):

### Rule 1: Protect Business Invariants Inside Aggregate Boundaries

An invariant is a business rule that must always be true. The aggregate is
responsible for enforcing its invariants — no external code should bypass the
aggregate root.

**In Drupal:** Use entity methods for rules that apply to the entity and its
children. Use `hook_entity_presave` as a safety net, not as the primary
enforcement mechanism.

### Rule 2: Design Small Aggregates

Prefer small aggregates — ideally the root entity plus value objects. Large
aggregates cause performance problems and concurrency conflicts.

**In Drupal:** Don't try to make a single node the aggregate root for dozens of
referenced entities. If a paragraph references other paragraphs, the "aggregate"
is the immediate parent-child relationship, not the entire tree.

### Rule 3: Reference Other Aggregates by Identity Only

Don't hold object references to other aggregates. Use IDs.

```php
// GOOD: reference by ID
class Order extends ContentEntityBase {
  // field_customer stores a target_id (integer reference)
  public function customerId(): string {
    return (string) $this->get('field_customer')->target_id;
  }
}

// BAD: loading the entire customer aggregate
class Order extends ContentEntityBase {
  public function customer(): Customer {
    return $this->get('field_customer')->entity;
    // This loads the customer, creating a tight coupling
  }
}
```

**Drupal's entity_reference fields already follow this rule** — they store
target IDs, not loaded objects. The `->entity` property performs lazy loading,
which is convenient but can lead to unintended coupling. In domain logic, prefer
using `->target_id` and loading through a repository when needed.

### Rule 4: Use Eventual Consistency Across Aggregates

If a business rule spans two aggregates, use domain events and eventual
consistency rather than trying to modify both in a single transaction.

```php
// When an order is placed, update the customer's order count.
// Don't do this synchronously — use an event.

class Order extends ContentEntityBase {
  public function place(): void {
    $this->set('status', 'placed');
    // The event will be dispatched after save
    // A listener will update the customer's stats asynchronously
  }
}

// In the Application Service:
$order->place();
$this->orderRepository->save($order);
$this->eventDispatcher->dispatch(new OrderWasPlaced($order->id()));
```

---

## Factories

### Factory Method on Aggregate Root

When creating a child entity requires checking the root's invariants, use
a factory method on the root:

```php
class Course extends ContentEntityBase {

  public function createEnrollment(string $studentId): Enrollment {
    if (!$this->isOpen()) {
      throw new CourseNotOpenException((string) $this->id());
    }
    if ($this->isFull()) {
      throw new CourseFullException((string) $this->id());
    }
    return Enrollment::create([
      'course_id' => $this->id(),
      'student_id' => $studentId,
      'status' => 'pending',
    ]);
  }

}
```

### Factory as Domain Service

When creation involves multiple aggregates or external data, use a mapper
or factory service:

```php
final readonly class ExternalProductMapper {

  public function __construct(
    private ProductRepositoryInterface $products,
    private CategoryRepositoryInterface $categories,
  ) {}

  /**
   * Map a DTO from an external API to a Product entity.
   *
   * Creates new or updates existing based on external ID.
   */
  public function map(ExternalProductDto $dto): ProductInterface {
    $existing = $this->products->loadByExternalId($dto->id);

    if ($existing !== NULL) {
      return $this->updateExisting($existing, $dto);
    }

    return $this->createNew($dto);
  }

}
```

This pattern is common when integrating with external APIs — the mapper
translates external DTOs to domain entities, handling both creation and updates.

### Test Data Builders

For tests, use the Builder pattern to create entities with sensible defaults:

```php
class EnrollmentBuilder {

  private string $studentId = 'student-1';
  private string $courseId = 'course-1';
  private string $status = 'pending';

  public function withStudent(string $id): self {
    $clone = clone $this;
    $clone->studentId = $id;
    return $clone;
  }

  public function confirmed(): self {
    $clone = clone $this;
    $clone->status = 'confirmed';
    return $clone;
  }

  public function build(): Enrollment {
    return Enrollment::create([
      'student_id' => $this->studentId,
      'course_id' => $this->courseId,
      'status' => $this->status,
    ]);
  }

}

// Usage in tests:
$enrollment = (new EnrollmentBuilder())
  ->withStudent('student-42')
  ->confirmed()
  ->build();
```

---

## Concurrency and Consistency

Drupal does not provide built-in optimistic or pessimistic locking for content
entities. When concurrent modifications are a risk, consider these strategies:

### Optimistic Locking (Version Field)

Add a `version` base field that increments on each save. Check it before saving:

```php
// In the entity's base field definitions:
$fields['version'] = BaseFieldDefinition::create('integer')
  ->setLabel(new TranslatableMarkup('Version'))
  ->setDefaultValue(0);

// In the repository:
public function save(OrderInterface $order): void {
  $currentVersion = $order->get('version')->value;
  // Reload from storage to check version hasn't changed
  $stored = $this->getStorage()->load($order->id());

  if ($stored && (int) $stored->get('version')->value !== (int) $currentVersion) {
    throw new OptimisticLockException(
      sprintf('Order %s was modified concurrently', $order->id())
    );
  }

  $order->set('version', $currentVersion + 1);
  $order->save();
}
```

### Pessimistic Locking (Database Lock)

For critical sections, use Drupal's database transaction with a SELECT FOR
UPDATE:

```php
$transaction = $this->database->startTransaction();
try {
  // Lock the row
  $this->database->query(
    'SELECT id FROM {my_entity} WHERE id = :id FOR UPDATE',
    [':id' => $entityId]
  );

  $entity = $this->getStorage()->load($entityId);
  // ... modify ...
  $entity->save();
}
catch (\Exception $e) {
  $transaction->rollBack();
  throw $e;
}
```

### When to Use

- **Optimistic locking:** Content that is rarely edited concurrently but needs
  protection (orders, enrollments). Low overhead.
- **Pessimistic locking:** Critical data with high contention (inventory counts,
  seat reservations). Higher overhead but guarantees consistency.
- **Neither:** Content edited by a single admin at a time (most Drupal content).
  Drupal's built-in "content lock" module may suffice.
