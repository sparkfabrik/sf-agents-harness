---
name: spark-http-proxy
description: 'Configure, run, and troubleshoot Spark HTTP Proxy, the Traefik-based local development reverse proxy that gives Docker containers clean domain names (for example myapp.spark.loc) over HTTP and HTTPS. Use this skill whenever the user wants to expose a local container under a domain, edit a docker-compose service to add VIRTUAL_HOST/VIRTUAL_PORT or traefik.* labels, generate trusted local certificates with mkcert, set up .loc/.dev domain resolution, or debug why a container is not reachable through the proxy. Trigger on signals like VIRTUAL_HOST, VIRTUAL_PORT, spark-http-proxy, "http-proxy", *.spark.loc / *.loc / *.dev / .local dev domains, "my app is not routing locally", "expose this container", "localhost port chaos", mkcert / trusted local HTTPS, configure-dns, or a docker-compose.yml in a local project that should be reachable by name. This is for LOCAL DEVELOPMENT only; it is not for configuring a production Traefik deployment.'
---

# Spark HTTP Proxy

Spark HTTP Proxy is a local-development reverse proxy built on Traefik. Adding
`VIRTUAL_HOST=myapp.spark.loc` (or native `traefik.*` labels) to any container
makes it reachable at `http://myapp.spark.loc` and `https://myapp.spark.loc` with
no port juggling and no `/etc/hosts` editing. Its built-in DNS server resolves the
configured TLDs to localhost, and `mkcert` integration provides browser-trusted
HTTPS.

Use this skill to **act** (edit a project's `compose.yml`, generate certificates,
configure DNS) and to **guide** a user who needs help. It is for local
development only, never a production Traefik setup.

## First, orient yourself

The `spark-http-proxy` CLI is installed on every SparkFabrik machine, so assume
it is available and invoke it directly rather than checking for it first.

1. **Is the proxy running?** Run `spark-http-proxy status`. If it is not running,
   `spark-http-proxy start`.
