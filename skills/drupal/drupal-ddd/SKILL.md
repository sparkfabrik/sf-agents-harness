---
name: drupal-ddd
description: >-
  Apply Domain-Driven Design patterns in Drupal 11 custom modules. Covers
  strategic design (Bounded Contexts, Ubiquitous Language, Context Maps) and
  tactical patterns (Value Objects, Entities, Aggregates, Domain Services,
  Domain Events, Factories, Application Services, Anti-Corruption Layers).
  Includes the mandatory Repository Pattern for ALL entity interactions —
  code using EntityTypeManager, EntityStorage, entity queries, or CRUD must
  follow this architecture. Patterns adapted from "DDD in PHP" to Drupal
  Entity API. Use when designing module architecture, modeling domains,
  structuring business logic, or when terms like "value object", "aggregate",
  "domain event", "bounded context", "rich model", "anemic model",
  "application service", "domain service", "anti-corruption layer",
  "repository pattern", or "hexagonal architecture" come up. Also for code
  that loads, queries, saves, or deletes entities, splitting modules,
  avoiding fat controllers, integrating external APIs, or deciding where
  logic belongs.
---

# Domain-Driven Design in Drupal

This skill teaches how to apply DDD principles in Drupal 11 custom modules.
Drupal uses a PDO-based Entity API (not Doctrine ORM), so every pattern here
is adapted to work with `EntityTypeManager`, entity queries, Drupal's service
container, and the hook/event system.

The **Repository Pattern** is a core DDD building block and is **mandatory** in
this project for ALL entity interactions. See `references/repository-pattern.md`
for the full implementation guide. This skill covers the broader DDD landscape —
Value Objects, Entities, Aggregates, Services, Events, and integration patterns —
and shows how they work alongside repositories in Drupal.

## How This Skill Is Organized

- **SKILL.md** (this file): Strategic design + tactical pattern overview with
  decision guidance. Read this first.
- **references/repository-pattern.md**: The mandatory Repository Design Pattern —
  interface definition, concrete implementation, service registration, directory
  structure, correct/incorrect examples, and edge cases.
- **references/value-objects.md**: Deep dive into Value Objects in Drupal — when
  to use them, how to persist them, testing patterns.
- **references/entities-aggregates.md**: Rich Entities, Aggregate design rules,
  invariant enforcement in Drupal's entity system.
- **references/services-and-events.md**: Domain Services vs Application Services,
  Domain Events via Symfony EventDispatcher, the Anemic Model trap.
- **references/bounded-contexts.md**: Strategic design — modules as Bounded
  Contexts, Anti-Corruption Layers, integration patterns.

Read the relevant reference file when you need implementation details for a
specific pattern.

---

## Strategic Design: The Big Picture

### Ubiquitous Language

The Ubiquitous Language is a shared vocabulary between developers and domain
experts. In Drupal, this means:

- **Content type names** use domain terms, not technical labels
  (e.g., `course_of_study` not `academic_content_type_3`)
- **Field names** reflect what the business calls them
  (e.g., `field_enrollment_deadline` not `field_date_2`)
- **Module names** represent domain concepts
  (e.g., `my_project_access` for access control, not `my_project_perms_util`)
- **Service class names** read as domain operations
  (e.g., `EnrollmentVerifier`, not `DataProcessor`)

When a domain expert says "a student enrolls in a course of study," the code
should contain classes named `Student`, `CourseOfStudy`, and a method called
`enroll()`. If the code uses different terms, communication breaks down and
bugs follow.

### Bounded Contexts

A Bounded Context is a boundary within which a particular domain model applies.
In Drupal, **each custom module is a natural Bounded Context**:

```
my_project_access/       → Access Control context (Groups, Permissions, Sections)
my_project_catalog/      → Product Catalog context (Products, Categories, Pricing)
my_project_crm/          → CRM Integration context (Contacts, Sync, External API)
my_project_content/      → Core Content context (Pages, Navigation, Layout)
```

**Rules for Bounded Context boundaries:**

