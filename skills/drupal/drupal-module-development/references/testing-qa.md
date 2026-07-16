# Testing & Quality Assurance

## Table of Contents

1. [PHPUnit Testing Framework](#phpunit-testing-framework)
2. [Test Types](#test-types)
3. [Code Quality Tools](#code-quality-tools)

---

## PHPUnit Testing Framework

Aim for >= 80% code coverage. Drupal provides multiple test types:

```bash
# Run all tests with coverage
phpunit -v --coverage-html coverage/

# Run specific test suites
phpunit --testsuite unit          # Unit tests (fast)
phpunit --testsuite kernel         # Kernel tests
phpunit --testsuite functional     # Functional tests (slower)
phpunit --testsuite javascript     # JavaScript tests

# Run specific tests
phpunit --filter MyModuleUnitTest
phpunit modules/custom/my_module/tests/src/Unit/
```

## Test Types

### Unit Tests (fastest)

- **Purpose**: Test individual classes and methods in isolation
- **Base class**: Extend `UnitTestCase` from `Drupal\Tests\UnitTestCase`
- **Speed**: Fastest test type, no Drupal bootstrap required
- **Isolation**: Test one piece of functionality at a time
- **Dependencies**: Mock external dependencies and services
- **Location**: Place in `tests/src/Unit/` directory
- **Use cases**: Service logic calculations, utility functions, data transformations
- **Best practices**: Keep tests small, focused, and deterministic

### Kernel Tests (with database)

- **Purpose**: Test Drupal interactions with minimal Drupal environment
- **Base class**: Extend `KernelTestBase` from `Drupal\KernelTests\KernelTestBase`
- **Environment**: Partial Drupal bootstrap with in-memory database
- **Modules**: Declare required modules in `$modules` static property
- **Database**: Uses SQLite in-memory database for speed
- **Location**: Place in `tests/src/Kernel/` directory
- **Use cases**: Entity CRUD operations, configuration validation, service registration
- **Setup**: Install modules and configuration in `setUp()` method

### Functional Tests (with browser)

- **Purpose**: Test complete user interactions through browser simulation
- **Base class**: Extend `BrowserTestBase` from `Drupal\Tests\BrowserTestBase`
- **Environment**: Full Drupal bootstrap with real browser
- **Speed**: Slowest test type, full page loads required
- **Theme**: Set `$defaultTheme` property (usually 'stark' or 'claro')
- **Location**: Place in `tests/src/Functional/` directory
- **Use cases**: Form submissions, page access, user permissions, JavaScript interactions
- **Browser simulation**: Uses Goutte/ChromeDriver for browser automation
- **Assertions**: Use `$this->assertSession()` for web assertions

## Code Quality Tools

Run `make drupal-qa` for all quality checks, or a single tool with `make drupal-qa <phpcs|cspell|phpmd|phpstan>`. Never run the tools from the `bin/` directory directly. The full QA workflow, including how to fix each tool's failures, lives in the `drupal-qa` skill.