2. **If the command is genuinely not found**, this is a non-standard machine.
   Don't stop at "not installed" — give the user the install commands:

   ```bash
   # One-liner installer
   bash <(curl -fsSL https://raw.githubusercontent.com/sparkfabrik/http-proxy/main/bin/install.sh)
   ```

   Or the manual route (clone, symlink onto `PATH`, enable completion):

   ```bash
   mkdir -p "${HOME}/.local/spark/http-proxy"
   git clone git@github.com:sparkfabrik/http-proxy.git "${HOME}/.local/spark/http-proxy/src"
   sudo ln -s "${HOME}/.local/spark/http-proxy/src/bin/spark-http-proxy" /usr/local/bin/spark-http-proxy
   sudo chmod +x /usr/local/bin/spark-http-proxy
   spark-http-proxy install-completion
   ```

   Then `spark-http-proxy start`. Full instructions:
   [project README](https://github.com/sparkfabrik/http-proxy#quick-start).

3. **What does the user actually need?** Map it to one task below and read only
   the reference you need. Do not load every reference; each is self-contained.

| The user wants to…                               | Do this                        | Read                             |
| ------------------------------------------------ | ------------------------------ | -------------------------------- |
| Make a container reachable at a domain           | Edit its `compose.yml` service | `references/expose-container.md` |
| Get trusted HTTPS / fix certificate warnings     | Run `generate-mkcert`          | `references/certificates.md`     |
| Resolve `*.loc` (or other TLDs) on their machine | Run `configure-dns`            | `references/dns.md`              |
| Fix "it's not working / not reachable"           | Walk the decision tree         | `references/troubleshooting.md`  |
| Check dependencies, or uninstall / clean up      | Verify or remove the pieces    | `references/uninstall.md`        |

Dependencies: Docker is required (the proxy is a Docker stack; `spark-http-proxy
self-test` checks the daemon). `mkcert` is only needed for trusted HTTPS and is
installed automatically by `generate-mkcert` — you rarely check it yourself. See
`references/uninstall.md` for how to verify what is installed, where certificates
and config live, and how to uninstall.

## The most common task: expose a container

Most requests reduce to adding routing to a service in the project's
`docker-compose.yml`. The quick path is the dinghy-style env var:

```yaml
services:
  myapp:
    image: nginx:alpine
    environment:
      - VIRTUAL_HOST=myapp.spark.loc # the domain to expose
      - VIRTUAL_PORT=8080 # optional; the backend port the app listens on
```

That is enough: the proxy auto-discovers the container, creates **both** HTTP and
HTTPS routes, and joins the container's Docker network. The user can then open
`https://myapp.spark.loc`.

> **SparkFabrik convention:** name local dev environments under `*.spark.loc`
> (for example `myapp.spark.loc`, `api.spark.loc`). The proxy works with any
> domain, so honor an existing project's scheme if it already uses one, but
> default to `*.spark.loc` for new local names.

Two things to know before editing:

- **The proxy is opt-in** (`exposedByDefault: false`). Only containers with
  `VIRTUAL_HOST` or `traefik.*` labels are touched; everything else is ignored.
  So adding the env var is both necessary and sufficient — there is no global
  config to change.
- **`VIRTUAL_PORT` is the port the app listens on inside the container**, not a
  published host port. You usually do not need to publish ports at all once the
  app is behind the proxy.

For multiple domains, wildcards/regex, the native `traefik.*` label form, and
when to prefer labels over `VIRTUAL_HOST`, read `references/expose-container.md`.

## Certificates (trusted local HTTPS)

HTTPS works out of the box with a self-signed certificate (browser warning). For
a trusted certificate, generate one with mkcert — it installs mkcert if needed,
writes the cert, and restarts Traefik:

```bash
# Wildcard for the SparkFabrik convention: covers myapp.spark.loc, api.spark.loc, …
spark-http-proxy generate-mkcert "*.spark.loc"

# Or a specific host
spark-http-proxy generate-mkcert "myapp.spark.loc"
```

The key gotcha: a wildcard covers exactly one label level, so match it to the
level directly above the host. `*.spark.loc` covers `myapp.spark.loc` but **not**
a deeper host like `drupal.client.spark.loc` — that needs `*.client.spark.loc`.
And `*.loc` does **not** cover `myapp.spark.loc` at all, which is why the
convention's base certificate is `*.spark.loc`, not `*.loc`. Full details, the
cert directory, SNI matching, and manual generation are in
`references/certificates.md`.

## Guiding a user

When the user just wants to understand the tool rather than have you change
files, run `spark-http-proxy help` for the authoritative command list and explain
the relevant commands. The lifecycle and utility commands:

| Command                                | Purpose                                              |
| -------------------------------------- | ---------------------------------------------------- |
| `start` / `start-with-metrics`         | Start the proxy (optionally with Prometheus/Grafana) |
| `status`                               | Show running services and the dashboard URL          |
| `restart` / `stop-metrics`             | Restart the stack / stop only monitoring             |
| `generate-mkcert <domain>`             | Create trusted certificates for a domain             |
| `configure-dns`                        | Wire system DNS to resolve the proxy TLDs            |
| `show-config`                          | Print current configuration and file locations       |
| `logs [service]`                       | Tail logs (optionally for one service)               |
| `dashboard` / `grafana` / `prometheus` | Open the respective web UI                           |
| `upgrade` / `self-update`              | Update images / update the script and compose files  |
| `clean` / `destroy`                    | Stop + remove volumes / remove everything            |

Behavior is tuned with env vars, most usefully `HTTP_PROXY_DNS_TLDS` (default
`loc`) to serve additional TLDs such as `dev`. See `references/dns.md`.

## When something does not work

Routing through this proxy depends on three independent things lining up: the
container is opted in, the proxy has joined the container's network, and DNS
resolves the domain. The failure is almost always one of those. Do not guess —
walk the decision tree in `references/troubleshooting.md`, which maps each
symptom (resolves but not reachable, does not resolve, certificate untrusted,
wrong backend, container ignored) to its cause and fix.
