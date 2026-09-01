# Node.js and Frontend Security Patterns

Common vulnerability patterns and hardening guidance for Node.js backends and
browser-based frontends.

## XSS (Cross-Site Scripting)

### DOM-based XSS

#### Vulnerable

```javascript
document.getElementById("output").innerHTML = location.hash.slice(1);
```

#### Safe

```javascript
document.getElementById("output").textContent = location.hash.slice(1);
```

**Dangerous sinks to look for**:

- `element.innerHTML`
- `element.outerHTML`
- `document.write()`
- `document.writeln()`
- `eval()`
- `setTimeout(string)`
- `setInterval(string)`
- `new Function(string)`

**Dangerous sources** (user-controlled data):

- `location.hash`, `location.search`, `location.href`
- `document.referrer`
- `document.cookie`
- `window.name`
- `postMessage` data

### Escaping helpers

When you must insert dynamic content into HTML, use proper escaping:

```javascript
function escapeHtml(str) {
  const div = document.createElement("div");
  div.textContent = str;
  return div.innerHTML;
}

function escapeAttr(str) {
  return str
    .replace(/&/g, "&amp;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#x27;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;");
}
```

**What to look for**: Any place user input flows into `innerHTML` or template
literals that produce HTML.

## Prototype pollution

### Vulnerable

```javascript
function merge(target, source) {
  for (const key in source) {
    target[key] = source[key]; // __proto__ pollution
  }
}
```

### Safe

```javascript
function merge(target, source) {
  for (const key of Object.keys(source)) {
    // skip inherited
    if (key === "__proto__" || key === "constructor" || key === "prototype")
      continue;
    target[key] = source[key];
  }
}
// Or use Object.assign / structuredClone
```

## SQL injection (Node.js ORMs)

### Vulnerable (raw queries)

```javascript
db.query(`SELECT * FROM users WHERE id = ${req.params.id}`);
```

### Safe

```javascript
db.query("SELECT * FROM users WHERE id = ?", [req.params.id]);
```

**What to look for**: Template literals or string concatenation in SQL queries,
especially with `knex.raw()`, `sequelize.query()`, or `prisma.$queryRaw`.

## NoSQL injection (MongoDB)

### Vulnerable

```javascript
db.users.find({ username: req.body.username, password: req.body.password });
// attacker sends: { "password": { "$ne": "" } }
```

### Safe

```javascript
const username = String(req.body.username);
const password = String(req.body.password);
db.users.find({ username, password });
```

## Path traversal

### Vulnerable

```javascript
const filePath = path.join(uploadDir, req.params.filename);
res.sendFile(filePath);
```

### Safe

```javascript
const filePath = path.join(uploadDir, path.basename(req.params.filename));
if (!filePath.startsWith(path.resolve(uploadDir))) {
  return res.status(400).send("Invalid path");
}
res.sendFile(filePath);
```

## SSRF (Server-Side Request Forgery)

### Vulnerable

```javascript
const response = await fetch(req.body.url); // user controls URL
```

### Safe

```javascript
const url = new URL(req.body.url);
const allowedHosts = ["api.example.com"];
if (!allowedHosts.includes(url.hostname)) {
  return res.status(400).send("Host not allowed");
}
// Also check for internal IPs (127.0.0.1, 10.x, 172.16-31.x, 192.168.x)
```

## Dependency security

```bash
# Check for known CVEs
npm audit

# Fix automatically where possible
npm audit fix

# Check for outdated packages
npm outdated
```

**What to look for**: Missing `package-lock.json`, unpinned versions (`^` or
`*` ranges on security-sensitive packages), unused dependencies.

## Express.js hardening

```javascript
const helmet = require("helmet");
app.use(helmet()); // sets security headers

// Disable X-Powered-By
app.disable("x-powered-by");

// Limit request body size
app.use(express.json({ limit: "1mb" }));

// Rate limiting
const rateLimit = require("express-rate-limit");
app.use(
  "/api/auth",
  rateLimit({
    windowMs: 15 * 60 * 1000,
    max: 100,
  }),
);
```

## Content Security Policy

For frontend applications serving static HTML + vanilla JS:

```
Content-Security-Policy: default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; font-src 'self'; connect-src 'self'; frame-ancestors 'none'; base-uri 'self'; form-action 'self'
```

**What to look for**: `unsafe-inline` in `script-src` (allows XSS payloads),
`unsafe-eval` (allows `eval()`), wildcard `*` sources, missing CSP entirely.

## Cookie security (Express)

```javascript
app.use(
  session({
    cookie: {
      httpOnly: true,
      secure: true, // requires HTTPS
      sameSite: "lax",
      maxAge: 30 * 24 * 60 * 60 * 1000,
    },
    // ...
  }),
);
```

## Secrets management

**What to look for**:

- Hardcoded API keys, tokens, passwords in source code
- `.env` files committed to git (check `.gitignore`)
- Secrets in client-side JavaScript (visible in browser)
- Secrets logged to console or error responses

## npm-specific concerns

- **postinstall scripts**: Malicious packages can execute code at install time
- **typosquatting**: Verify package names carefully
- **Lockfile integrity**: `package-lock.json` should be committed and reviewed

## semgrep rules for JavaScript

Key patterns semgrep catches:

| Pattern                                     | Description                    |
| ------------------------------------------- | ------------------------------ |
| `javascript.browser.security.innerHTML`     | Dynamic innerHTML assignment   |
| `javascript.express.security.injection`     | SQL/NoSQL injection in Express |
| `javascript.lang.security.eval`             | Use of eval()                  |
| `javascript.express.security.open-redirect` | Unvalidated redirects          |
| `javascript.jwt.security.jwt-none-alg`      | JWT with "none" algorithm      |
