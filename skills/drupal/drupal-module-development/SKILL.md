---
name: drupal-module-development
description: >-
  How to develop custom Drupal 11 modules on SparkFabrik's Firestarter platform.
  Covers module scaffolding, hook implementations, and best practices for custom
  functionality. Use this skill whenever building custom features that can't be
  achieved with contrib modules or configuration alone — whether it's a simple
  hook_form_alter or a complex integration with external APIs.
  Always follow Drupal coding standards and the config-first workflow for any
  structural changes.
---

ALWAYS CLEAR CACHES AFTER ANY CODE CHANGE! Use `drush cr` or `drush cache:rebuild` to ensure you see the latest code in action.

ALWAYS RUN A FULL QA CHECK WHEN IMPLEMENTATION IS COMPLETE! Use `make drupal-qa` to run all quality checks and fix any
issues, even those not introduced by your code. For implementation that impacts the web UI (both admin and frontend),
check if they are working as expected in a real browser and that no new errors appear in the logs.

NEVER add `@phpstan-ignore`, `@SuppressWarnings`, `// phpcs:ignore`, or any other suppression annotation to silence QA
errors. If you cannot fix the root cause of a QA failure with a clean code change, STOP and explain the problem to the
user. Suppressions are a deliberate human decision, never an automated fix. See the `drupal-php-standards` skill for
write-time prevention and the `drupal-qa` skill for the full fix protocol and the last-resort notification procedure.

# Code Style and Standards
Adhere to Drupal coding standards (PSR-12 with Drupal extensions). Use Coder and PHPCS for enforcement.

- **PHP**:
    - Indentation: 2 spaces (no tabs)
    - Line length: ≤ 80 characters
    - Naming: CamelCase classes/methods, snake_case variables/functions
    - Always use braces; prefer early returns
    - Full PHPDoc blocks with `@param`, `@return`, `@throws`

- **YAML**: 2-space indentation, lowercase keys
- **Twig**: `{{ }}` for output, `{% %}` for logic; always escape with `|e`

Case conventions:
* Classes: PascalCase (e.g., `MyModuleService`)
* Methods: camelCase (e.g., `getConfigValue()`)
* Properties: camelCase (e.g., `$configFactory`)
* Functions: lower_case (e.g., `my_module_helper()`)
* Variables: lower_case (e.g., `$my_variable`)

**Reject any code that fails Drupal Coder sniffs.**

# Drupal Development Patterns

## Attributes
- **use PHP8 attributes** for plugin definitions, hooks, and other metadata

## Services & Dependency Injection
- **Create services** in `modulename.services.yml` file for reusable logic
- **Use dependency injection** to inject services into controllers, forms, and plugins
- **Core services** like `@current_user`, `@entity_type.manager`, `@database` are available
- **Best practice**: Avoid static `\Drupal::` calls in favor of dependency injection
- **Service discovery**: Use `drush eval "print_r(\Drupal::getContainer()->getServiceIds());"` to see available services
- **Location**: Place service classes in `src/` directory with proper namespace

### Dependency Injection Optimization

**Core Principle: Keep Constructors Lightweight (Lazy Initialization)**

In Drupal, service constructors should be strictly limited to assigning injected dependencies to class properties. With PHP 8+, this is best achieved using **constructor property promotion**.

**The Rule:** Do not fetch configuration, compute values, or instantiate complex objects (like HTTP clients or external API wrappers) directly inside the `__construct()` method.

**Why it matters:**
* **Preserves Lazy Loading:** Service containers often instantiate services just to inject them into other services, even if they aren't used in that specific request. Doing "real work" in the constructor forces unnecessary processing and memory allocation.
* **Improves Testability:** Keeping constructors simple isolates logic failures to specific method executions rather than failing during the initial mock/setup phase of a unit test.

**The Solution:**
Use PHP 8 constructor property promotion to inject services (like `ConfigFactory`), and use a private/protected **getter method** with memoization to instantiate complex objects only when they are first explicitly requested.

**Code Example:**

```php
// ❌ BAD: Doing work in the constructor
public function __construct(
  protected ConfigFactoryInterface $configFactory,
  protected ?ApiClient $apiClient = null,
) {
  // Forces config load and allocation every time the service is built
  $config = $this->configFactory->get('my.settings'); 
  $this->apiClient = new ApiClient($config->get('api_key'));
}

// ✅ GOOD: Lazy loading + PHP 8 Promoted Properties
class MyService {
  // The client itself is not promoted, as it is not injected
  protected ?ApiClient $apiClient = null;

  public function __construct(
    // Dependencies are promoted and automatically assigned
    protected ConfigFactoryInterface $configFactory,
  ) {} // Constructor body is completely empty!

  protected function getApiClient(): ApiClient {
    // Memoization: Build it only once, and only if requested
    if ($this->apiClient === null) {
      $config = $this->configFactory->get('my.settings');
      $this->apiClient = new ApiClient($config->get('api_key'));
    }
    return $this->apiClient;
  }
}
```

