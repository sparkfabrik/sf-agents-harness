# Drupal Repository Design Pattern — Mandatory Architecture

**This is a HARD CONSTRAINT. You MUST follow these rules for ALL entity
interactions in Drupal modules. There are NO exceptions.**

This project enforces strict separation of concerns through the Repository
Design Pattern. All entity storage and query logic is encapsulated in
dedicated repository classes. Controllers, forms, services, event subscribers,
and plugins NEVER interact with the entity storage layer directly.

---

## Table of Contents

1. [Forbidden Patterns](#forbidden-patterns)
2. [Required Architecture](#required-architecture)
3. [Directory Structure](#directory-structure)
4. [Implementation Guide](#implementation-guide)
5. [Correct vs Incorrect Examples](#correct-vs-incorrect-examples)
6. [Decision Checklist](#decision-checklist)
7. [Abstract Base Class Pattern](#abstract-base-class-pattern)
8. [Edge Cases and Clarifications](#edge-cases-and-clarifications)

---

## Forbidden Patterns

You **MUST NEVER** do any of the following outside of a Repository class:

| Forbidden Action                                     | Where It Must Not Appear                                                                                               |
| ---------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------- |
| Inject `EntityTypeManagerInterface`                  | Controllers, Forms, Services, Event Subscribers, Plugins, Message Handlers                                             |
| Inject `EntityStorageInterface`                      | Controllers, Forms, Services, Event Subscribers, Plugins, Message Handlers                                             |
| Call `\Drupal::entityTypeManager()`                  | Anywhere (static calls are always forbidden)                                                                           |
| Call `\Drupal::entityQuery()`                        | Anywhere outside a Repository                                                                                          |
| Call `$storage->load()`, `$storage->loadMultiple()`  | Anywhere outside a Repository                                                                                          |
| Call `$entity->save()`, `$entity->delete()` directly | Anywhere outside a Repository (unless on the entity's own form handler via `$entity->save()` in a content entity form) |

**If you find yourself about to inject `EntityTypeManagerInterface` into a Controller, Form, or Service — STOP. You need
a Repository.**

---

## Required Architecture

Whenever ANY code needs to interact with entities (load, query, create, save,
delete), you **MUST**:

1. **Define a Repository Interface** in the domain layer
2. **Implement the Repository** in the infrastructure layer
3. **Register it as a service** with an interface alias
4. **Inject the interface** into the consumer (controller, form, service, etc.)

### Architecture Flow

```
Consumer (Controller/Form/Service)
    |
    |  injects RepositoryInterface (domain contract)
    v
RepositoryInterface  <----  defines domain methods (load, query, create...)
    |
    |  implemented by
    v
ConcreteRepository  ---->  ONLY class allowed to use EntityTypeManagerInterface
    |
    |  registered in
    v
module.services.yml  ---->  interface alias -> concrete class
```

---

## Directory Structure

You **MUST** place files according to this layout:

### Custom Module Entities

```
src/
├── Entity/
│   └── {EntityName}/
│       ├── {EntityName}Interface.php                  # Entity interface
│       └── {EntityName}RepositoryInterface.php        # Repository contract
├── Infrastructure/
│   └── Persistence/
│       └── Repository/
│           └── Entity/
│               ├── Abstract{Module}EntityRepository.php   # Optional base class
│               └── {EntityName}Repository.php             # Concrete implementation
```

### Contrib / Third-Party Entity Wrappers

When wrapping entities from contributed modules (User, File, Node, etc.):

```
src/
├── Entity/
│   └── Contrib/
│       └── {ContribEntity}RepositoryInterface.php     # Repository contract
├── Infrastructure/
│   └── Persistence/
│       └── Repository/
│           └── Entity/
│               └── {ContribEntity}Repository.php      # Concrete implementation
```

---

## Implementation Guide

### Step 1: Define the Repository Interface

Place in `src/Entity/{EntityName}/{EntityName}RepositoryInterface.php` (custom)
or `src/Entity/Contrib/{Entity}RepositoryInterface.php` (contrib wrapper).

**Rules:**

- Return **strongly-typed** domain objects, never generic `EntityInterface`
- Use `?TypedReturn` for nullable loads
- Never expose `EntityStorageInterface` or query objects

```php
<?php

declare(strict_types=1);

namespace Drupal\my_module\Entity\Project;

/**
 * Repository interface for Project entity operations.
 */
interface ProjectRepositoryInterface {

  /**
   * Load all projects.
   *
   * @return array<array-key, \Drupal\my_module\Entity\Project\ProjectInterface>
   *   The project entities.
   */
  public function loadAll(): array;

  /**
   * Load a single project by ID.
   *
   * @param string $entity_id
   *   The project entity ID.
   *
   * @return ?\Drupal\my_module\Entity\Project\ProjectInterface
   *   The project entity or NULL if not found.
   */
  public function load(string $entity_id): ?ProjectInterface;

  /**
   * Load projects by owner.
   *
   * @param string $owner_id
   *   The owner user ID.
   *
   * @return array<array-key, \Drupal\my_module\Entity\Project\ProjectInterface>
   *   The matching project entities.
   */
  public function loadByOwner(string $owner_id): array;

}
```

### Step 2: Implement the Repository

Place in `src/Infrastructure/Persistence/Repository/Entity/{EntityName}Repository.php`.

**Rules:**

- This is the **ONLY** class that may depend on `EntityTypeManagerInterface`
- Use `getStorage()` from the abstract base class or inject storage directly
- All public methods return domain-typed objects
- Encapsulate `entityQuery` calls inside repository methods

```php
<?php

declare(strict_types=1);

namespace Drupal\my_module\Infrastructure\Persistence\Repository\Entity;

use Drupal\Core\Entity\EntityTypeManagerInterface;
use Drupal\my_module\Entity\Project\ProjectInterface;
use Drupal\my_module\Entity\Project\ProjectRepositoryInterface;

class ProjectRepository implements ProjectRepositoryInterface {

  public function __construct(
    private readonly EntityTypeManagerInterface $entityTypeManager,
  ) {}

  /**
   * {@inheritdoc}
   */
  public function loadAll(): array {
    /** @var array<array-key, \Drupal\my_module\Entity\Project\ProjectInterface> */
    return $this->getStorage()->loadMultiple();
  }

  /**
   * {@inheritdoc}
   */
  public function load(string $entity_id): ?ProjectInterface {
    $entity = $this->getStorage()->load($entity_id);
    return $entity instanceof ProjectInterface ? $entity : NULL;
  }

  /**
   * {@inheritdoc}
   */
  public function loadByOwner(string $owner_id): array {
    $ids = $this->getStorage()->getQuery()
      ->accessCheck(FALSE)
      ->condition('owner_id', $owner_id)
      ->execute();

    if (empty($ids)) {
      return [];
    }

    /** @var array<array-key, \Drupal\my_module\Entity\Project\ProjectInterface> */
    return $this->getStorage()->loadMultiple($ids);
  }

  private function getStorage(): \Drupal\Core\Entity\EntityStorageInterface {
    return $this->entityTypeManager->getStorage('my_module_project');
  }

}
```

### Step 3: Register the Service

In `my_module.services.yml`:

```yaml
services:
  # Concrete repository (autowired)
  Drupal\my_module\Infrastructure\Persistence\Repository\Entity\ProjectRepository: ~

  # Interface alias — consumers inject the INTERFACE, resolved to the concrete class
  Drupal\my_module\Entity\Project\ProjectRepositoryInterface: '@Drupal\my_module\Infrastructure\Persistence\Repository\Entity\ProjectRepository'
```

For repositories needing constructor arguments (e.g., entity type ID):

```yaml
services:
  Drupal\my_module\Infrastructure\Persistence\Repository\Entity\ProjectRepository:
    arguments:
      $entityTypeId: "my_module_project"

  Drupal\my_module\Entity\Project\ProjectRepositoryInterface: '@Drupal\my_module\Infrastructure\Persistence\Repository\Entity\ProjectRepository'
```

### Step 4: Inject Into Consumers

Controllers, forms, services, and message handlers inject the **interface**:

```php
<?php

declare(strict_types=1);

namespace Drupal\my_module\Controller;

use Drupal\Core\Controller\ControllerBase;
use Drupal\my_module\Entity\Project\ProjectRepositoryInterface;
use Symfony\Component\HttpFoundation\JsonResponse;

class ProjectController extends ControllerBase {

  public function __construct(
    private readonly ProjectRepositoryInterface $projectRepository,
  ) {}

  public function list(): JsonResponse {
    $projects = $this->projectRepository->loadAll();
    // ... build response
    return new JsonResponse($data);
  }

  public function detail(string $project_id): JsonResponse {
    $project = $this->projectRepository->load($project_id);
    if ($project === NULL) {
      throw new NotFoundHttpException();
    }
    // ... build response
    return new JsonResponse($data);
  }

}
```

---

## Correct vs Incorrect Examples

### Scenario: A controller needs to load a Tenant entity by ID

#### INCORRECT — Do NOT generate this

```php
// WRONG: Injecting EntityTypeManagerInterface directly into a controller.
class TenantController extends ControllerBase {

  public function __construct(
    private readonly EntityTypeManagerInterface $entityTypeManager, // FORBIDDEN
  ) {}

  public function view(string $tenant_id): array {
    $tenant = $this->entityTypeManager
      ->getStorage('sf_ai_tenant')  // Direct storage access
      ->load($tenant_id);
    // ...
  }

}
```

**Why it is wrong:**

- The controller now knows about storage internals (entity type ID, storage API)
- Business logic and persistence are coupled
- Cannot be unit-tested without mocking the entire entity subsystem
- Violates the Single Responsibility Principle

#### CORRECT — Generate this instead

```php
// RIGHT: Inject the repository interface.
class TenantController extends ControllerBase {

  public function __construct(
    private readonly TenantRepositoryInterface $tenantRepository, // Domain contract
  ) {}

  public function view(string $tenant_id): array {
    $tenant = $this->tenantRepository->load($tenant_id); // Clean, typed, testable
    // ...
  }

}
```

**Why it is correct:**

- Controller depends on a domain interface, not infrastructure
- Storage logic is encapsulated in `TenantRepository`
- Easily unit-testable with a mock/stub of `TenantRepositoryInterface`
- Adding new query methods requires only updating the repository, never the consumer

---

### Scenario: A form needs to create a new Webpage entity

#### INCORRECT

```php
class WebpageCreateForm extends FormBase {

  public function __construct(
    private readonly EntityTypeManagerInterface $entityTypeManager, // FORBIDDEN
  ) {}

  public function submitForm(array &$form, FormStateInterface $form_state): void {
    $storage = $this->entityTypeManager->getStorage('sf_ai_webpage');
    $webpage = $storage->create([
      'uri' => $form_state->getValue('uri'),
    ]);
    $webpage->save(); // Direct save outside repository
  }

}
```

#### CORRECT

```php
class WebpageCreateForm extends FormBase {

  public function __construct(
    private readonly WebpageRepositoryInterface $webpageRepository,
  ) {}

  public function submitForm(array &$form, FormStateInterface $form_state): void {
    $this->webpageRepository->create(
      new WebpageDTO(url: $form_state->getValue('uri')),
      $knowledgeBase,
      WebpageSyncFrequency::Daily,
    ); // Repository handles creation, validation, and persistence
  }

}
```

---

### Scenario: A service needs to query entities with conditions

#### INCORRECT

```php
class WebpageSyncService {

  public function __construct(
    private readonly EntityTypeManagerInterface $entityTypeManager, // FORBIDDEN
  ) {}

  public function findStaleWebpages(): array {
    $ids = $this->entityTypeManager->getStorage('sf_ai_webpage')
      ->getQuery()
      ->accessCheck(FALSE)
      ->condition('last_sync', strtotime('-1 day'), '<')
      ->execute();

    return $this->entityTypeManager->getStorage('sf_ai_webpage')
      ->loadMultiple($ids);
  }

}
```

#### CORRECT

```php
// 1. Add the method to the repository interface:
interface WebpageRepositoryInterface {
  public function loadStaleWebpages(\DateTimeInterface $since): array;
}

// 2. Implement in the repository:
class WebpageRepository implements WebpageRepositoryInterface {

  public function loadStaleWebpages(\DateTimeInterface $since): array {
    $ids = $this->getStorage()->getQuery()
      ->accessCheck(FALSE)
      ->condition('last_sync', $since->getTimestamp(), '<')
      ->execute();

    return empty($ids) ? [] : $this->getStorage()->loadMultiple($ids);
  }

}

// 3. Inject the interface into the service:
class WebpageSyncService {

  public function __construct(
    private readonly WebpageRepositoryInterface $webpageRepository,
  ) {}

  public function findStaleWebpages(): array {
    return $this->webpageRepository->loadStaleWebpages(
      new \DateTimeImmutable('-1 day'),
    );
  }

}
```

---

## Decision Checklist

Before generating any entity-related code, ask yourself:

| Question                                                          | If YES                                                               |
| ----------------------------------------------------------------- | -------------------------------------------------------------------- |
| Does this class need to load an entity?                           | Inject a `RepositoryInterface`                                       |
| Does this class need to query entities by conditions?             | Add a method to the `RepositoryInterface`, implement in `Repository` |
| Does this class need to create/save/delete entities?              | Add a method to the `RepositoryInterface`, implement in `Repository` |
| Is the entity from a contrib module (User, File, Node, etc.)?     | Create a wrapper repository under `Entity/Contrib/`                  |
| Am I about to type `EntityTypeManagerInterface` in a constructor? | **STOP.** You need a Repository instead.                             |

---

## Abstract Base Class Pattern

When a module has multiple custom entity repositories sharing common behavior,
use an abstract base class:

```php
abstract class AbstractModuleEntityRepository implements ModuleEntityRepositoryInterface {

  public function __construct(
    private readonly string $entityTypeId,
    private readonly EntityTypeManagerInterface $entityTypeManager,
  ) {}

  protected function getStorage(): EntityStorageInterface {
    return $this->entityTypeManager->getStorage($this->entityTypeId);
  }

}
```

Concrete repositories extend the base class **and implement a domain-specific
interface**. All public methods **MUST** return strongly-typed domain objects:

```php
class ProjectRepository extends AbstractModuleEntityRepository
  implements ProjectRepositoryInterface {

  public function __construct(
    string $entityTypeId,
    EntityTypeManagerInterface $entityTypeManager,
  ) {
    parent::__construct($entityTypeId, $entityTypeManager);
  }

  /**
   * {@inheritdoc}
   *
   * @return array<array-key, \Drupal\my_module\Entity\Project\ProjectInterface>
   */
  public function loadAll(): array {
    /** @var array<array-key, \Drupal\my_module\Entity\Project\ProjectInterface> */
    return $this->getStorage()->loadMultiple();
  }

  /**
   * {@inheritdoc}
   */
  public function load(string $entity_id): ?ProjectInterface {
    $entity = $this->getStorage()->load($entity_id);
    return $entity instanceof ProjectInterface ? $entity : NULL;
  }

  /**
   * @return array<array-key, \Drupal\my_module\Entity\Project\ProjectInterface>
   */
  public function loadByOwner(string $owner_id): array {
    $ids = $this->getStorage()->getQuery()
      ->accessCheck(FALSE)
      ->condition('owner_id', $owner_id)
      ->execute();

    if (empty($ids)) {
      return [];
    }

    /** @var array<array-key, \Drupal\my_module\Entity\Project\ProjectInterface> */
    return $this->getStorage()->loadMultiple($ids);
  }

}
```

The corresponding interface defines the full domain contract with typed returns:

```php
interface ProjectRepositoryInterface extends ModuleEntityRepositoryInterface {

  /**
   * @return array<array-key, \Drupal\my_module\Entity\Project\ProjectInterface>
   */
  public function loadAll(): array;

  public function load(string $entity_id): ?ProjectInterface;

  /**
   * @return array<array-key, \Drupal\my_module\Entity\Project\ProjectInterface>
   */
  public function loadByOwner(string $owner_id): array;

}
```

---

## Edge Cases and Clarifications

- **Entity forms** (extending `ContentEntityForm` or `EntityForm`): The form's
  built-in `$this->entity->save()` in `save()` is acceptable — the form
  system itself manages the entity lifecycle. You do NOT need a repository
  for the entity form's own save operation.
- **Entity list builders**: `EntityListBuilder` receives storage by design
  from Drupal core. This is acceptable within the list builder class only.
- **Hook implementations**: If a hook receives an entity parameter, operating
  on that entity directly is fine. But if the hook needs to LOAD additional
  entities, use a repository.
- **Migrations**: Migration plugins may use `EntityTypeManagerInterface`
  directly, as they are infrastructure-level operations.
- **Tests**: Test classes may use `EntityTypeManagerInterface` for test setup
  and assertions. Production code must still use repositories.
