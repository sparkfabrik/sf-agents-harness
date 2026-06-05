---
name: http-cache-tools
description: HTTP cache debugging tools and techniques. Use when asked to inspect cache headers, debug HTTP responses, use curl for cache analysis, or verify caching behavior. Includes SparkFabrik container context with make drupal-cli and docker compose commands.
---

# HTTP Cache Debugging Tools

Practical tools and commands for inspecting HTTP cache headers and debugging Drupal caching behavior.

## When to Use

- Inspecting cache response headers (X-Drupal-Cache, Cache-Control, etc.)
- Verifying cache hit/miss status
- Debugging why pages aren't caching
- Testing authenticated vs anonymous caching
- Analyzing Vary headers and cache variations

## SparkFabrik Project Context

For container access and service URLs in SparkFabrik projects, see the [pkg-skills](../drupal/pkg-skills/SKILL.md) reference.

**Quick reminder:**

- Inside container: `http://drupal-nginx`
- From host: Use `fs-cli pkg:get-urls` to get external URL

## curl - The Essential Tool

### Basic Header Inspection

```bash
# Get headers only (-I = HEAD request, -s = silent)
curl -sI https://example.com/

# GET request with headers shown (-i includes headers in output)
curl -si https://example.com/

# Follow redirects (-L)
curl -sIL https://example.com/
```

### Cache-Specific Header Filters

```bash
# Filter Drupal cache headers
curl -sI https://example.com/ | grep -iE 'x-drupal|cache-control|age|vary|etag'

# Full cache header analysis
curl -sI https://example.com/ | grep -iE 'x-drupal|cache|age|vary|etag|expires|pragma|last-modified'

# Just Drupal-specific headers
curl -sI https://example.com/ | grep -i 'x-drupal'
```

### Authenticated Requests

```bash
# With session cookie (simulate logged-in user)
curl -sI -H "Cookie: SESSabc123=xyz789" https://example.com/

# With basic auth
curl -sI -u username:password https://example.com/

# With bearer token
curl -sI -H "Authorization: Bearer TOKEN" https://example.com/
```

### Cache Bypass Testing

```bash
# Force cache miss with Cache-Control header
curl -sI -H "Cache-Control: no-cache" https://example.com/

# Add random query string to bypass cache
curl -sI "https://example.com/?nocache=$(date +%s)"

# Pragma no-cache (legacy)
curl -sI -H "Pragma: no-cache" https://example.com/
```

### Timing and Performance

```bash
# Show timing breakdown
curl -sI -w "\n\nTiming:\n  DNS: %{time_namelookup}s\n  Connect: %{time_connect}s\n  TLS: %{time_appconnect}s\n  TTFB: %{time_starttransfer}s\n  Total: %{time_total}s\n" https://example.com/

# Simple total time
curl -sI -w "\nTotal time: %{time_total}s\n" https://example.com/
```

## Examples

### Example 1: Quick Cache Status Check

**Input:** "Check if the homepage is being cached"

**Output:**

```bash
# From SparkFabrik container
make drupal-cli

# Inside container
curl -sI http://drupal-nginx/ | grep -iE 'x-drupal|cache-control'

# Expected output for cached page:
# X-Drupal-Cache: HIT
# X-Drupal-Dynamic-Cache: HIT
# Cache-Control: max-age=3600, public
```

### Example 2: Compare Anonymous vs Authenticated

**Input:** "Check caching difference between anonymous and logged-in users"

**Output:**

```bash
# Anonymous request
echo "=== Anonymous ==="
curl -sI http://drupal-nginx/node/1 | grep -iE 'x-drupal|cache-control|set-cookie'

# Authenticated request (with session cookie)
echo "=== Authenticated ==="
curl -sI -H "Cookie: SESSxyz=abc123" http://drupal-nginx/node/1 | grep -iE 'x-drupal|cache-control'

# Expected:
# Anonymous: X-Drupal-Cache: HIT, Cache-Control: public
# Authenticated: X-Drupal-Dynamic-Cache: HIT, Cache-Control: private
```

