# PHP and Drupal Security Patterns

Common vulnerability patterns and hardening guidance for PHP applications and
Drupal sites.

## Code injection

### eval() and dynamic code execution

#### Vulnerable

```php
eval($_GET['code']);

// preg_replace with /e modifier (removed in PHP 7, but legacy code may have it)
preg_replace('/.*/e', $_GET['replacement'], $input);

// create_function (deprecated in PHP 7.2, removed in PHP 8.0)
$func = create_function('$a', $_GET['body']);

// assert() with string argument (PHP < 8.0)
assert($_GET['expr']);
```

#### Safe

```php
// Never pass user input to eval(), assert(), or dynamic code execution.
// If you need dynamic behavior, use a whitelist of allowed operations.

$allowed = ['sum', 'avg', 'count'];
if (in_array($operation, $allowed, true)) {
    $result = call_user_func("calculate_$operation", $data);
}
```

**What to look for**: `eval(`, `assert(` with string arguments, `create_function(`,
`preg_replace` with `/e` modifier, `call_user_func` with user-controlled function
names.

## Object injection (unserialize)

### Vulnerable

```php
$data = unserialize($_COOKIE['session_data']);

$object = unserialize(file_get_contents($_GET['url']));
```

### Safe

```php
// Use json_decode instead of unserialize for untrusted data
$data = json_decode($_COOKIE['session_data'], true);

// If unserialize is unavoidable, restrict allowed classes
$data = unserialize($input, ['allowed_classes' => [SafeClass::class]]);
```

**What to look for**: `unserialize(` where the input comes from user-controlled
sources (`$_GET`, `$_POST`, `$_COOKIE`, `$_REQUEST`, file uploads, database
values controlled by users).

## Variable injection (extract)

### Vulnerable

```php
extract($_GET);  // overwrites any local variable
extract($_POST);
```

### Safe

```php
// Never use extract() with user input.
// Access variables explicitly.
$name = $_GET['name'] ?? '';
$email = $_GET['email'] ?? '';

// If extract is needed, use EXTR_SKIP to prevent overwriting
extract($data, EXTR_SKIP);
```

**What to look for**: `extract(` with `$_GET`, `$_POST`, `$_REQUEST`, or any
user-controlled array.

## Local/remote file inclusion

### Vulnerable

```php
include $_GET['page'] . '.php';

require_once $userInput;

include "templates/" . $_GET['template'];
```

### Safe

```php
$allowed = ['home', 'about', 'contact'];
$page = $_GET['page'] ?? 'home';
if (in_array($page, $allowed, true)) {
    include "templates/$page.php";
}
```

**What to look for**: `include`, `include_once`, `require`, `require_once` with
user-controlled paths or path components. Also `file_get_contents()`,
`readfile()`, `fopen()` with user input.

## Command injection

### Vulnerable

```php
system("ls " . $_GET['dir']);
exec("convert " . $_GET['file'] . " output.png");
passthru("ping " . $_POST['host']);
$output = shell_exec("grep " . $userInput . " /var/log/app.log");
$output = `cat {$_GET['file']}`;  // backtick operator
```

### Safe

```php
// Use escapeshellarg() for individual arguments
$dir = escapeshellarg($_GET['dir']);
system("ls $dir");

// Use escapeshellcmd() for full commands (less safe than escapeshellarg)
// Prefer escapeshellarg() on individual arguments.

// Best: avoid shell entirely
$files = scandir($validated_dir);
```

**What to look for**: `system(`, `exec(`, `passthru(`, `shell_exec(`,
`popen(`, `proc_open(`, backtick operator with user input. Also
`escapeshellarg` / `escapeshellcmd` that are applied incorrectly or
inconsistently.

## XSS (htmlspecialchars)

### Vulnerable

```php
echo "Hello, " . $_GET['name'];

echo "<a href='" . $userInput . "'>link</a>";

// Missing ENT_QUOTES -- allows attribute breakout via single quotes
echo htmlspecialchars($input);  // defaults to ENT_QUOTES in PHP 8.1+, but older versions use ENT_COMPAT
```

### Safe

```php
echo "Hello, " . htmlspecialchars($_GET['name'], ENT_QUOTES, 'UTF-8');

// Always specify ENT_QUOTES and encoding for portability
echo '<a href="' . htmlspecialchars($url, ENT_QUOTES, 'UTF-8') . '">link</a>';
```

**What to look for**: `echo`, `print`, `printf` with `$_GET`, `$_POST`,
`$_REQUEST`, or any user input without `htmlspecialchars()`. Also
`htmlspecialchars()` without `ENT_QUOTES` or encoding parameter on PHP < 8.1.

## SQL injection

### Vulnerable (raw PDO / mysqli)

```php
$stmt = $pdo->query("SELECT * FROM users WHERE id = " . $_GET['id']);

$result = mysqli_query($conn, "SELECT * FROM users WHERE name = '" . $_POST['name'] . "'");
```

### Safe

