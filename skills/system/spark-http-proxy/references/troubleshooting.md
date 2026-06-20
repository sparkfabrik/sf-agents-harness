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

Most common. Work down this list:

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
4. **Both label and `VIRTUAL_HOST` present.** Any `traefik.*` label makes the
   compatibility layer skip `VIRTUAL_HOST`. Use one mechanism, not both.

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