### Example 3: Debug UNCACHEABLE Response

**Input:** "Find out why the page shows UNCACHEABLE"

**Output:**

```bash
# Enable debug headers first (in settings.local.php):
# $settings['http.response.debug_cacheability_headers'] = TRUE;

# Then check all cache metadata
curl -sI http://drupal-nginx/node/1 | grep -iE 'x-drupal'

# Look for:
# X-Drupal-Cache-Max-Age: 0  → Something set max-age to 0
# X-Drupal-Cache-Contexts: user  → High-cardinality context
# X-Drupal-Dynamic-Cache: UNCACHEABLE  → Page cannot be cached
```

### Example 4: Test Cache Invalidation

**Input:** "Verify cache clears after content edit"

**Output:**

```bash
# Step 1: Check current cache status
curl -sI http://drupal-nginx/node/1 | grep 'X-Drupal-Cache'
# X-Drupal-Cache: HIT

# Step 2: Edit the node (via UI or drush)
drush php-eval "\Drupal::entityTypeManager()->getStorage('node')->load(1)->save();"

# Step 3: Verify cache miss after invalidation
curl -sI http://drupal-nginx/node/1 | grep 'X-Drupal-Cache'
# X-Drupal-Cache: MISS

# Step 4: Confirm next request is cached
curl -sI http://drupal-nginx/node/1 | grep 'X-Drupal-Cache'
# X-Drupal-Cache: HIT
```

### Example 5: Check Vary Headers

**Input:** "See what the page varies on"

**Output:**

```bash
curl -sI http://drupal-nginx/ | grep -iE 'vary|x-drupal-cache-contexts'

# Example output:
# Vary: Cookie, Accept-Encoding
# X-Drupal-Cache-Contexts: languages:language_interface theme url.path user.permissions

# The Vary header tells proxies/CDNs what to cache separately
# Cache-Contexts show Drupal's internal cache variations
```

### Example 6: Full Debug Script

**Input:** "Give me a complete cache debug for a URL"

**Output:**

```bash
#!/bin/bash
# cache-debug.sh - Run from inside drupal-tools container

URL="${1:-http://drupal-nginx/}"

echo "=== Cache Debug for: $URL ==="
echo ""

echo "--- Response Headers ---"
curl -sI "$URL" | grep -iE 'http/|x-drupal|cache|vary|age|etag|expires'

echo ""
echo "--- Timing ---"
curl -sI -w "DNS: %{time_namelookup}s | Connect: %{time_connect}s | TTFB: %{time_starttransfer}s | Total: %{time_total}s\n" -o /dev/null "$URL"

echo ""
echo "--- Cache Status Summary ---"
CACHE=$(curl -sI "$URL" | grep -i 'X-Drupal-Cache:' | cut -d' ' -f2 | tr -d '\r')
DYNAMIC=$(curl -sI "$URL" | grep -i 'X-Drupal-Dynamic-Cache:' | cut -d' ' -f2 | tr -d '\r')

echo "Page Cache: ${CACHE:-N/A}"
echo "Dynamic Cache: ${DYNAMIC:-N/A}"

if [ "$DYNAMIC" = "UNCACHEABLE" ]; then
  echo "⚠️  WARNING: Page is UNCACHEABLE - check for max-age:0"
fi
```

```bash
# Usage from SparkFabrik project
docker compose run --rm -it drupal-tools bash -c 'URL="http://drupal-nginx/node/1"; curl -sI "$URL" | grep -iE "x-drupal|cache"'
```

### Example 7: Watch Cache Headers in Real-Time

**Input:** "Monitor cache status during development"

**Output:**

```bash
# Watch cache status every 2 seconds
watch -n 2 'curl -sI http://drupal-nginx/ | grep -iE "x-drupal|cache-control"'

# Or with timestamp
while true; do
  echo "=== $(date) ==="
  curl -sI http://drupal-nginx/ | grep -iE 'x-drupal'
  sleep 5
done
```

