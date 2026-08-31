---
name: spark-http-proxy
description: 'Configure, run, and troubleshoot Spark HTTP Proxy, the Traefik-based local development reverse proxy that gives Docker containers clean domain names (for example myapp.spark.loc) over HTTP and HTTPS. Use this skill whenever the user wants to expose a local container under a domain, edit a docker-compose service to add VIRTUAL_HOST/VIRTUAL_PORT or traefik.* labels, generate trusted local certificates with mkcert, set up .loc/.dev domain resolution, or debug why a container is not reachable through the proxy. Trigger on signals like VIRTUAL_HOST, VIRTUAL_PORT, VIRTUAL_PATH, spark-http-proxy, "http-proxy", *.spark.loc / *.loc / *.dev / .local dev domains, "my app is not routing locally", "expose this container", "localhost port chaos", serving a frontend and its API on one origin or one domain to avoid CORS, mounting an app under a path such as /api, "why is /api not routing locally", mkcert / trusted local HTTPS, configure-dns, tailnet peer routing, tailscale, start-with-tailscale, tailscale-peers, "reachable from my other machine", "same hostname on both machines", or a docker-compose.yml in a local project that should be reachable by name. This is for LOCAL DEVELOPMENT only; it is not for configuring a production Traefik deployment.'
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

SparkFabrik workstations are provisioned automatically, so the CLI is normally
already installed: macOS by [sparkdock](https://github.com/sparkfabrik/sparkdock)
and Linux (Arch and Debian/Ubuntu) by the archlinux-ansible-provisioner. Assume
`spark-http-proxy` is available and invoke it directly. Two platform differences
matter: the Linux provisioner installs the CLI but does **not** auto-start the
proxy, and `*.loc` resolves to `127.0.0.1` on macOS but to the Docker bridge
`127.0.0.1` on Linux. See `references/provisioning.md` for the full per-platform
picture and how to update.

1. **Is the proxy running?** Run `spark-http-proxy status`. If it is not running,
   `spark-http-proxy start`.
2. **If the command is genuinely not found** (an unprovisioned machine), don't
   stop at "not installed" — give the user the install commands:

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
| Understand how it's installed / update it        | Per-platform provisioner notes | `references/provisioning.md`     |
| Check dependencies, or uninstall / clean up      | Verify or remove the pieces    | `references/uninstall.md`        |
| Reach a hostname served by another machine       | Start peer routing on both     | `references/peer-routing.md`     |

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

### Two containers on one domain

When a browser-served frontend and its API must share an origin (no CORS, no
preflight, one certificate), give both the same `VIRTUAL_HOST` and mount one
under a path:

```yaml
services:
  frontend:
    environment:
      - VIRTUAL_HOST=myapp.spark.loc
      - VIRTUAL_PORT=5173

  api:
    environment:
      - VIRTUAL_HOST=myapp.spark.loc # the same domain
      - VIRTUAL_PATH=/api # mounted under it
      - VIRTUAL_PORT=3000
```

The page can then call `/api/...` with no host in front of it. Two things to say
when suggesting this: the API must serve the `/api` prefix itself, because nothing
is stripped, and `/api` never captures `/api-docs`, because matching is by path
segment.

Do **not** reach for `traefik.*` labels to achieve this. They work, but adding any
`traefik.` label to a container makes the proxy ignore its `VIRTUAL_HOST`
entirely, so you then own every router by hand.

For multiple domains, wildcards/regex, the full `VIRTUAL_PATH` rules, the native
`traefik.*` label form, and when to prefer labels over `VIRTUAL_HOST`, read
`references/expose-container.md`.

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

| Command                                   | Purpose                                              |
| ----------------------------------------- | ---------------------------------------------------- |
| `start` / `start-with-metrics`            | Start the proxy (optionally with Prometheus/Grafana) |
| `status`                                  | Show running services and the dashboard URL          |
| `restart` / `stop-metrics`                | Restart the stack / stop only monitoring             |
| `start-with-tailscale` / `stop-tailscale` | Start with, or stop, tailnet peer routing            |
| `tailscale-peers [--refresh]`             | Show the last discovery cycle, or run one first      |
| `generate-mkcert <domain>`                | Create trusted certificates for a domain             |
| `configure-dns`                           | Wire system DNS to resolve the proxy TLDs            |
| `show-config`                             | Print current configuration and file locations       |
| `logs [service]`                          | Tail logs (optionally for one service)               |
| `dashboard` / `grafana` / `prometheus`    | Open the respective web UI                           |
| `upgrade` / `self-update`                 | Update images / update the script and compose files  |
| `clean` / `destroy`                       | Stop + remove volumes / remove everything            |

Behavior is tuned with env vars, most usefully `HTTP_PROXY_DNS_TLDS` (default
`loc`) to serve additional TLDs such as `dev`. See `references/dns.md`.

## Hostnames from another machine

A hostname served on one machine can be reached under the same name from the
other machines of the same Tailscale account. Off by default, started per
machine with `start-with-tailscale`, and a local container always wins over a
peer. See `references/peer-routing.md`.

## When something does not work

Routing through this proxy depends on three independent things lining up: the
container is opted in, the proxy has joined the container's network, and DNS
resolves the domain. The failure is almost always one of those. Do not guess —
walk the decision tree in `references/troubleshooting.md`, which maps each
symptom (resolves but not reachable, does not resolve, certificate untrusted,
wrong backend, container ignored) to its cause and fix.