1. Each module owns its domain model — its entity types, value objects, and
   business rules. Other modules interact through **published interfaces**
   (services, events), never by reaching into another module's internals.

2. The same real-world concept may have different representations in different
   contexts. A "User" in an access control module cares about group membership;
   a "User" in a CRM module cares about sync history. Each context defines its
   own interface for the aspects it needs.

3. Shared code between contexts should be minimal. If two modules need the same
   utility, extract it to a shared library module, but keep domain logic within
   its owning module.

### Context Maps and Integration Patterns

When modules need to communicate, choose the right integration pattern:

| Pattern                   | When to Use                                  | Drupal Implementation                                                      |
| ------------------------- | -------------------------------------------- | -------------------------------------------------------------------------- |
| **Published Language**    | Modules agree on a shared data format        | Shared interfaces in a base module                                         |
| **Customer-Supplier**     | One module serves another's needs            | Service interface in supplier, consumer injects it                         |
| **Anti-Corruption Layer** | Integrating with external/legacy systems     | Adapter service that translates external API responses into domain objects |
| **Conformist**            | You must accept another system's model as-is | Direct mapping with minimal translation                                    |
| **Separate Ways**         | No meaningful relationship                   | Modules don't interact at all                                              |

For detailed implementation guidance on integration patterns and ACLs, read
`references/bounded-contexts.md`.

---

## Tactical Patterns: Decision Guide

The hardest part of DDD is knowing **which pattern to reach for**. Use this
decision tree when designing a feature:

### "Where does this logic belong?"

```
Is it a concept with no identity, defined only by its attributes?
  → VALUE OBJECT (Email, Money, DateRange, Slug, PostalCode)
  → See references/value-objects.md

Is it a concept with identity that changes over time?
  → ENTITY (Node, User, Order, Product)
  → See references/entities-aggregates.md

Is it a cluster of entities that must be consistent together?
  → AGGREGATE (Node + its Paragraphs, Order + its LineItems)
  → See references/entities-aggregates.md

Is it an operation that doesn't naturally belong to any entity?
  → DOMAIN SERVICE (authentication, cross-entity calculations)
  → See references/services-and-events.md

Is it an orchestration of multiple steps (load, validate, save, notify)?
  → APPLICATION SERVICE (form submit handler, API endpoint logic)
  → See references/services-and-events.md

Is it something significant that happened in the domain?
  → DOMAIN EVENT (UserRegistered, OrderPlaced, PaymentReceived)
  → See references/services-and-events.md

Does it create complex objects with business rules?
  → FACTORY (entity creation with invariant checks)
  → See references/entities-aggregates.md
```

### "Is DDD overkill here?"

DDD is not always the answer. Use this checklist:

- **Simple CRUD** with no business rules beyond validation → Use Drupal's
  built-in entity forms and validation constraints. No need for domain objects.
- **Configuration pages** → Use `ConfigFormBase`. No domain modeling needed.
- **Display logic** (how things look) → Theme layer, SDC components. Not domain.
- **Complex business rules**, state machines, cross-entity consistency,
  external integrations → DDD patterns shine here.

The goal is not to apply every pattern everywhere, but to use the right pattern
where complexity justifies it. A module with 3 fields and no business logic
doesn't need Value Objects and Aggregates. A module integrating with an external
ERP and enforcing business rules does.

---

## Tactical Pattern Quick Reference

### Value Objects

Immutable objects defined by their attributes, not identity. Use them to replace
primitive types (`string`, `int`) with domain-meaningful types.

```php
// Instead of passing raw strings around:
function sendEmail(string $to, string $subject): void;

// Use Value Objects that self-validate:
function sendEmail(EmailAddress $to, Subject $subject): void;
```

**When to use in Drupal:**

- Complex field values (Money = amount + currency, DateRange = start + end)
- Domain concepts that appear in multiple places (PostalCode, IsoLanguageCode)
- Anything where validation rules exist (email format, currency codes)

**Drupal-specific:** Drupal fields are already a form of persistence-level value
objects. PHP Value Objects add domain-level validation and behavior on top.
Convert between them at the repository boundary.