### Autoconfiguration
Automatically tags services based on the interfaces they implement. Registered in CoreServiceProvider (since Drupal 10.2):

* EventSubscriberInterface -> event_subscriber
* LoggerAwareInterface -> logger_aware
* PreWarmableInterface -> cache_prewarmable
* ModuleUninstallValidatorInterface -> module_install.uninstall_validator
* MediaLibraryOpenerInterface -> media_library.opener

### Autowiring
When enabled, the container resolves constructor dependencies automatically by matching type hints to FQCN-aliased services. Enable it globally:

```yml
services:
  _defaults:
    autoconfigure: true
    autowire: true
  Drupal\my_module\MyService: ~   # tilde = no extra config needed
```

Always use the FQCN as the service ID for your own services. This allows autowiring to work seamlessly without needing to specify service names. Add an alias only if you need to reference the service by a different name.

If multiple services implement the same interface (e.g. LoggerInterface), the container throws an exception. Use the `#[Autowire]` attribute:

```php
use Symfony\Component\DependencyInjection\Attribute\Autowire;
use Psr\Log\LoggerInterface;
class MyService {
  public function __construct(
    #[Autowire(service: 'logger.channel.my_module')]
    private readonly LoggerInterface $logger,
  ) {}
}
```

Drupal service container does not support binding arguments by name with `bind`, never use it. Always rely on type hints and autowiring for dependencies.

Any class implementing `Symfony\Component\DependencyInjection\ContainerInterface\ContainerInjectionInterface` can use `Drupal\Core\DependencyInjection\AutowireTrait` trait for autowiring.

#### Autowiring in Controllers (Drupal 10.2+)
`ControllerBase` already ships with `AutowireTrait`. Don't use the static create() factory, but use constructor injection directly:

```php
class MyController extends ControllerBase {
  public function __construct(
    private readonly MyService $myService,
  ) {}
}
```

#### Autowiring in Hook classes (Drupal 11.1+)
Hook classes are automatically registered as autowired services:

```php
namespace Drupal\my_module\Hook;
class MyModuleHooks {
  public function __construct(
    protected readonly EntityTypeManagerInterface $entityTypeManager,
  ) {}
  #[Hook('entity_presave')]
  public function entityPresave(EntityInterface $entity): void { ... }
}
```

## Entity API & Queries
- **Entity queries**: Use entity queries for database operations instead of raw SQL
- **Query conditions**: Chain multiple conditions with `->condition()`, `->sort()`, `->range()`
- **Field access**: Use entity field API instead of direct property access
- **Performance**: Use entity query cache tags and contexts for optimal caching

### Repository Pattern (MANDATORY)

This project enforces the **Repository Design Pattern** for ALL entity interactions.
Controllers, forms, services, event subscribers, and plugins NEVER interact with
entity storage directly — no `EntityTypeManagerInterface` injection, no `\Drupal::entityQuery()`,
no direct `$entity->save()` or `$entity->delete()` outside of repository classes.

**Whenever you need to load, query, create, save, or delete entities, load the
`drupal-ddd` skill and read its `references/repository-pattern.md`** — it covers
interface definition, concrete implementation, service registration, directory
structure, correct/incorrect examples, and edge cases. The DDD skill also covers
Value Objects, Aggregates, Domain Services, Domain Events, and other patterns for
structuring complex business logic in Drupal modules.

## Plugin System
- **Plugin types**: Blocks, field formatters, field widgets, menu links, and more
- **Plugin discovery**: Use annotation-based discovery in docblocks
- **Plugin configuration**: Define plugin ID, label, and other metadata in annotations
- **Plugin base classes**: Extend appropriate base classes (BlockBase, FormatterBase, etc.)
- **Plugin placement**: Place plugins in `src/Plugin/Type/` directory structure
- **Derivative plugins**: Use for creating multiple plugins from one definition

## Hooks
- **Hook implementation**: Implement hooks as methods in the `Hook` namespace of your module
- **Hook attributes**: Use `#[Hook('hook_name')]` attribute to define which hook the method implements
- **Hook naming**: Give hooks descriptive names that indicate their purpose (`addFieldToNodeForm()`, `alterMenuLinks()`, etc.)
- **Hook parameters**: Use type hints and proper parameter documentation
- **Hook order**: Hooks fire in module weight order (lowest first)
- **Best practice**: Keep hook implementations focused and use services for complex logic

