# Certificates (trusted local HTTPS)

Every `VIRTUAL_HOST` (and label-based HTTPS router) gets an HTTPS route
automatically. Without a matching certificate, Traefik serves a self-signed one
and the browser shows a warning. To make local HTTPS trusted, generate a
certificate with mkcert.

## The `certs` commands

All certificate work is under one topic. `spark-http-proxy certs help` prints it.

| Command                    | Does                                                                 |
| -------------------------- | -------------------------------------------------------------------- |
| `certs list`               | Table of installed certificates and the files holding each one       |
| `certs describe <domain>`  | What one certificate covers, its dates, issuer, whether it is served |
| `certs generate <domain>`  | Generate with mkcert and apply to the running proxy, no restart      |
| `certs delete <domain>...` | Remove certificate and key, one confirmation, apply to the proxy     |

The former names `generate-mkcert`, `list-certs` and `remove-cert` still run and
print a deprecation warning on stderr naming the replacement. Seeing
`list-certs is deprecated, use: spark-http-proxy certs list` in a user's terminal
is expected on an up-to-date CLI, not a sign of a broken install. Write the
`certs` form.

## Generate with the CLI (preferred)

```bash
# SparkFabrik convention: covers myapp.spark.loc, api.spark.loc, …
spark-http-proxy certs generate "*.spark.loc"

# A specific host
spark-http-proxy certs generate "myapp.spark.loc"

# A deeper level, if a project nests further (see the gotcha below)
spark-http-proxy certs generate "*.project.spark.loc"
```

`certs generate` does everything: installs mkcert if missing (Homebrew on macOS,
pacman on Arch; on other Linux distros it prints manual install steps), runs
`mkcert -install` to add the local CA to the system trust store, creates the
certificate directory `~/.local/spark/http-proxy/certs`, writes the cert with a
safe filename, and applies it to the running proxy **without a restart**, so
nothing else the proxy serves drops a connection. No config file editing is
needed: the Traefik entrypoint scans the certs directory and generates the TLS
config (`/traefik/dynamic/auto-tls.yml`). To check or remove mkcert, the certs,
or the CA, see `uninstall.md`.

## List, describe, delete

`certs list` is the inventory. The directory is printed once, then one row per
certificate. A wildcard is stored as `_wildcard_`, and a key that is not beside
its certificate shows as `missing`. It needs neither Docker nor the proxy:

```text
Certificates in ~/.local/spark/http-proxy/certs

DOMAIN                    CERTIFICATE                   KEY
api.spark.loc             api.spark.loc.pem             api.spark.loc-key.pem
*.spark.loc               _wildcard_.spark.loc.pem      _wildcard_.spark.loc-key.pem

2 certificates. Remove one with: spark-http-proxy certs delete '*.spark.loc'
```

`certs describe` reads one certificate with openssl. Give it a hostname rather
than a certificate name and it finds the certificate covering it, or says why
none does. This is the first command to run on a certificate warning:

```bash
spark-http-proxy certs describe "*.spark.loc"        # the certificate itself
spark-http-proxy certs describe "app.spark.loc"      # covered by *.spark.loc, shows it
spark-http-proxy certs describe "a.b.spark.loc"      # not covered, explains why
```

```text
*.spark.loc
  certificate    ~/.local/spark/http-proxy/certs/_wildcard_.spark.loc.pem
  private key    ~/.local/spark/http-proxy/certs/_wildcard_.spark.loc-key.pem
  covers         *.spark.loc
  valid          2025-07-13 to 2027-10-13
  issued by      mkcert paolo@workstation
  served         yes, by the running proxy
```

`served` is read from the running proxy; with the proxy stopped it says so. If
`describe` stops with a message about openssl, that machine lacks a usable
`openssl` (sparkdock installs it as `openssl@3`); `list`, `generate` and `delete`
do not need it.

`certs delete` takes the same domains that were passed to `generate`, wildcards
included, lists every match, reports any it cannot find, asks once, and applies
the change to the running proxy. It refuses to delete without a terminal to
confirm on, so it cannot be scripted into silently removing certificates.

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
spark-http-proxy certs generate "*.client.spark.loc"   # covers drupal.client.spark.loc, api.client.spark.loc, …
```

If a user reports a certificate warning on a nested name while a broader wildcard
exists, this mismatch is almost always the cause. `spark-http-proxy certs
describe <the hostname>` confirms it: it names the wildcard that falls one label
short and prints the `certs generate` command for the one that would cover it.

## How matching works (SNI)

Traefik selects a certificate per request using Server Name Indication: it reads
the requested hostname and picks the certificate whose Subject Alternative Names
match. If none match, it falls back to a generated self-signed certificate (the
warning case). The startup logs list which domains each loaded certificate
covers — useful when diagnosing a mismatch.

A certificate therefore covers a **hostname**, never a path. A container mounted
under a path with `VIRTUAL_PATH` is served by the certificate of the domain it
sits on and needs none of its own. Passing a path to the certificate commands is
refused:

```bash
spark-http-proxy certs generate myapp.spark.loc       # correct
spark-http-proxy certs generate myapp.spark.loc/api   # refused
```

## Manual generation (alternative)

If you would rather drive mkcert directly:

```bash
mkcert -install                                   # install the local CA once
mkdir -p ~/.local/spark/http-proxy/certs
mkcert -cert-file ~/.local/spark/http-proxy/certs/wildcard.spark.loc.pem \
       -key-file  ~/.local/spark/http-proxy/certs/wildcard.spark.loc-key.pem \
       "*.spark.loc"
spark-http-proxy restart                          # a hand-written cert is applied on restart
```

The cert and key go in `~/.local/spark/http-proxy/certs`, which Traefik mounts
read-only. After dropping files there manually, restart the proxy so they load;
certificates made with `certs generate` are applied without one.