```php
$stmt = $pdo->prepare("SELECT * FROM users WHERE id = :id");
$stmt->execute([':id' => $_GET['id']]);

$stmt = $conn->prepare("SELECT * FROM users WHERE name = ?");
$stmt->bind_param('s', $_POST['name']);
$stmt->execute();
```

**What to look for**: String concatenation or variable interpolation in SQL
query strings passed to `->query()`, `->exec()`, `mysqli_query()`.

---

## Drupal-specific patterns

### Render array injection (XSS)

#### Vulnerable

```php
// #markup does NOT escape HTML -- user input goes straight to output
$build['content'] = [
  '#markup' => $user_input,
];

// t() with user input as the string (not as a replacement)
$build['content'] = [
  '#markup' => t($user_input),
];
```

#### Safe

```php
// #plain_text auto-escapes
$build['content'] = [
  '#plain_text' => $user_input,
];

// Or explicitly filter
use Drupal\Component\Utility\Xss;
$build['content'] = [
  '#markup' => Xss::filter($user_input),
];

// For translated strings, user input goes in replacements, not the string
$build['content'] = [
  '#markup' => t('Hello @name', ['@name' => $user_input]),
];
```

**What to look for**: `#markup` with variables that may contain user input.
`t()` where the first argument is a variable rather than a literal string.
`\Drupal\Component\Utility\Html::escape()` missing on user-facing output.

### Drupal SQL injection

#### Vulnerable

```php
// String concatenation in database queries
$result = \Drupal::database()->query(
  "SELECT * FROM {node_field_data} WHERE title = '" . $title . "'"
);

// Variable interpolation
$result = \Drupal::database()->query(
  "SELECT * FROM {users_field_data} WHERE uid = $uid"
);
```

#### Safe

```php
// Parameterized query with :placeholder
$result = \Drupal::database()->query(
  "SELECT * FROM {node_field_data} WHERE title = :title",
  [':title' => $title]
);

// Using the query builder
$query = \Drupal::database()->select('node_field_data', 'n');
$query->condition('title', $title);
$query->fields('n');
$result = $query->execute();

// Entity query (preferred for entities)
$nids = \Drupal::entityQuery('node')
  ->condition('title', $title)
  ->accessCheck(TRUE)
  ->execute();
```

**What to look for**: `\Drupal::database()->query(` with string concatenation
or variable interpolation. Also `db_query()` (deprecated) with the same
patterns. `->select()`, `->insert()`, `->update()`, `->delete()` where
`->condition()` values are built via concatenation.

### Form API CSRF

Drupal's Form API provides built-in CSRF protection via form tokens. The
vulnerability appears when state-changing operations bypass the Form API.

#### Vulnerable

```php
// Custom route controller that modifies data without CSRF protection
class DeleteController extends ControllerBase {
  public function delete($id) {
    // No form, no token -- any GET request deletes the entity
    $entity = Node::load($id);
    $entity->delete();
    return new RedirectResponse('/admin/content');
  }
}
```

```yaml
# routing.yml -- state-changing action on GET
mymodule.delete:
  path: "/admin/delete/{id}"
  defaults:
    _controller: '\Drupal\mymodule\Controller\DeleteController::delete'
  requirements:
    _permission: "administer content"
```

#### Safe

```php
// Use a confirmation form (extends ConfirmFormBase) for destructive actions
class DeleteForm extends ConfirmFormBase {
  public function getFormId() { return 'mymodule_delete_form'; }
  public function getQuestion() { return $this->t('Are you sure?'); }
  public function getCancelUrl() { return new Url('system.admin_content'); }

  public function submitForm(array &$form, FormStateInterface $form_state) {
    // Form API handles CSRF token validation automatically
    $entity = Node::load($this->entityId);
    $entity->delete();
  }
}

// Or use CSRF token on custom routes
// In routing.yml:
// requirements:
//   _csrf_token: 'TRUE'
```

**What to look for**: Route controllers performing `->delete()`, `->save()`, or
other state-changing operations without using Form API or `_csrf_token`
requirement. Routes that accept GET for state-changing actions.

### Twig autoescape bypass

Drupal's Twig templates auto-escape output by default. Vulnerabilities appear
when autoescape is explicitly bypassed.

#### Vulnerable

```twig
{# |raw disables escaping -- XSS if user_input is attacker-controlled #}
{{ user_input|raw }}

{# Markup objects bypass escaping #}
{{ content.field_body }}  {# safe if field is properly sanitized #}

{# Inline template with raw #}
{% set html = '<script>alert(1)</script>' %}
{{ html|raw }}
```

#### Safe

```twig
{# Auto-escaped by default -- safe #}
{{ user_input }}

{# Explicit escape (redundant but documents intent) #}
{{ user_input|escape }}

{# Escape for specific context #}
{{ url|escape('url') }}
```

**What to look for**: `|raw` filter in `.html.twig` files, especially where
the variable may contain user input. `{% autoescape false %}` blocks. Custom
Twig extensions that return `\Twig\Markup` objects wrapping user input.