## Forms API
- **Form classes**: Extend `FormBase` for simple forms or `ConfigFormBase` for configuration forms
- **Form structure**: Use render array structure with `#type`, `#title`, `#description` properties
- **Form validation**: Implement `validateForm()` method for custom validation
- **Form submission**: Implement `submitForm()` method for processing form data
- **Form elements**: Use proper form element types (textfield, select, checkbox, etc.)
- **AJAX forms**: Add `#ajax` property to form elements for dynamic behavior
- **Form caching**: Forms are automatically cached with CSRF protection

## Routes & Controllers
- **Routing file**: Define routes in `modulename.routing.yml` with path, defaults, and requirements
- **Controllers**: ALWAYS create controller classes extending `ControllerBase` in `src/Controller/`. ControllerBase already includes the AutowireTrait for dependency injection. ControllerBase provides common helper methods and access to core services, you MUST use them.
- **Route parameters**: Use `{parameter}` placeholders in paths and inject into controller methods
- **Access control**: Implement `_permission`, `_role`, or custom access callbacks
- **Route naming**: Use `modulename.action` naming convention for clarity
- **Controller injection**: Use constructor injection for dependencies
- **Return values**: Return render arrays or Symfony Response objects

# Security & Performance Guidelines

## Security Requirements
- **Always sanitize user input**: Use `#plain_text` for untrusted content
- **CSRF protection**: Include `#token` for forms with side effects
- **Permissions**: Implement proper access checks and route requirements
- **SQL Injection**: Use Entity Query or proper parameter binding
- **XSS Prevention**: Always use `|e` filter in Twig, `#markup` for trusted HTML only
- **File uploads**: Validate file types and sizes
- **Database credentials**: Never commit credentials to version control

## Performance Best Practices
- **Render caching**: Always add `#cache` array to render arrays with appropriate `tags` and `contexts`
- **Cache tags**: Use entity-based tags like `['node:123']` or list-based tags like `['node_list']`
- **Cache contexts**: Apply user-specific contexts like `['user.roles']` for personalized content
- **Lazy loading**: Use `#lazy_builder` for expensive operations that can be loaded separately
- **Placeholder strategy**: Set `#create_placeholder: TRUE` for lazy builders to improve initial page load
- **Cache max-age**: Set appropriate `max-age` values based on content freshness requirements
- **Avoid premature optimization**: Profile first, then optimize based on actual bottlenecks
- **Database queries**: Use entity queries instead of raw SQL for better caching and security
- **Entity loading**: Load multiple entities at once when possible for better performance

## Caching Strategies
- **Render cache**: Cache complex markup with proper tags/contexts
- **Dynamic page cache**: Configure for anonymous users
- **Internal page cache**: Enable for authenticated users
- **Entity cache**: Leverage core entity caching
- **Redis/Memcache**: Configure for distributed caching

# Development Workflow

## Project Structure
- **Modules** → `modules/custom/<module_name>`
- **Themes** → `themes/custom/<theme_name>`
- **Configuration** → Export with `drush config:export`
- **Profiles** → `profiles/custom/<profile_name>`

## Essential Development Commands
```bash
# Cache management
drush cr                    # Clear all caches
drush cache:rebuild         # Alternative cache clear

# Configuration management
drush config:export         # Export configuration
drush config:import         # Import configuration
drush config:diff           # Compare config with directory

# Database operations
drush sql:dump              # Export database
drush sql:cli               # Access database CLI
drush updatedb              # Run database updates
```

## Debugging & Troubleshooting

**When debugging issues, read `references/debugging-tools.md`** for the full
drush command reference — logs, cache debugging, config debugging, module/theme
debugging, database/entity debugging, performance profiling, and common
troubleshooting recipes.

Key quick-reference:
- Logs: `docker compose logs -f drupal-php` (Monolog to stdout, no watchdog)
- Cache rebuild: `drush cr`
- Config inspect: `drush config:get <name>`
- Interactive PHP: `drush php` or `drush php:eval "code"`

# Testing & Quality Assurance

**When writing or running tests, read `references/testing-qa.md`** for PHPUnit
framework details, test types (Unit, Kernel, Functional), and code quality tool
usage.

Key essentials:
- Run all QA checks: `make drupal-qa`
- Run individual tools: `make drupal-qa phpcs`, `make drupal-qa phpstan`, etc.
- **NEVER** run QA tools from `bin/` directly — always use `make drupal-qa <tool>`
- **NEVER** silence QA errors with suppression annotations — fix the root cause. See the
  `drupal-php-standards` skill (write-time prevention) and `drupal-qa` skill (fix-time
  remediation and last-resort user notification protocol).

# Advanced Development Patterns

**When implementing Batch API, Symfony Messenger, or AJAX forms, read
`references/advanced-patterns.md`** for detailed guidance on each pattern.
