# Certificates (trusted local HTTPS)

Every `VIRTUAL_HOST` (and label-based HTTPS router) gets an HTTPS route
automatically. Without a matching certificate, Traefik serves a self-signed one
and the browser shows a warning. To make local HTTPS trusted, generate a
certificate with mkcert.

## Generate with the CLI (preferred)

```bash
# SparkFabrik convention: covers myapp.spark.loc, api.spark.loc, …
spark-http-proxy generate-mkcert "*.spark.loc"

# A specific host
spark-http-proxy generate-mkcert "myapp.spark.loc"

# A deeper level, if a project nests further (see the gotcha below)
spark-http-proxy generate-mkcert "*.project.spark.loc"
```

`generate-mkcert` does everything: installs mkcert if missing (Homebrew on macOS,
pacman on Arch; on other Linux distros it prints manual install steps), runs
`mkcert -install` to add the local CA to the system trust store, creates the
certificate directory `~/.local/spark/http-proxy/certs`, writes the cert with a
safe filename, and **restarts Traefik** so it loads immediately. No config file
editing is needed — the Traefik entrypoint scans the certs directory and
generates the TLS config (`/traefik/dynamic/auto-tls.yml`). To check or remove
mkcert, the certs, or the CA, see `uninstall.md`.

## The wildcard nesting gotcha

A wildcard certificate covers exactly **one** label level. Match the wildcard to
the level directly above the host:

- `*.spark.loc` covers `myapp.spark.loc`, `api.spark.loc`.
- `*.spark.loc` does **not** cover a deeper host like `drupal.client.spark.loc`.
  For that, the certificate must be **`*.client.spark.loc`** — the wildcard sits
  one level above the host.
- `*.loc` does **not** cover `myapp.spark.loc` at all — `spark.loc` is already a
  level below `loc`. This is why the SparkFabrik convention's base certificate is
  `*.spark.loc`, not `*.loc`.

Rule of thumb: for `<name>.<parent>`, generate `*.<parent>`. So a per-client
nested scheme like `<app>.<client>.spark.loc` needs `*.<client>.spark.loc`:

```bash
spark-http-proxy generate-mkcert "*.client.spark.loc"   # covers drupal.client.spark.loc, api.client.spark.loc, …
```

If a user reports a certificate warning on a nested name while a broader wildcard
exists, this mismatch is almost always the cause: generate the wildcard one level
above the host.

## How matching works (SNI)

Traefik selects a certificate per request using Server Name Indication: it reads
the requested hostname and picks the certificate whose Subject Alternative Names
match. If none match, it falls back to a generated self-signed certificate (the
warning case). The startup logs list which domains each loaded certificate
covers — useful when diagnosing a mismatch.

## Manual generation (alternative)

If you would rather drive mkcert directly:

```bash
mkcert -install                                   # install the local CA once
mkdir -p ~/.local/spark/http-proxy/certs
mkcert -cert-file ~/.local/spark/http-proxy/certs/wildcard.spark.loc.pem \
       -key-file  ~/.local/spark/http-proxy/certs/wildcard.spark.loc-key.pem \
       "*.spark.loc"
docker compose restart                            # reload certs (CLI does this for you)
```

The cert and key go in `~/.local/spark/http-proxy/certs`, which Traefik mounts
read-only. After dropping files there manually, restart the proxy so they load.
