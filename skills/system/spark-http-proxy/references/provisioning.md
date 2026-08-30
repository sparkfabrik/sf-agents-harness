# Install on SparkFabrik machines (provisioners)

SparkFabrik workstations are provisioned automatically, which is why
`spark-http-proxy` is normally already present. Two provisioners exist, one per
platform, and they differ in important ways — especially the DNS target IP.

| Aspect           | macOS — [sparkdock](https://github.com/sparkfabrik/sparkdock)                        | Linux — archlinux-ansible-provisioner (Arch _and_ Debian/Ubuntu)                         |
| ---------------- | ------------------------------------------------------------------------------------ | ---------------------------------------------------------------------------------------- |
| Installs CLI     | git clone to `/opt/sparkdock/http-proxy` + symlink `/usr/local/bin/spark-http-proxy` | `get_url` of `bin/spark-http-proxy` → `/usr/local/bin/spark-http-proxy` (0755); no clone |
| Compose file     | from the clone                                                                       | `bin/compose.yml` → `~/.local/spark/http-proxy/compose.yml`                              |
| Starts the proxy | **yes** (`spark-http-proxy start`)                                                   | **no** — run `spark-http-proxy start` yourself                                           |
| mkcert local CA  | package only; CA trust via `sjust system-install-mkcert` or `generate-mkcert`        | `mkcert -install` **is** run during provisioning                                         |
| `*.loc` DNS      | `/etc/resolver/loc` → `127.0.0.1` port `19322`                                       | systemd-resolved drop-in → `127.0.0.1:19322` (Arch and Debian/Ubuntu)                    |
| CLI guaranteed   | yes (fail-fast verification)                                                         | no explicit verification step                                                            |

## How each platform is pointed at the DNS server

Both reach it on loopback, since the DNS server publishes its port on all
interfaces. What differs is the mechanism, not the target.

- **macOS** uses an `/etc/resolver/loc` file naming `127.0.0.1` port `19322`.
- **Linux** (Arch and Debian/Ubuntu) uses a systemd-resolved drop-in at
  `/etc/systemd/resolved.conf.d/http-proxy.conf` with `DNS=127.0.0.1:19322` and
  `Domains=` listing the served TLDs, `~loc` by default. See `dns.md`.

## Consequences worth knowing

- **macOS checkout is managed.** `/opt/sparkdock/http-proxy` is force-updated to
  `origin/main`; never assume a custom checkout there or tell a user to edit it.
- **Linux does not auto-start the proxy.** Provisioning installs the CLI, compose,
  the mkcert CA, and the `*.loc` DNS drop-in, but does not run
  `spark-http-proxy start` — the user does that. If `*.loc` still does not resolve
  on a Linux box, run `configure-dns`.
- **mkcert CA trust differs.** Linux provisioning trusts the CA (`mkcert -install`)
  automatically; macOS does not until `generate-mkcert` or `sjust
system-install-mkcert` runs. A lingering TLS warning on macOS often means that
  step has not run.

## Updating

- **macOS:** `sjust http-proxy-install-update` (updates the managed checkout and
  reinstalls/restarts). Don't `git pull` it by hand.
- **Linux:** re-run the provisioner for the proxy tag, e.g.
  `ajust provision-tags spark-http-proxy`.

Neither provisioner ships start/stop/restart/status recipes — lifecycle always
goes through the `spark-http-proxy` CLI directly.