### Example 8: Test Multiple URLs

**Input:** "Check cache status for multiple pages"

**Output:**

```bash
# List of URLs to check
URLS=(
  "http://drupal-nginx/"
  "http://drupal-nginx/node/1"
  "http://drupal-nginx/admin"
  "http://drupal-nginx/user/login"
)

for url in "${URLS[@]}"; do
  echo "=== $url ==="
  curl -sI "$url" | grep -iE 'x-drupal-cache|x-drupal-dynamic' || echo "No cache headers"
  echo ""
done
```

## Alternative to curl: httpie

httpie provides more readable syntax with colorized output.

### Installation

If not present in the `drupal-tools` container:

```bash
# Enter container as root
make drupal-cli-root

# Install httpie
apk add --no-cache httpie
```

### Usage

```bash
# Headers only
http HEAD http://drupal-nginx/

# With specific headers
http http://drupal-nginx/ 'Cookie:SESSxyz=abc'

# Filter headers
http --print=h http://drupal-nginx/ | grep -i cache

# Compare anonymous vs authenticated
http --print=h HEAD http://drupal-nginx/node/1
http --print=h HEAD http://drupal-nginx/node/1 'Cookie:SESSxyz=abc'
```

## Browser DevTools

For visual debugging:

1. **Network tab** → Select request → Headers section
2. **Filter by:** `cache` or `x-drupal`
3. **Disable cache:** Network tab → Check "Disable cache"
4. **Preserve log:** Keep requests across navigation

### DevTools Cache Headers to Check

| Header                   | Location | Meaning                       |
| ------------------------ | -------- | ----------------------------- |
| `X-Drupal-Cache`         | Response | Page Cache status             |
| `X-Drupal-Dynamic-Cache` | Response | Dynamic Cache status          |
| `Cache-Control`          | Response | Browser/proxy caching rules   |
| `Age`                    | Response | Seconds since cached by proxy |
| `Vary`                   | Response | What causes cache variations  |

## Quick Reference

| Task               | Command                                            |
| ------------------ | -------------------------------------------------- |
| Check cache status | `curl -sI URL \| grep -i x-drupal`                 |
| Full headers       | `curl -sI URL`                                     |
| Authenticated      | `curl -sI -H "Cookie: SESS=x" URL`                 |
| Bypass cache       | `curl -sI -H "Cache-Control: no-cache" URL`        |
| Timing             | `curl -sI -w "TTFB: %{time_starttransfer}s\n" URL` |
| Follow redirects   | `curl -sIL URL`                                    |

## Anonymous vs Authenticated Cache Analysis

This section helps analyze how Drupal caches pages for anonymous and authenticated users.

### Step-by-Step Analysis

#### 1. Get a Valid Session Cookie

First, log in to Drupal and extract the session cookie:

```bash
# Option A: From browser DevTools
# 1. Log in to Drupal
# 2. Open DevTools → Application → Cookies
# 3. Copy the SESS* cookie value (e.g., SESSabc123=xyz789)

# Option B: Via curl (if you have credentials)
curl -c cookies.txt -X POST \
  -d "name=admin&pass=password&form_id=user_login_form&op=Log+in" \
  http://drupal-nginx/user/login

# Extract session cookie
cat cookies.txt | grep SESS
```

#### 2. Compare Anonymous vs Authenticated Headers

```bash
URL="http://drupal-nginx/node/1"

echo "========== ANONYMOUS REQUEST =========="
curl -sI "$URL" | grep -iE 'http/|x-drupal|cache-control|set-cookie|vary'

echo ""
echo "========== AUTHENTICATED REQUEST =========="
curl -sI -H "Cookie: SESSxxxxxxx=yyyyyyyy" "$URL" | grep -iE 'http/|x-drupal|cache-control|vary'
```

#### 3. Interpret the Results

**Key headers to analyze:**

