# Troubleshooting

Routing depends on three independent things being true at once: the container is
opted in, the proxy has joined the container's network, and DNS resolves the
domain. Diagnose by symptom rather than guessing.

## Start with the facts

```bash
spark-http-proxy status                       # is the stack up?
docker ps                                      # is the target container running?
spark-http-proxy logs                          # proxy-side errors
dig @127.0.0.1 -p 19322 <host>                 # does the name resolve?
curl -v -H "Host: <host>" http://localhost     # bypass DNS, test routing directly
```

The last command is the key disambiguator: it tests Traefik routing while
bypassing DNS by sending the `Host` header manually. Combine with the `dig`
result:

| `dig` resolves? | `curl -H Host` works? | Conclusion                                         |
| --------------- | --------------------- | -------------------------------------------------- |
| no              | yes                   | DNS problem — see "Does not resolve"               |
| yes             | no                    | routing problem — see "Resolves but not reachable" |
| no              | no                    | both; fix routing first, then DNS                  |
| yes             | yes                   | working; suspect a browser/cert cache              |

## Resolves but not reachable (404 / connection refused)

Most common. **This is not a certificate problem** — a missing or mismatched
certificate produces a TLS trust _warning_ on a page that still loads, never a
404 or a refused connection. Do not chase the cert-nesting rule here; that lives
under "Certificate untrusted or mismatched" below. Work down this list instead:

1. **Container not opted in.** It needs `VIRTUAL_HOST` or a `traefik.*` label;
   the proxy ignores everything else (`exposedByDefault: false`). Confirm the
   env var or label is actually on the running container:
   `docker inspect <container> --format '{{.Config.Env}} {{.Config.Labels}}'`.
2. **Proxy has not joined the network.** The `join-networks` sidecar bridges the
   `http-proxy` container onto any network holding a manageable container. Check
   `spark-http-proxy logs join_networks`. Recreating the target container
   (`docker compose up -d`) re-triggers the join. A route can exist while traffic
   still cannot reach the backend if this step has not happened.
3. **Wrong backend port.** If the app listens on a port the proxy did not guess,
   set `VIRTUAL_PORT` (or the `loadbalancer.server.port` label) to the real
   in-container port. The proxy defaults to the lowest exposed TCP port, then 80.
4. **Both label and `VIRTUAL_HOST` present.** Any `traefik.` label makes the
   compatibility layer skip the container entirely, `VIRTUAL_HOST` and
   `VIRTUAL_PATH` included. A middleware label alone is enough to trigger it, so
   this bites people who add CORS or headers to an otherwise working service. Use
   one mechanism, not both; the proxy warns when it happens, so check
   `spark-http-proxy logs dinghy_layer`.

## A path reaches the wrong container

Symptoms specific to `VIRTUAL_PATH`. Note that the first two do **not** produce a
404, which is why they are confusing.

1. **The mounted container is not running.** Its routes go with it, so its paths
   fall through to whatever serves the domain. A dev server answers unknown paths
   with its own page and a `200`, so every API call silently returns HTML. Check
   the container is up before suspecting the routing.
2. **The path is not what you think.** Matching is by segment: `/api` matches
   `/api` and everything under it, never `/api-docs`. If a request you expected to
   be captured is not, check whether it is a sibling rather than a child.
3. **The API 404s on its own routes.** Nothing is stripped, so the container
   receives `/api/users`, not `/users`. The application has to serve the prefix
   itself, usually through a global route-prefix setting.
4. **`VIRTUAL_PATH` with no `VIRTUAL_HOST`.** A path needs a domain to sit on, and
   without `VIRTUAL_HOST` the container is not exposed at all. The proxy warns;
   see `spark-http-proxy logs dinghy_layer`.
5. **Two containers claim the same path.** Which one answers is not defined. The
   proxy warns and names both.
6. **The value changed but nothing did.** Environment variables cannot change in
   place, so the container has to be recreated: `docker compose up -d`.

Confirm what the proxy actually generated when in doubt:

```bash
spark-http-proxy logs dinghy_layer   # warnings about ignored or conflicting values
```

## Does not resolve

1. Confirm the proxy DNS answers directly:
   `dig @127.0.0.1 -p 19322 <host>` should return the target IP.
2. If that works but the system does not resolve the name, the OS is not wired to
   the proxy DNS. Run `spark-http-proxy configure-dns` (details and the manual
   per-OS setup are in `dns.md`).
3. If the host's TLD is not among `HTTP_PROXY_DNS_TLDS` (default `loc`), the
   server refuses it. Restart with the TLD included, e.g.
   `HTTP_PROXY_DNS_TLDS=loc,dev spark-http-proxy start`.

## Certificate untrusted or mismatched

The symptom here is a **browser TLS trust warning** ("not secure", `NET::ERR_CERT_*`)
on a page that otherwise loads — not a 404 and not a refused connection. If the
page does not load at all, it is a routing or DNS problem above, not this.

1. Trusted cert never generated → run `spark-http-proxy generate-mkcert "*.spark.loc"`.
2. Warning on a nested domain (`drupal.client.spark.loc`) while `*.spark.loc`
   exists → wildcards cover one level only; generate the wildcard one level above
   the host, here `*.client.spark.loc`. See `certificates.md`.
3. After generating, Traefik must reload — the CLI restarts it automatically;
   for a manual cert drop, `docker compose restart`.

## Last resorts

- `spark-http-proxy self-test` runs a built-in diagnosis.
- `spark-http-proxy restart` clears transient state.
- The Traefik dashboard (`spark-http-proxy dashboard`) shows whether the router
  and service for the host actually exist.