Read `references/value-objects.md` for full implementation details.

### Entities and Aggregates

Entities have identity and mutable state. Aggregates are clusters of entities
with a root that enforces consistency.

**In Drupal**, content entities (nodes, taxonomy terms, custom entities) are
already entities with identity. The DDD contribution is:

1. **Rich behavior** — push business logic into entity methods instead of
   spreading it across hooks and services
2. **Aggregate boundaries** — a node + its paragraphs form a natural aggregate;
   the node is the root
3. **Invariant enforcement** — use `hook_entity_presave` or custom validation
   constraints to enforce business rules

Read `references/entities-aggregates.md` for patterns.

### Domain Services

Stateless operations that don't belong to any single entity. In Drupal, these
are registered as services in `*.services.yml`.

```php
// Domain Service: operates on domain concepts, no infrastructure dependency
final readonly class EnrollmentEligibilityChecker {
  public function isEligible(Student $student, CourseOfStudy $course): bool {
    // Business rule: check prerequisites, capacity, deadlines
  }
}
```

**The Anemic Model trap:** Drupal's architecture naturally pushes toward entities
as data bags with all logic in services/hooks. Fight this by asking: "Could this
logic live on the entity itself?" If the logic needs only the entity's own data,
it belongs on the entity.

Read `references/services-and-events.md` for the full picture.

### Domain Events

Record that something significant happened. In Drupal, use Symfony's
EventDispatcher for synchronous events, or Drupal's Queue API / Symfony
Messenger for async.

```php
// Event class (immutable record of what happened)
final readonly class OrderWasPlaced {
  public function __construct(
    public string $orderId,
    public string $customerId,
    public \DateTimeImmutable $occurredOn,
  ) {}
}
```

**When to use instead of hooks:**

- When the side-effect is in a different Bounded Context
- When you need an audit trail of domain changes
- When the reaction can happen asynchronously
- When you want to decouple the triggering code from the reacting code

Read `references/services-and-events.md` for implementation patterns.

### Application Services

Thin orchestrators that coordinate domain operations. In Drupal, these sit
between the controller/form layer and the domain:

```php
final readonly class PlaceOrderService {
  public function __construct(
    private OrderRepositoryInterface $orders,
    private InventoryServiceInterface $inventory,
    private EventDispatcherInterface $events,
  ) {}

  public function execute(string $customerId, array $items): OrderOutcome {
    $order = Order::createDraft($customerId, $items);
    $this->inventory->reserve($items);
    $this->orders->save($order);
    $this->events->dispatch(new OrderWasPlaced($order->id(), $customerId));
    return OrderOutcome::placed((string) $order->id());
  }
}
```

**Rules:**

- No business logic in application services — delegate to entities/domain services
- Accept primitive types or DTOs as input (not entities)
- Return DTOs or Value Objects (not entities) to the presentation layer
- Handle transactions at this level

Read `references/services-and-events.md` for details.

---

## Module Directory Structure

This is the recommended structure for a DDD-oriented Drupal module. Not every
module needs every directory — use what fits the complexity:

```
web/modules/custom/my_module/
├── my_module.info.yml
├── my_module.module              # Thin: delegates to Hook classes
├── my_module.services.yml        # DI wiring
├── src/
│   ├── Domain/                   # Domain settings, constants, specifications
│   │   └── Settings.php          # Config wrapper (domain concept names)
│   ├── Entity/                   # Entity classes + repository interfaces
│   │   ├── Order/
│   │   │   ├── Order.php         # Drupal entity with rich behavior
│   │   │   ├── OrderInterface.php
│   │   │   └── OrderRepositoryInterface.php
│   │   ├── Contrib/              # Repo interfaces for contrib entities
│   │   │   └── NodeRepositoryInterface.php
│   │   └── ValueObject/          # Pure PHP value objects
│   │       ├── Money.php
│   │       └── PostalCode.php
│   ├── Infrastructure/
│   │   └── Persistence/
│   │       └── Repository/       # Concrete repository implementations
│   │           └── OrderRepository.php
│   ├── Service/                  # Application services (orchestrators)
│   │   └── PlaceOrderService.php
│   ├── Event/                    # Domain events
│   │   └── OrderWasPlaced.php
│   ├── EventSubscriber/          # Event listeners (reactions)
│   ├── Messenger/                # Async message classes + handlers
│   ├── Hook/                     # Drupal hook implementations
│   ├── Controller/               # Route controllers (thin)
│   ├── Form/                     # Drupal forms
│   ├── Plugin/                   # Drupal plugins
│   ├── Presentation/             # UI-facing services, Twig extensions
│   │   └── Acl/                  # Access policies
│   ├── Adapter/                  # Adapter pattern (domain interface wrappers)
│   ├── Exception/                # Domain-specific exceptions
│   └── Trait/                    # Reusable traits
```

