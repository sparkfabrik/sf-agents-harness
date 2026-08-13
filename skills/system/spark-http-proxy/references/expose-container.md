# Exposing a container

There are two ways to make a container reachable through the proxy. Both produce
HTTP and HTTPS routes and both require nothing more than editing the container's
definition — the proxy discovers the change automatically.

> The Compose file may be named `compose.yaml`, `compose.yml`, or the legacy
> `docker-compose.yml` / `docker-compose.yaml`. These are the same thing to Docker
> Compose v2 — edit whichever file the project already has rather than creating a
> second one.

## Path 1: `VIRTUAL_HOST` (the quick path)

Add environment variables to the service. Best for the common case.

```yaml
services:
  myapp:
    image: nginx:alpine
    environment:
      - VIRTUAL_HOST=myapp.spark.loc
      - VIRTUAL_PORT=8080 # optional
```

> SparkFabrik names local dev environments under `*.spark.loc` by default. Other
> conventions work too; match an existing project's scheme if it has one.

- **`VIRTUAL_HOST`** — the domain(s) to route to this container.
- **`VIRTUAL_PORT`** — the port the application listens on **inside** the
  container. Optional: if omitted, the proxy uses the lowest exposed TCP port,
  falling back to `80`. Set it explicitly when the app listens on a non-obvious
  port or the image exposes several.
- **`VIRTUAL_PATH`** — optional. Mounts this container under a path of its
  `VIRTUAL_HOST` instead of at the root, so several containers can share one
  domain. See [Sharing one domain](#sharing-one-domain-with-virtual_path).

### Multiple domains, wildcards, regex

`VIRTUAL_HOST` accepts more than a single host:

| Form                       | Example                                    | Routes                         |
| -------------------------- | ------------------------------------------ | ------------------------------ |
| Single                     | `VIRTUAL_HOST=myapp.spark.loc`             | `myapp.spark.loc`              |
| Multiple (comma-separated) | `VIRTUAL_HOST=app.spark.loc,api.spark.loc` | both hosts, one shared backend |
| Wildcard                   | `VIRTUAL_HOST=*.myapp.spark.loc`           | any single-level subdomain     |
| Regex (prefix with `~`)    | `VIRTUAL_HOST=~^api\..*\.spark\.loc$`      | hosts matching the pattern     |

A per-host port is also accepted as `host:port` (for example
`VIRTUAL_HOST=myapp.spark.loc:8080`).

`VIRTUAL_PATH` is **not** another entry in this table. It is a separate variable
that changes where on the domain the container answers, and it combines with any
of the forms above.

### Sharing one domain with `VIRTUAL_PATH`

Use this when a browser-served frontend and its API must be on **one origin**: no
CORS, no preflight, one certificate, and the page can call `/api/...` with no host
in front of it. Point both containers at the same `VIRTUAL_HOST` and give the one
that should sit under a path a `VIRTUAL_PATH`:

```yaml
services:
  frontend:
    image: node:22-alpine
    environment:
      - VIRTUAL_HOST=myapp.spark.loc
      - VIRTUAL_PORT=5173

  api:
    image: node:22-alpine
    environment:
      - VIRTUAL_HOST=myapp.spark.loc # the same domain
      - VIRTUAL_PATH=/api # mounted under it
      - VIRTUAL_PORT=3000
```

`https://myapp.spark.loc/` reaches the frontend and `https://myapp.spark.loc/api/...`
reaches the API.

This mirrors how an ingress routes a path prefix to a different service in a
deployed environment, so the same relative call in application code works in both
places.

What to tell the user before they adopt it:

- **Matching is by path segment.** `/api` matches `/api` and everything under it,
  and never `/api-docs`.
- **Nothing is stripped.** The API receives `/api/users`, not `/users`, so it has
  to serve the prefix itself. Most frameworks have a setting for this, such as a
  global route prefix. `VIRTUAL_DEST`, nginx-proxy's rewriting companion, is not
  supported.
- **A certificate covers the domain**, not a path, so the mounted container needs
  none of its own. Never run the certificate command with a path in the argument;
  it is refused.
- **`VIRTUAL_PORT` belongs to each container**, independently of the others
  sharing the domain.
- **`VIRTUAL_PATH` applies to every domain the container names.** With
  `VIRTUAL_HOST=a.spark.loc,b.spark.loc` it is mounted at that path on both.
- **Stopping the mounted container does not produce a 404.** Its routes go with
  it, so its paths fall through to whichever container serves the domain. For a
  dev server that usually means a page and a `200`, which is confusing to debug.
- **Changing the value needs the container recreated**, since environment
  variables cannot change in place. `docker compose up -d` does this.

## Path 2: native `traefik.*` labels (more control)

Use labels when you need routing features `VIRTUAL_HOST` does not express
(middlewares, path rules, multiple services, custom entrypoints). Labels are
read directly by Traefik's Docker provider. The equivalent of the quick path
above, written as labels:

```yaml
services:
  myapp:
    image: nginx:alpine
    labels:
      # HTTP router
      - "traefik.http.routers.myapp.rule=Host(`myapp.spark.loc`)"
      - "traefik.http.routers.myapp.entrypoints=http"
      - "traefik.http.routers.myapp.service=myapp"
      # HTTPS router
      - "traefik.http.routers.myapp-tls.rule=Host(`myapp.spark.loc`)"
      - "traefik.http.routers.myapp-tls.entrypoints=https"
      - "traefik.http.routers.myapp-tls.tls=true"
      - "traefik.http.routers.myapp-tls.service=myapp"
      # backend port
      - "traefik.http.services.myapp.loadbalancer.server.port=80"
```

The entrypoint names are `http` (port 80) and `https` (port 443). Unlike
`VIRTUAL_HOST`, labels do not auto-create the HTTPS router — declare both routers
as shown if you want HTTPS.

**Do not mix the two on the same container.** If a container already has any
`traefik.*` label, the proxy's compatibility layer skips its `VIRTUAL_HOST`
entirely and lets Traefik's native label handling win.

## What happens after you edit

1. Recreate the container so the proxy sees the change: `docker compose up -d`.
2. The proxy joins the container's Docker network automatically (the
   `join-networks` sidecar) and creates the routes.
3. Visit `http://<host>` / `https://<host>`. If it does not work, see
   `troubleshooting.md`.

The container does **not** need to publish ports to the host once it is behind
the proxy; the proxy reaches it over the shared Docker network.