| Header                   | Anonymous (expected)      | Authenticated (expected)       | Meaning                         |
| ------------------------ | ------------------------- | ------------------------------ | ------------------------------- |
| `X-Drupal-Cache`         | `HIT` or `MISS`           | Not present                    | Page Cache (only for anonymous) |
| `X-Drupal-Dynamic-Cache` | `HIT`                     | `HIT` or `UNCACHEABLE`         | Dynamic Page Cache              |
| `Cache-Control`          | `max-age=X, public`       | `max-age=0, private, no-cache` | Browser/proxy caching           |
| `Vary`                   | `Cookie, Accept-Encoding` | `Cookie, Accept-Encoding`      | Cache variations                |
| `Set-Cookie`             | May set session           | Should not set new session     | Session handling                |

### Understanding Cache Behavior

#### Scenario 1: Optimal Caching (Anonymous)

```
X-Drupal-Cache: HIT
X-Drupal-Dynamic-Cache: HIT
Cache-Control: max-age=3600, public
```

✅ **Good:** Page is fully cached, served from Page Cache.

#### Scenario 2: Dynamic Cache Only (Anonymous)

```
X-Drupal-Cache: MISS
X-Drupal-Dynamic-Cache: HIT
Cache-Control: max-age=3600, public
```

⚠️ **Partial:** Page uses Dynamic Cache but not Page Cache. Check if there are session cookies being set.

#### Scenario 3: Uncacheable (Anonymous)

```
X-Drupal-Cache: MISS
X-Drupal-Dynamic-Cache: UNCACHEABLE
Cache-Control: must-revalidate, no-cache, private
```

❌ **Problem:** Page cannot be cached. Check for:

- `max-age: 0` on render elements
- High-cardinality cache contexts (e.g., `user`)
- Session being started unexpectedly

#### Scenario 4: Authenticated User (Expected)

```
X-Drupal-Dynamic-Cache: HIT
Cache-Control: max-age=0, private, no-cache
```

✅ **Expected:** Authenticated pages should be private, Dynamic Cache can still help.

#### Scenario 5: Authenticated User Uncacheable

```
X-Drupal-Dynamic-Cache: UNCACHEABLE
Cache-Control: must-revalidate, no-cache, private
```

⚠️ **Check:** Even for authenticated users, Dynamic Cache should work. Look for `max-age: 0` issues.

### Full Comparison Script

