# Services and Domain Events in Drupal

## Table of Contents

1. [The Three Service Types](#the-three-service-types)
2. [Domain Services](#domain-services)
3. [Application Services](#application-services)
4. [Domain Events](#domain-events)
5. [The Anemic Model Trap](#the-anemic-model-trap)
6. [Transactions](#transactions)

---

## The Three Service Types

DDD distinguishes three kinds of services. Understanding the difference is
critical for keeping logic in the right place.

| Type                       | Lives In             | Purpose                                            | Example                                      |
| -------------------------- | -------------------- | -------------------------------------------------- | -------------------------------------------- |
| **Domain Service**         | Domain layer         | Business logic that doesn't fit an entity          | `EnrollmentEligibilityChecker`               |
| **Application Service**    | Application layer    | Orchestrates use cases, coordinates domain objects | `PlaceOrderService`, form submit handlers    |
| **Infrastructure Service** | Infrastructure layer | Technical concerns (HTTP, email, file I/O)         | `PaymentGatewayClient`, `OAuthTokenProvider` |

**The rule:** Domain Services contain business rules. Application Services
coordinate flow. Infrastructure Services talk to the outside world.

---

## Domain Services

A Domain Service handles business logic that doesn't naturally belong to a
single entity. It is **stateless** — it doesn't remember anything between calls.

### When to Use

- The operation involves **multiple entities** (e.g., transferring money between
  two accounts)
- The operation requires **domain knowledge** but no single entity owns it
  (e.g., checking eligibility for enrollment based on multiple criteria)
- The logic would make the entity **too complex** or require dependencies the
  entity shouldn't have

### Implementation Pattern

```php
<?php

declare(strict_types=1);

namespace Drupal\my_module\Domain;

/**
 * Checks if a student is eligible for enrollment in a course.
 *
 * This is a Domain Service because the eligibility check involves
 * multiple domain objects and business rules that don't belong to
 * any single entity.
 */
final readonly class EnrollmentEligibilityChecker {

  /**
   * Check enrollment eligibility.
   *
   * @param array<string, mixed> $studentData
   *   Student data including prerequisites.
   * @param array<string, mixed> $courseData
   *   Course data including capacity and requirements.
   *
   * @return bool
   *   TRUE if the student is eligible.
   */
  public function isEligible(
    array $studentData,
    array $courseData,
  ): bool {
    // Business rules:
    // 1. Student has completed prerequisites
    // 2. Course has available capacity
    // 3. Enrollment window is open
    // 4. Student is not already enrolled
    return $this->hasPrerequisites($studentData, $courseData)
      && $this->hasCapacity($courseData)
      && $this->isWithinEnrollmentWindow($courseData);
  }

  private function hasPrerequisites(array $student, array $course): bool {
    // ... domain logic
    return TRUE;
  }

  private function hasCapacity(array $course): bool {
    return ($course['enrolled_count'] ?? 0) < ($course['max_capacity'] ?? PHP_INT_MAX);
  }

  private function isWithinEnrollmentWindow(array $course): bool {
    // ... domain logic
    return TRUE;
  }

}
```

### Domain Service vs Infrastructure Service

When a domain operation depends on external systems, split it:

```php
// Domain layer: interface
namespace Drupal\my_module\Domain;

interface PasswordHashingInterface {
  public function hash(string $plainPassword): string;
  public function verify(string $plainPassword, string $hash): bool;
}

// Infrastructure layer: implementation
namespace Drupal\my_module\Infrastructure;

final readonly class BcryptPasswordHashing implements PasswordHashingInterface {
  public function hash(string $plainPassword): string {
    return password_hash($plainPassword, PASSWORD_BCRYPT);
  }
  public function verify(string $plainPassword, string $hash): bool {
    return password_verify($plainPassword, $hash);
  }
}
```

The domain interface expresses what the domain needs. The infrastructure
implementation handles how it's done. Wire them in `services.yml`:

```yaml
Drupal\my_module\Infrastructure\BcryptPasswordHashing: ~
Drupal\my_module\Domain\PasswordHashingInterface:
  alias: Drupal\my_module\Infrastructure\BcryptPasswordHashing
```

### Typical Domain Service Examples

- **`SiteSettings`** — wraps config access with domain-meaningful method names
  (`getMaxItemsPerPage()`, `isRegistrationOpen()`)
- **`PricingCalculator`** — computes prices applying discounts, taxes, and
  currency conversion rules
- **`ShippingCostEstimator`** — determines shipping cost based on weight,
  destination, and carrier rules

---

## Application Services

Application Services are thin orchestrators. They coordinate the execution
of a use case without containing business logic themselves.

### The Formula

Every application service follows the same pattern:

1. **Accept a request** (DTO with primitives, not domain objects)
2. **Load aggregates** from repositories
3. **Call domain methods** on the aggregates
4. **Persist changes** via repositories
5. **Dispatch events** if needed
6. **Return a response** (DTO, not domain entities)

### Implementation Pattern

```php
<?php

declare(strict_types=1);

namespace Drupal\my_module\Service;

use Drupal\my_module\Entity\Enrollment\EnrollmentRepositoryInterface;
use Drupal\my_module\Entity\Contrib\NodeRepositoryInterface;
use Drupal\my_module\Domain\EnrollmentEligibilityChecker;
use Drupal\my_module\Event\StudentWasEnrolled;
use Psr\Log\LoggerInterface;
use Symfony\Component\DependencyInjection\Attribute\Autowire;
use Symfony\Contracts\EventDispatcher\EventDispatcherInterface;

/**
 * Application Service: orchestrates student enrollment.
 *
 * This service does NOT contain business logic — it coordinates
 * domain objects and infrastructure.
 */
final readonly class EnrollStudentService {

  public function __construct(
    private EnrollmentRepositoryInterface $enrollments,
    private NodeRepositoryInterface $courses,
    private EnrollmentEligibilityChecker $eligibilityChecker,
    private EventDispatcherInterface $eventDispatcher,
    #[Autowire(service: 'logger.channel.my_module')]
    private LoggerInterface $logger,
  ) {}

  /**
   * Enroll a student in a course.
   *
   * @param string $studentId
   *   The student user ID.
   * @param string $courseId
   *   The course entity ID.
   *
   * @return \Drupal\my_module\Entity\ValueObject\EnrollmentOutcome
   *   The enrollment outcome.
   */
  public function execute(string $studentId, string $courseId): EnrollmentOutcome {
    // 1. Load aggregates
    $course = $this->courses->load($courseId);
    if ($course === NULL) {
      return EnrollmentOutcome::failed('Course not found');
    }

    // 2. Check domain rules (via Domain Service)
    if (!$this->eligibilityChecker->isEligible($studentId, $course)) {
      return EnrollmentOutcome::failed('Student not eligible');
    }

    // 3. Create enrollment (domain method on aggregate root)
    $enrollment = $course->createEnrollment($studentId);

    // 4. Persist
    $this->enrollments->save($enrollment);

    // 5. Dispatch domain event
    $this->eventDispatcher->dispatch(
      new StudentWasEnrolled($studentId, $courseId),
    );

    // 6. Return result
    $this->logger->info('Student {student} enrolled in course {course}', [
      'student' => $studentId,
      'course' => $courseId,
    ]);

    return EnrollmentOutcome::enrolled((string) $enrollment->id());
  }

}
```

### Application Services in Drupal's Architecture

In Drupal, application services sit between the framework layer (controllers,
forms, Drush commands) and the domain:

```
Controller / Form / Drush Command
  → calls Application Service (thin orchestrator)
    → uses Repository (load/save)
    → calls Domain methods (business logic)
    → dispatches Events (side effects)
    → returns DTO (no entities leak out)
```

**Rules:**

- Application Services accept **primitives or DTOs** (not entities)
- Application Services return **DTOs or Value Objects** (not entities)
- Application Services manage **transactions** (see below)
- Application Services do NOT contain `if/else` business logic — that goes
  in domain methods or domain services
- Application Services are the right place to handle **logging** and
  **event dispatching**

### When Is a Dedicated Application Service Worth It?

- The same operation is triggered from multiple places (form, REST, Drush)
- The operation involves multiple repositories or external services
- The operation has side effects (events, notifications)
- You want to unit test the orchestration independently from the framework

If the operation is simple (load one entity, change one field, save), a form
submit handler calling a repository directly is fine.

---

## Domain Events

A Domain Event records that something significant happened in the domain. It
is **immutable** — a fact about the past that cannot be changed.

### Naming Convention

Domain Events are named as **past-tense verbs**:

- `StudentWasEnrolled`
- `OrderWasPlaced`
- `PaymentWasReceived`
- `InventoryWasReplenished`

### Event Class

```php
<?php

declare(strict_types=1);

namespace Drupal\my_module\Event;

use Symfony\Contracts\EventDispatcher\Event;

/**
 * Dispatched when a student enrolls in a course.
 */
final class StudentWasEnrolled extends Event {

  public function __construct(
    public readonly string $studentId,
    public readonly string $courseId,
    public readonly \DateTimeImmutable $occurredOn = new \DateTimeImmutable(),
  ) {}

}
```

### Event Subscriber

```php
<?php

declare(strict_types=1);

namespace Drupal\my_module\EventSubscriber;

use Drupal\my_module\Event\StudentWasEnrolled;
use Symfony\Component\EventDispatcher\EventSubscriberInterface;

/**
 * Reacts to enrollment events.
 */
final class SendEnrollmentConfirmation implements EventSubscriberInterface {

  public function __construct(
    private readonly MailManagerInterface $mailManager,
  ) {}

  public static function getSubscribedEvents(): array {
    return [
      StudentWasEnrolled::class => 'onStudentEnrolled',
    ];
  }

  public function onStudentEnrolled(StudentWasEnrolled $event): void {
    // Send confirmation email — this is a side effect, not domain logic
    $this->mailManager->mail(
      'my_module',
      'enrollment_confirmation',
      $this->getStudentEmail($event->studentId),
      'en',
      ['course_id' => $event->courseId],
    );
  }

}
```

### Domain Events vs Drupal Hooks

|                  | Drupal Hooks                                                      | Domain Events                                 |
| ---------------- | ----------------------------------------------------------------- | --------------------------------------------- |
| **Coupling**     | Tight (hook implementations know about internal entity structure) | Loose (events carry only what listeners need) |
| **Semantics**    | Technical (`hook_entity_insert`)                                  | Domain (`StudentWasEnrolled`)                 |
| **Cross-module** | Any module can implement any hook                                 | Events are dispatched by the owning module    |
| **Async**        | Always synchronous                                                | Can be async (via Symfony Messenger)          |
| **Testing**      | Requires Drupal bootstrap                                         | Can test dispatch + handling independently    |

**Use hooks when:**

- You need to alter Drupal's built-in behavior (form alter, entity view, etc.)
- The reaction is tightly coupled to Drupal's lifecycle (presave, insert, delete)

**Use Domain Events when:**

- The side effect is in a different Bounded Context
- You want to decouple modules
- The reaction can happen asynchronously
- You need an audit trail of what happened
- You want to test the event dispatch independently

### Async Domain Events with Symfony Messenger

For operations that can tolerate delay, dispatch a message instead:

```php
// Message class (immutable, serializable)
final readonly class SyncOrderToExternalSystem {
  public function __construct(
    public string $orderId,
    public string $targetSystem,
  ) {}
}

// Handler (processes the message asynchronously)
#[AsMessageHandler]
final readonly class SyncOrderHandler {
  public function __construct(
    private OrderRepositoryInterface $orders,
    private ExternalClient $client,
  ) {}

  public function __invoke(SyncOrderToExternalSystem $message): void {
    $order = $this->orders->load($message->orderId);
    $this->client->sync($order, $message->targetSystem);
  }
}
```

---

## The Anemic Model Trap

The Anemic Domain Model anti-pattern is the most common DDD pitfall in Drupal
because Drupal's architecture naturally pushes logic away from entities.

### How to Detect It

| Signal                                                                   | What It Means                     |
| ------------------------------------------------------------------------ | --------------------------------- |
| Entity has only getters/setters, no business methods                     | Logic is elsewhere                |
| `hook_entity_presave` contains `if ($entity->bundle() === 'X')` branches | Business rules leaked into hooks  |
| A "god service" orchestrates dozens of field operations                  | Service is doing the entity's job |
| Domain events are dispatched from services, never from entities          | Entities are passive data bags    |

### How to Fix It

1. **Identify business operations** — look at your hooks and services for
   `$entity->set()` calls surrounded by business logic
2. **Move them to entity methods** — create named methods that express
   the intent (`$order->accept()`, `$enrollment->confirm()`)
3. **Keep hooks thin** — hooks should delegate to entity methods or services
4. **Test entity methods** — since they contain the logic, they need tests

```php
// BEFORE: Logic in a hook
function my_module_entity_presave(EntityInterface $entity): void {
  if ($entity instanceof OrderInterface && $entity->isNew()) {
    $entity->set('field_order_number', OrderNumberGenerator::next());
    $entity->set('field_created_by', \Drupal::currentUser()->id());
    $entity->set('field_status', 'draft');
  }
}

// AFTER: Logic on the entity
class Order extends ContentEntityBase implements OrderInterface {
  public static function createDraft(
    string $orderNumber,
    string $createdBy,
  ): static {
    return static::create([
      'field_order_number' => $orderNumber,
      'field_created_by' => $createdBy,
      'field_status' => 'draft',
    ]);
  }
}

// Application Service calls the factory method:
$order = Order::createDraft(
  $this->orderNumberGenerator->next(),
  $currentUser->id(),
);
$this->orderRepository->save($order);
```

### The Pragmatic Middle Ground

Not every entity needs to be a rich domain model. The decision tree:

- **No business logic** (basic page, simple content) → Anemic is fine
- **Some validation** (field constraints, required fields) → Drupal's built-in
  validation is sufficient
- **Business rules** (state transitions, calculations, cross-field invariants) →
  Rich entity methods
- **Complex orchestration** (multi-entity, external systems) → Rich entity
  methods + Domain Services + Application Services

---

## Transactions

### Who Manages Transactions?

The Application Service layer owns transaction boundaries. Domain objects
and repositories should not start or commit transactions — they operate within
a transaction managed by their caller.

### Drupal's Transaction Support

```php
// In an Application Service:
public function transferFunds(string $fromId, string $toId, Money $amount): void {
  $transaction = $this->database->startTransaction();
  try {
    $from = $this->accountRepository->load($fromId);
    $to = $this->accountRepository->load($toId);

    $from->debit($amount);
    $to->credit($amount);

    $this->accountRepository->save($from);
    $this->accountRepository->save($to);

    // Transaction commits when $transaction goes out of scope
  }
  catch (\Exception $e) {
    $transaction->rollBack();
    throw $e;
  }
}
```

**Drupal's transaction model:** Transactions in Drupal auto-commit when the
transaction object goes out of scope. Call `$transaction->rollBack()` explicitly
on failure. Nested transactions use savepoints.

### When Transactions Matter

- Multiple entities modified in a single operation (both must succeed or fail)
- Financial or accounting operations
- Operations where partial completion would leave data inconsistent

For single-entity saves, Drupal's built-in `$entity->save()` is already
atomic — no manual transaction needed.
