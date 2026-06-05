# Bounded Contexts and Integration Patterns in Drupal

## Table of Contents

1. [Modules as Bounded Contexts](#modules-as-bounded-contexts)
2. [Context Mapping](#context-mapping)
3. [Anti-Corruption Layer](#anti-corruption-layer)
4. [Integration Patterns](#integration-patterns)
5. [Cross-Module Communication](#cross-module-communication)
6. [Hexagonal Architecture in Drupal](#hexagonal-architecture-in-drupal)

---

## Modules as Bounded Contexts

A Bounded Context is a boundary within which a particular domain model applies.
The key insight: **the same real-world concept can have different meanings in
different contexts.**

A "User" in an Access Control context is a principal with roles and permissions.
A "User" in a CRM Integration context is a contact with sync metadata. These
are different models of the same real-world thing, and they should live in
different modules.

### How Drupal Modules Map to Bounded Contexts

Each custom Drupal module should own a coherent slice of the domain:

```
my_project_access/       → Access Control BC
  - Group entity, group membership, section-based access
  - "User" here = UserWithGroupsInterface (groups, permissions)

my_project_catalog/      → Product Catalog BC
  - Product, Category, Pricing entities
  - "Product" here = something with inventory and pricing rules

my_project_crm/          → CRM Integration BC
  - Contact sync, field mapping, submission tracking
  - "Contact" here = data packet for the external CRM system

my_project_content/      → Core Content BC
  - Base content, homepage, common settings
  - "Page" here = navigational content with SEO and layout
```

### Module Boundary Rules

1. **Own your entities.** A module's entity types, their fields, and their
   storage logic belong exclusively to that module.

2. **Expose through interfaces.** If another module needs data from yours,
   expose a service interface. Don't let them query your tables directly.

3. **Don't share entity classes.** If two modules both need "Node" data,
   each creates its own `NodeRepositoryInterface` with the specific methods
   it needs. They don't share a single god-repository.

4. **Separate the language.** Each module can have its own vocabulary.
   `field_access_groups` means something specific in the access module;
   another module shouldn't interpret it.

5. **Configuration ownership.** Each module exports and manages its own
   configuration. Cross-module config dependencies should be explicit
   (via `dependencies:` in `.info.yml`).

---

## Context Mapping

A Context Map shows the relationships between Bounded Contexts. In Drupal,
these relationships manifest as module dependencies and service interfaces.

### Relationship Types

**Customer-Supplier (Upstream/Downstream)**

One module supplies data that another consumes. The supplier defines the
interface; the consumer adapts.

```
my_project_catalog (Supplier)  →  my_project_content (Customer)
  ProductRepositoryInterface         Loads product data to display on pages
```

```yaml
# In my_project_content.info.yml
dependencies:
  - my_project_catalog:my_project_catalog
```

**Conformist**

You accept another system's model without translation. Common when using
contrib modules as-is:

```
Drupal Core User  →  my_project_access
  my_project_access accepts Drupal's User entity model
  and wraps it with UserWithGroupsInterface
```

**Anti-Corruption Layer (ACL)**

When integrating with an external system whose model doesn't match yours,
insert a translation layer. This is the most important integration pattern
for Drupal sites that talk to external APIs.

**Separate Ways**

Two modules have no interaction. Most Drupal modules fall into this category.

---

## Anti-Corruption Layer

The ACL is a shield between your domain model and an external system's model.
It translates external data into your domain's language so your code never
depends on external structures.

### Why It Matters

Without an ACL, external API changes ripple through your codebase:

```php
// BAD: External API structure leaks into domain code
class ProductService {
  public function findProduct(string $id): array {
    $response = $this->httpClient->get("/api/v2/products/{$id}");
    $data = json_decode($response->getBody(), TRUE);
    // Now your entire codebase depends on the API's JSON structure
    return [
      'name' => $data['product_name'],
      'price' => $data['unit_price_cents'] / 100,
      'sku' => $data['stock_keeping_unit'],
    ];
  }
}
```

With an ACL, the translation is isolated:

```php
// GOOD: Anti-Corruption Layer translates at the boundary
// 1. Adapter (talks to external API)
class ExternalCatalogAdapter implements ProductProviderInterface {
  public function __construct(
    private readonly HttpClientInterface $httpClient,
    private readonly ExternalProductTranslator $translator,
  ) {}

  public function findProduct(string $externalId): ?Product {
    $response = $this->httpClient->get("/api/v2/products/{$externalId}");
    $data = json_decode($response->getBody(), TRUE);
    return $this->translator->toDomainModel($data);
  }
}

// 2. Translator (converts external → domain)
class ExternalProductTranslator {
  public function toDomainModel(array $apiData): Product {
    return new Product(
      name: $apiData['product_name'] ?? '',
      price: Money::ofCents((int) ($apiData['unit_price_cents'] ?? 0), 'USD'),
      sku: $apiData['stock_keeping_unit'] ?? '',
    );
  }
}

// 3. Domain interface (what the domain needs — no external concepts)
interface ProductProviderInterface {
  public function findProduct(string $externalId): ?Product;
}
```

### ACL Components

| Component             | Role                          | Drupal Location                            |
| --------------------- | ----------------------------- | ------------------------------------------ |
| **Domain Interface**  | Defines what the domain needs | `src/Entity/` or `src/Domain/`             |
| **Adapter**           | Talks to the external system  | `src/Infrastructure/`                      |
| **Translator/Mapper** | Converts external → domain    | `src/Infrastructure/` or `src/Service/`    |
| **Domain Model**      | Your internal representation  | `src/Entity/` or `src/Entity/ValueObject/` |

### Exception Hierarchy

External system errors should be wrapped in domain-specific exceptions:

```php
// Base exception for the external integration
class ExternalSystemException extends \RuntimeException {}

// Specific failure modes
class AuthenticationFailedException extends ExternalSystemException {}
class RateLimitExceededException extends ExternalSystemException {
  public function __construct(
    public readonly int $retryAfterSeconds,
  ) {
    parent::__construct('Rate limit exceeded');
  }
}
class ResourceNotFoundException extends ExternalSystemException {}
```

This pattern isolates external error semantics from your domain. Your
application services catch `ExternalSystemException` subtypes and handle
them with domain-appropriate responses (retry, skip, fail gracefully).

---

## Integration Patterns

### Synchronous Integration (Service Calls)

Direct service injection — the simplest integration between modules:

```php
// Module A injects Module B's service interface
class ContentDisplayService {
  public function __construct(
    private readonly GroupRepositoryInterface $groups,
  ) {}

  public function getAccessibleContent(string $userId): array {
    $userGroups = $this->groups->loadGroupsForUser($userId);
    // ... filter content by groups
  }
}
```

**When to use:** The caller needs the result immediately, and both modules
are always deployed together.

### Asynchronous Integration (Events + Message Queue)

For operations that can tolerate delay or must not block the current request:

```php
// Module A dispatches an event
$this->eventDispatcher->dispatch(new ContentWasPublished($nodeId));

// Module B subscribes to react
class ExternalSearchIndexSubscriber implements EventSubscriberInterface {
  public static function getSubscribedEvents(): array {
    return [ContentWasPublished::class => 'onContentPublished'];
  }

  public function onContentPublished(ContentWasPublished $event): void {
    // Queue the indexing work for async processing
    $this->messageBus->dispatch(
      new IndexContentInExternalSearch($event->nodeId)
    );
  }
}
```

**When to use:**

- Side effects that can happen later (sending emails, updating search index)
- External system integration that might be slow or unreliable
- Operations that should not fail the current request if they error

### REST API Integration

When modules live in separate applications or you integrate with third-party
APIs:

```php
// Published Language: define the shared data contract
final readonly class ProductApiResponse {
  public function __construct(
    public string $id,
    public string $name,
    public float $price,
    public string $currency,
  ) {}

  public static function fromArray(array $data): self {
    return new self(
      id: $data['id'],
      name: $data['name'],
      price: $data['price'],
      currency: $data['currency'],
    );
  }
}
```

---

## Cross-Module Communication

### Drupal Queue API (Built-in Async)

For simple async work within a single Drupal installation:

```php
// Enqueue work
$queue = \Drupal::queue('my_module_sync');
$queue->createItem(['order_id' => $id]);

// Queue worker plugin processes it
#[QueueWorker(
  id: 'my_module_sync',
  title: new TranslatableMarkup('Sync orders'),
  cron: ['time' => 60],
)]
class SyncQueueWorker extends QueueWorkerBase {
  public function processItem($data): void {
    $this->syncService->sync($data['order_id']);
  }
}
```

### Symfony Messenger (Advanced Async)

For more sophisticated async processing with retry, routing, and transports:

```php
// Dispatch message
$this->messageBus->dispatch(
  new ProcessExternalData($recordId, $sourceSystem)
);

// Handler processes it (possibly on a different worker)
#[AsMessageHandler]
class ProcessExternalDataHandler {
  public function __invoke(ProcessExternalData $message): void {
    // Heavy processing here
  }
}
```

### Choosing the Right Integration

| Need                      | Pattern           | Drupal Tool                            |
| ------------------------- | ----------------- | -------------------------------------- |
| Simple side effect        | Symfony Event     | `EventDispatcherInterface`             |
| Background job            | Queue             | `\Drupal::queue()`                     |
| Reliable async with retry | Messenger         | Symfony Messenger                      |
| Cross-module data access  | Service interface | Service container DI                   |
| External API              | ACL + HTTP Client | `\Drupal::httpClient()` behind adapter |
| Real-time sync            | REST endpoint     | Custom route + controller              |

---

## Hexagonal Architecture in Drupal

Hexagonal Architecture (Ports and Adapters) is the architectural style
recommended by the DDD in PHP book. It maps naturally to Drupal:

```
                    ┌───────────────────────────────────┐
                    │                                   │
   HTTP Request ───→│  Port: Controller                 │
                    │    ↓                              │
   Form Submit ────→│  Port: Form Handler               │
                    │    ↓                              │
   Drush Command ──→│  Port: Drush Command              │
                    │    ↓                              │
                    │  Application Service              │
                    │    ↓                              │
                    │  Domain (Entities, VOs, Services) │
                    │    ↓                              │
                    │  Port: Repository Interface       │───→ Adapter: EntityStorage
                    │  Port: ExternalAPI Interface      │───→ Adapter: HTTP Client
                    │  Port: Notification Interface     │───→ Adapter: Mail Manager
                    │                                   │
                    └───────────────────────────────────┘
```

### Ports = Interfaces

**Driving ports** (input): How the outside world triggers your domain logic

- Controllers, Forms, Drush Commands, Queue Workers, Event Subscribers

**Driven ports** (output): How your domain reaches the outside world

- Repository interfaces, External API interfaces, Notification interfaces

### Adapters = Implementations

Each port has one or more adapters:

- `NodeRepositoryInterface` → `DrupalNodeRepository` (production),
  `InMemoryNodeRepository` (test)
- `ExternalApiInterface` → `HttpExternalApiClient` (production),
  `StubExternalApi` (test)

### The Key Benefit

Your domain code (entities, value objects, domain services) depends on
**ports** (interfaces), never on **adapters** (implementations). This means:

1. **Testability** — swap adapters for in-memory stubs in tests
2. **Flexibility** — change infrastructure without touching domain code
3. **Clarity** — the domain expresses what it needs, not how it's done

---

## Example: Full ACL for External API Integration

Here's a complete example of integrating a Drupal module with an external
product catalog API using the Anti-Corruption Layer pattern:

```
External Product Catalog API
  ↓ (raw JSON response)
ExternalCatalogClient (Infrastructure — HTTP adapter)
  ↓ (raw array data)
ExternalProductTranslator (Infrastructure — translator)
  ↓ (Product domain object)
ProductRepository (Infrastructure/Persistence)
  ↓ (persisted to Drupal storage)
```

Key classes:

- **`ExternalCatalogClient`** — handles HTTP calls, authentication, error
  wrapping. Only class that knows about the API's URL structure and auth.
- **`ExternalProductTranslator`** — maps API response fields to domain
  Value Objects and entities. Only class that knows about the API's field names.
- **`ProductProviderInterface`** — domain interface. The rest of the
  application depends on this, never on the HTTP client or translator.
- **`ExternalSystemException` hierarchy** — wraps HTTP errors into
  domain-meaningful exceptions.

The benefit: when the external API changes (field names, auth mechanism,
versioning), only the adapter and translator need updates. Your domain code,
application services, and controllers remain untouched.

### Integration Architecture Diagram

```
my_project_content ←──(service call)──→ my_project_catalog
  ↑                                          ↑
  │ (depends on)                      (REST API)
  │                                          │
  ↓                                          ↓
my_project_access                    External Catalog API
  ↑
  │ (adapts core entities)
  │
  ↓
Drupal Core (Node, User, MenuLink)

my_project_crm ←──(async message)──→ External CRM System
```

Each arrow represents a specific integration pattern:

- **Service call**: direct DI injection of interfaces
- **REST API**: Anti-Corruption Layer with adapter + translator
- **Async message**: Symfony Messenger for reliable sync
- **Adapts**: Adapter pattern wrapping core entities