### Access bypass

#### Vulnerable

```php
// Entity query without access check
$nids = \Drupal::entityQuery('node')
  ->condition('type', 'article')
  ->execute();
// Returns ALL articles regardless of user permissions

// Loading entities without access checking
$nodes = Node::loadMultiple($nids);
foreach ($nodes as $node) {
  // No access check before rendering -- unpublished content exposed
  $build[] = \Drupal::entityTypeManager()
    ->getViewBuilder('node')
    ->view($node);
}
```

```yaml
# Route without access control
mymodule.api:
  path: "/api/data"
  defaults:
    _controller: '\Drupal\mymodule\Controller\ApiController::getData'
  # Missing: requirements._permission or requirements._access
```

#### Safe

```php
// Entity query with access check
$nids = \Drupal::entityQuery('node')
  ->condition('type', 'article')
  ->accessCheck(TRUE)  // REQUIRED since Drupal 9.3
  ->execute();

// Check access before rendering
foreach ($nodes as $node) {
  if ($node->access('view')) {
    $build[] = \Drupal::entityTypeManager()
      ->getViewBuilder('node')
      ->view($node);
  }
}
```

```yaml
# Route with proper access control
mymodule.api:
  path: "/api/data"
  defaults:
    _controller: '\Drupal\mymodule\Controller\ApiController::getData'
  requirements:
    _permission: "access content"
```

**What to look for**: `\Drupal::entityQuery(` without `->accessCheck(TRUE)`.
Route definitions in `*.routing.yml` missing `_permission`, `_access`, or
`_role` under `requirements`. Custom controllers that load and display entities
without calling `->access()`. Hook implementations that bypass access (e.g.
`hook_node_access` returning `AccessResult::allowed()` too broadly).

### Insecure file handling

#### Vulnerable

```php
// Sensitive files stored in public:// (accessible via /sites/default/files/)
$file = \Drupal::service('file.repository')->writeData(
  $sensitive_data,
  'public://reports/user-data.pdf'
);

// File upload field configured with public:// for private documents
$fields['document'] = BaseFieldDefinition::create('file')
  ->setSetting('uri_scheme', 'public')  // world-accessible!
  ->setSetting('file_extensions', 'pdf doc docx');
```

#### Safe

```php
// Use private:// for sensitive files
$file = \Drupal::service('file.repository')->writeData(
  $sensitive_data,
  'private://reports/user-data.pdf'
);

// File field with private storage
$fields['document'] = BaseFieldDefinition::create('file')
  ->setSetting('uri_scheme', 'private')
  ->setSetting('file_extensions', 'pdf doc docx');
```

**What to look for**: `public://` used for files that contain sensitive data
(user documents, reports, exports). File field definitions with
`'uri_scheme' => 'public'` for private/sensitive content. Missing
`private://` file system configuration in `settings.php`
(`$settings['file_private_path']`).

---

## PHP scanner tool configuration

### composer audit

Checks `composer.lock` against the PHP Security Advisories Database.

```bash
composer audit --format=json
```

Requires `composer.lock` to exist. Reports known CVEs in installed packages.

### phpcs with Drupal coding standards

```bash
phpcs --standard=Drupal,DrupalPractice --extensions=php,module,inc,install,theme --report=json .
```

Key security-related sniffs:

- `Drupal.Semantics.FunctionT` -- validates `t()` usage
- `DrupalPractice.General.ClassName` -- checks for proper namespacing
- `Drupal.Functions.DiscouragedFunctions` -- flags `eval()`, `exec()`, etc.

### psalm (taint analysis)

Psalm's taint analysis traces data flow from user input (sources) to dangerous
operations (sinks).

```bash
psalm --taint-analysis --output-format=json
```

Requires `vendor/` to exist (needs autoloader). Taint sources include `$_GET`,
`$_POST`, `$_COOKIE`, `$_SERVER`, and framework-specific input methods. Sinks
include `echo`, `eval()`, SQL queries, `exec()`, `file_get_contents()`.

Psalm's taint analysis is the most effective automated tool for finding data
flow vulnerabilities in PHP. If `vendor/` is available, prioritize running it.

### phpstan

```bash
phpstan analyse --error-format=json --no-progress
```

Requires `vendor/` and a `phpstan.neon` configuration. General static analysis
that catches type errors, dead code, and some security issues. More effective
with security-focused extensions:

- `phpstan/phpstan-strict-rules` -- stricter type checking
- `phpstan/phpstan-deprecation-rules` -- deprecated function usage

### drupal-check

```bash
drupal-check --no-progress --format=json web/modules/custom
```

Checks for deprecated API usage and some Drupal-specific issues. Useful for
identifying code that may have known security implications in newer Drupal
versions.

### local-php-security-checker

```bash
local-php-security-checker --path=composer.lock --format=json
```

Standalone binary from Symfony. Checks `composer.lock` against the FriendsOfPHP
security advisories database. Similar to `composer audit` but uses a different
advisory source, so it may catch different CVEs.
