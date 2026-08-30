# Tailnet peer routing

A hostname served by a container on one machine can be reached, under the same
name, from the other machines of the same Tailscale account. A developer with a
laptop and a desktop keeps `app.spark.loc` meaning one thing everywhere instead
of one name per machine.

It is off by default and has to be started explicitly on each machine.

What does not change: DNS still answers `127.0.0.1` for every name, hostnames
stay unqualified, and TLS still terminates on the machine the browser is on, so
no certificate authority is shared between machines. **A local container always
wins**: only a hostname no local container claims is eligible to be forwarded.

## Turning it on

```bash
spark-http-proxy start-with-tailscale   # start the proxy with peer routing
spark-http-proxy stop-tailscale         # stop peer routing, leave the proxy up
```

They mirror `start-with-metrics` and `stop-metrics`. Which optional stacks are
on is recorded, so peer routing survives `restart` and `upgrade` without being
asked for again. `stop-tailscale` withdraws every forwarded hostname at once,
without restarting the proxy.

**Both machines need it running**, and both need a version that publishes the
self-declaration described below. One machine alone forwards nothing.

## Seeing what happened

```bash
spark-http-proxy tailscale-peers          # the last discovery cycle
spark-http-proxy tailscale-peers --json   # the same, machine-readable
```

Every machine on the tailnet appears with an outcome, so a machine that
contributes nothing says why rather than being absent:

| Status           | Meaning                                                                   |
| ---------------- | ------------------------------------------------------------------------- |
| `ok`             | answered, and the hostnames it contributes are listed                     |
| `unreachable`    | did not answer; the detail says when it will be tried again               |
| `not this proxy` | answered, but it is not running this proxy, so nothing is taken from it   |
| `no proxy`       | nothing is listening where the proxy would be                             |
| `skipped`        | not probed: offline, belongs to another account, or the cycle ended early |

The failures are deliberately distinct: a machine that did not answer, one that
answered with something else, and one excluded on ownership are different
problems with different fixes.

## "It is not reachable from my other machine yet"

Work down this list.

1. **Is peer routing on, on both machines?** `tailscale-peers` on the machine
   that cannot reach the hostname. If it reports that peer routing is disabled,
   start it there with `start-with-tailscale`.
2. **Has a cycle run since the container started?** Discovery polls every 60
   seconds by default, so a container started a moment ago may simply not have
   been seen yet. Force a cycle rather than waiting:

   ```bash
   spark-http-proxy tailscale-refresh-peers
   ```

   It runs a cycle now, waits for it, and prints the resulting report. It exits
   non-zero if no cycle happened, so it is safe in a script.

3. **Is the hostname served locally too?** A local container always wins. If the
   name resolves to something local, that is the answer, not the peer.
4. **Is the other machine `ok` in the report?** If it is, and the hostname is
   not in its list, the container on that machine is not exposed through the
   proxy there. That is an ordinary `VIRTUAL_HOST` problem on that machine, and
   `references/expose-container.md` applies.
5. **Are both machines online in Tailscale?** A machine that is offline is
   `skipped`, and no amount of proxy configuration changes that.

## "HTTPS to the peer hostname is not trusted"

TLS terminates on the machine the browser is talking to, so the peer's
certificate is never presented. The machine doing the reaching needs a
certificate for a hostname it does not serve. Without one, Traefik serves its
default and the browser refuses:

```
SSL: no alternative certificate subject name matches target hostname 'macos.test.spark.loc'
subject: CN=TRAEFIK DEFAULT CERT
```

Fix it on the machine doing the reaching, not the one serving:

```bash
spark-http-proxy generate-mkcert 'macos.test.spark.loc'
```

**A wildcard covers exactly one label.** This is the part that catches people, so
check the label count before assuming an existing wildcard applies. Measured
against a machine holding `*.spark.loc`:

| Hostname               | Certificate served |
| ---------------------- | ------------------ |
| `test123.spark.loc`    | `*.spark.loc`      |
| `a.b.spark.loc`        | Traefik's default  |
| `macos.test.spark.loc` | Traefik's default  |

A nested name needs its own certificate, or a wildcard at its own level
(`*.test.spark.loc`), which then covers every name directly under it.

Nothing generates these automatically. `tailscale-peers` names the command when
machines are forwarding, and the user runs it.

## "Why does this peer say `not this proxy`"

Every proxy publishes a declaration of itself, and a machine is adopted only
when that declaration is present. `not this proxy` means something answered on
the port the proxy uses, but did not identify itself as this proxy.

The usual cause is a **version older than the one that publishes the
declaration**. Both machines need that version or newer before anything is
forwarded, so upgrading only one is not enough:

```bash
spark-http-proxy self-update && spark-http-proxy upgrade
```

The other cause is something unrelated listening on that port, in which case the
report is telling the truth and nothing is wrong with the proxy.

## The extra step on macOS

Peer discovery needs to know which machines exist. On Linux it reads that from
the Tailscale daemon's socket, mounted into the container. **On macOS the daemon
exposes no socket a container can reach**, so the host writes a status document
that the container reads instead.

This is handled automatically:

- `start-with-tailscale` writes the document and installs a launchd agent that
  refreshes it every 300 seconds.
- The source is **detected, not configured**: the CLI reports which one it is
  using, and `HTTP_PROXY_TAILSCALE_SOURCE` overrides it only if asked.
- `tailscale-refresh-peers` rewrites the document before forcing a cycle, so a
  machine that came online since the last refresh is found rather than missed.

What this means in practice: the machine list on macOS can be up to five minutes
old, while what each machine serves is always read live. So a container that
appeared on a machine already known shows up within one cycle, but a machine
that joined the tailnet minutes ago may need `tailscale-refresh-peers`.

If the document cannot be written, the Tailscale command-line client is missing.
Install Tailscale and run `start-with-tailscale` again.

## Ownership is not configurable

Only machines belonging to the same Tailscale account are considered. A machine
shared into the tailnet from another account is `skipped`, and no setting widens
this. When a user asks to route to a colleague's machine, the answer is that
peer routing does not do it, not that a flag exists.

## Settings

Defaults are right for a developer machine; change them only with a reason.

| Variable                                | Default  | Meaning                                                             |
| --------------------------------------- | -------- | ------------------------------------------------------------------- |
| `HTTP_PROXY_TAILSCALE_REFRESH_INTERVAL` | `60s`    | How often peers are re-read                                         |
| `HTTP_PROXY_TAILSCALE_STATUS_MAX_AGE`   | `10m`    | How old the macOS status document may be before it counts as absent |
| `HTTP_PROXY_TAILSCALE_SOURCE`           | detected | `socket` or `file`, overriding the detected source                  |