**Key principles:**

- Group by domain concept within `Entity/`, not by architectural role
- `Entity/ValueObject/` holds pure PHP classes with no Drupal dependency
- Repository interfaces live next to the entities they serve
- Infrastructure code (persistence, external APIs) stays in `Infrastructure/`
- Keep controllers and forms thin — they delegate to services

---

## Layered Architecture in Drupal

DDD organizes code into layers with strict dependency rules:

```
┌─────────────────────────────────────────────┐
│  Presentation Layer                         │
│  Controllers, Forms, Twig, SDC, Hooks       │
│  → Can depend on: Application, Domain       │
├─────────────────────────────────────────────┤
│  Application Layer                          │
│  Application Services, DTOs, Commands       │
│  → Can depend on: Domain                    │
├─────────────────────────────────────────────┤
│  Domain Layer                               │
│  Entities, Value Objects, Domain Services,  │
│  Repository Interfaces, Domain Events       │
│  → Depends on: NOTHING (pure PHP)           │
├─────────────────────────────────────────────┤
│  Infrastructure Layer                       │
│  Repository Implementations, API Clients,   │
│  Messaging, File Storage                    │
│  → Implements: Domain interfaces            │
│  → Can depend on: Domain, Drupal APIs       │
└─────────────────────────────────────────────┘
```

The critical rule: **the Domain layer has no dependencies on Drupal APIs**.
Value Objects, Domain Services, and Domain Events are pure PHP. This makes
them testable without bootstrapping Drupal.

The exception: Drupal Entity classes (in `Entity/`) necessarily depend on
Drupal's Entity API. This is a pragmatic compromise — Drupal entities are both
domain objects and persistence objects. Enrich them with behavior, but keep
complex business logic in separate domain classes when possible.

---

## Anti-Patterns to Avoid

### 1. Anemic Domain Model

**Symptom:** Entities are data bags with getters/setters. All logic lives in
services, hooks, or form handlers.

```php
// BAD: Entity is just a data container
$order->set('status', 'accepted');
$order->set('updated', new \DateTimeImmutable());
$order->save();

// GOOD: Entity encapsulates behavior
$order->accept(); // internally sets status + timestamp + records event
```

### 2. Fat Controllers / Fat Hooks

**Symptom:** Controllers or hook implementations contain 50+ lines of business
logic, entity queries, and conditional branching.

**Fix:** Extract to an Application Service that orchestrates domain operations.
The controller just calls the service and returns a response.

### 3. Primitive Obsession

**Symptom:** Passing `string $email`, `float $amount`, `string $currency_code`
everywhere instead of typed Value Objects.

**Fix:** Create `EmailAddress`, `Money`, `CurrencyCode` value objects that
self-validate on construction. Invalid values can't exist.

### 4. Shared Database / Shared Kernel Creep

**Symptom:** Module A directly queries Module B's database tables or reaches
into its entity storage.

**Fix:** Module B exposes a service interface. Module A injects and calls that
interface. If the integration is with an external system, use an
Anti-Corruption Layer.

### 5. Event Handlers with Business Logic

**Symptom:** An event subscriber contains complex business rules instead of
simply reacting to an event.

**Fix:** The event subscriber should delegate to a Domain Service or
Application Service. It's a thin dispatcher, not a business logic container.
