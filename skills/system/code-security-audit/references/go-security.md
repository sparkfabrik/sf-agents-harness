# Go Security Patterns

Common vulnerability patterns and hardening guidance for Go web applications.

## SQL injection

Go's `database/sql` package uses `?` placeholders. The most common mistake is
string concatenation instead of parameterized queries.

### Vulnerable

```go
query := "SELECT * FROM users WHERE id = " + userInput
db.Query(query)
```

### Safe

```go
db.Query("SELECT * FROM users WHERE id = ?", userInput)
```

**What to look for**: `fmt.Sprintf` or `+` concatenation used to build SQL
strings. Search for patterns like:

```
fmt.Sprintf("SELECT.*FROM
"SELECT.*" \+
"INSERT.*" \+
"UPDATE.*" \+
"DELETE.*" \+
```

## Command injection

### Vulnerable

```go
cmd := exec.Command("sh", "-c", "echo "+userInput)
```

### Safe

```go
cmd := exec.Command("echo", userInput)  // no shell interpretation
```

**What to look for**: `exec.Command("sh", "-c", ...)` or `exec.Command("bash",
"-c", ...)` with user-controlled arguments.

## Path traversal

### Vulnerable

```go
http.ServeFile(w, r, filepath.Join(baseDir, r.URL.Path))
```

### Safe

```go
cleanPath := filepath.Clean(r.URL.Path)
if strings.Contains(cleanPath, "..") {
    http.Error(w, "invalid path", http.StatusBadRequest)
    return
}
fullPath := filepath.Join(baseDir, cleanPath)
if !strings.HasPrefix(fullPath, baseDir) {
    http.Error(w, "invalid path", http.StatusBadRequest)
    return
}
http.ServeFile(w, r, fullPath)
```

## XSS in Go templates

Go's `html/template` package auto-escapes by default. Vulnerabilities appear
when using `text/template` for HTML or when using `template.HTML()` to bypass
escaping.

### Vulnerable

```go
import "text/template"  // no auto-escaping!

tmpl.Execute(w, template.HTML(userInput))  // explicitly bypasses escaping
```

### Safe

```go
import "html/template"  // auto-escapes

tmpl.Execute(w, userInput)  // auto-escaped
```

**What to look for**: `text/template` imported for HTML rendering,
`template.HTML()`, `template.JS()`, `template.CSS()` casts with user input.

## Cookie security

```go
http.SetCookie(w, &http.Cookie{
    Name:     "session",
    Value:    token,
    HttpOnly: true,      // prevent JS access
    Secure:   true,      // HTTPS only
    SameSite: http.SameSiteLaxMode,  // CSRF protection
    Path:     "/",
    MaxAge:   86400 * 30,
})
```

**What to look for**: Cookies set without `HttpOnly`, `Secure`, or `SameSite`.

## HTTP server hardening

```go
srv := &http.Server{
    Addr:              ":8080",
    ReadTimeout:       10 * time.Second,
    ReadHeaderTimeout: 5 * time.Second,
    WriteTimeout:      30 * time.Second,
    IdleTimeout:       120 * time.Second,
    MaxHeaderBytes:    1 << 20,  // 1 MB
}
```

**What to look for**: `http.ListenAndServe` without timeout configuration
(vulnerable to slowloris).

## Open redirect

### Vulnerable

```go
redirectURL := r.URL.Query().Get("redirect")
http.Redirect(w, r, redirectURL, http.StatusFound)
```

### Safe

```go
redirectURL := r.URL.Query().Get("redirect")
parsed, err := url.Parse(redirectURL)
if err != nil || parsed.Host != "" {
    http.Error(w, "invalid redirect", http.StatusBadRequest)
    return
}
http.Redirect(w, r, redirectURL, http.StatusFound)
```

## HMAC / token validation

### Vulnerable (timing attack)

```go
if token == expectedToken {  // constant-time comparison NOT used
```

### Safe

```go
if !hmac.Equal([]byte(token), []byte(expectedToken)) {
```

## Race conditions

Go's goroutine model makes race conditions common. Use `-race` flag during
testing and look for shared mutable state.

```bash
go test -race ./...
```

**What to look for**: Global variables mutated from HTTP handlers, map access
from multiple goroutines without `sync.Mutex` or `sync.Map`.

## gosec rules reference

Key gosec rules to watch for:

| Rule | Description                                 |
| ---- | ------------------------------------------- |
| G101 | Hardcoded credentials                       |
| G102 | Binding to all interfaces                   |
| G104 | Unhandled errors                            |
| G107 | URL provided to HTTP request as taint input |
| G108 | Profiling endpoint exposed                  |
| G110 | Decompression bomb                          |
| G201 | SQL string concatenation                    |
| G202 | SQL string formatting                       |
| G301 | Poor file permissions on directory creation |
| G302 | Poor file permissions on file creation      |
| G304 | File path provided as taint input           |
| G401 | Use of weak crypto (MD5, SHA1 for security) |
| G501 | Blacklisted crypto import                   |