```bash
#!/bin/bash
# cache-compare.sh - Compare anonymous vs authenticated caching

URL="${1:-http://drupal-nginx/}"
SESSION_COOKIE="${2:-}"

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║  Cache Analysis: $URL"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

echo "┌─────────────────────────────────────────────────────────────────┐"
echo "│ ANONYMOUS REQUEST                                               │"
echo "└─────────────────────────────────────────────────────────────────┘"
ANON_HEADERS=$(curl -sI "$URL")
echo "$ANON_HEADERS" | grep -iE 'http/|x-drupal|cache-control|vary|set-cookie'

ANON_PAGE_CACHE=$(echo "$ANON_HEADERS" | grep -i 'X-Drupal-Cache:' | awk '{print $2}' | tr -d '\r')
ANON_DYN_CACHE=$(echo "$ANON_HEADERS" | grep -i 'X-Drupal-Dynamic-Cache:' | awk '{print $2}' | tr -d '\r')
ANON_CACHE_CTRL=$(echo "$ANON_HEADERS" | grep -i 'Cache-Control:' | cut -d':' -f2 | tr -d '\r')

echo ""
echo "Summary:"
echo "  Page Cache:    ${ANON_PAGE_CACHE:-N/A}"
echo "  Dynamic Cache: ${ANON_DYN_CACHE:-N/A}"
echo "  Cache-Control: ${ANON_CACHE_CTRL:-N/A}"

if [ -n "$SESSION_COOKIE" ]; then
  echo ""
  echo "┌─────────────────────────────────────────────────────────────────┐"
  echo "│ AUTHENTICATED REQUEST                                          │"
  echo "└─────────────────────────────────────────────────────────────────┘"
  AUTH_HEADERS=$(curl -sI -H "Cookie: $SESSION_COOKIE" "$URL")
  echo "$AUTH_HEADERS" | grep -iE 'http/|x-drupal|cache-control|vary'

  AUTH_DYN_CACHE=$(echo "$AUTH_HEADERS" | grep -i 'X-Drupal-Dynamic-Cache:' | awk '{print $2}' | tr -d '\r')
  AUTH_CACHE_CTRL=$(echo "$AUTH_HEADERS" | grep -i 'Cache-Control:' | cut -d':' -f2 | tr -d '\r')

  echo ""
  echo "Summary:"
  echo "  Dynamic Cache: ${AUTH_DYN_CACHE:-N/A}"
  echo "  Cache-Control: ${AUTH_CACHE_CTRL:-N/A}"
fi

echo ""
echo "┌─────────────────────────────────────────────────────────────────┐"
echo "│ DIAGNOSIS                                                       │"
echo "└─────────────────────────────────────────────────────────────────┘"

# Anonymous diagnosis
if [ "$ANON_PAGE_CACHE" = "HIT" ]; then
  echo "✅ Anonymous: Page Cache is working"
elif [ "$ANON_DYN_CACHE" = "HIT" ]; then
  echo "⚠️  Anonymous: Only Dynamic Cache working (Page Cache MISS)"
elif [ "$ANON_DYN_CACHE" = "UNCACHEABLE" ]; then
  echo "❌ Anonymous: Page is UNCACHEABLE - needs investigation"
else
  echo "⚠️  Anonymous: Cache status unclear"
fi

# Authenticated diagnosis
if [ -n "$SESSION_COOKIE" ]; then
  if [ "$AUTH_DYN_CACHE" = "HIT" ]; then
    echo "✅ Authenticated: Dynamic Cache is working"
  elif [ "$AUTH_DYN_CACHE" = "UNCACHEABLE" ]; then
    echo "⚠️  Authenticated: Dynamic Cache not working"
  fi

  if echo "$AUTH_CACHE_CTRL" | grep -q "private"; then
    echo "✅ Authenticated: Correctly marked as private"
  else
    echo "❌ Authenticated: Should be private but isn't!"
  fi
fi
```

**Usage:**

```bash
# Anonymous only
./cache-compare.sh http://drupal-nginx/node/1

# With authenticated comparison
./cache-compare.sh http://drupal-nginx/node/1 "SESSabc123=xyz789"
```

### Common Issues and Solutions

| Symptom                            | Likely Cause                    | Solution                                                 |
| ---------------------------------- | ------------------------------- | -------------------------------------------------------- |
| Anonymous gets `UNCACHEABLE`       | Something sets `max-age: 0`     | Enable debug headers, check for bad cache metadata       |
| Anonymous gets `Set-Cookie`        | Session started for anonymous   | Check for code that calls `\Drupal::currentUser()` early |
| Anonymous `Cache-Control: private` | Session or user context         | Look for `user` cache context being added                |
| Page Cache always `MISS`           | Vary on Cookie + session exists | Ensure anonymous users don't get sessions                |
| Authenticated `UNCACHEABLE`        | `max-age: 0` in render array    | Find element setting zero max-age                        |

### Debug Headers

Enable detailed cache debug headers in `settings.local.php`:

```php
$settings['http.response.debug_cacheability_headers'] = TRUE;
```

This exposes additional headers:

- `X-Drupal-Cache-Tags` - Cache tags for invalidation
- `X-Drupal-Cache-Contexts` - What the page varies on
- `X-Drupal-Cache-Max-Age` - Minimum max-age from all elements

## Container Quick Commands

```bash
# SparkFabrik: Open interactive shell
make drupal-cli

# SparkFabrik: One-off command
docker compose run --rm -it drupal-tools curl -sI http://drupal-nginx/

# Generic Docker Compose
docker compose exec php curl -sI http://localhost/
```
