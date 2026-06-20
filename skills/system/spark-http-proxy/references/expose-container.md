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
