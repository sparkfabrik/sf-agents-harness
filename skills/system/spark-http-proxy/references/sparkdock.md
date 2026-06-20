# Install on SparkFabrik machines (sparkdock)

[sparkdock](https://github.com/sparkfabrik/sparkdock) is SparkFabrik's **macOS**
workstation provisioner. It is why `spark-http-proxy` is "always there" on a
company Mac. There is no Linux provisioning path, so none of this is guaranteed
on Linux — treat a Linux box as a manual install.

## What sparkdock sets up (macOS)

On every provisioning run, the Ansible playbook:

- **Installs the CLI** — clones `sparkfabrik/http-proxy` (branch `main`) to
  `/opt/sparkdock/http-proxy` and symlinks `bin/spark-http-proxy` to
  `/usr/local/bin/spark-http-proxy`. Compatibility aliases `run-http-proxy` and
  `run-dinghy-proxy` point at the same CLI. Provisioning aborts if the symlink is
  missing afterward, so presence is guaranteed.
- **Configures DNS** — writes `/etc/resolver/loc` with `nameserver 127.0.0.1` and
  `port 19322`, then refreshes `mDNSResponder`. This is the macOS `/etc/resolver`
  mechanism (not dnsmasq/systemd-resolved), pointing `*.loc` at the proxy's DNS
  server. So `*.spark.loc` resolves out of the box.
- **Starts the proxy** — runs `spark-http-proxy start` at the end (when Docker is
  up).
- **Installs mkcert + nss** as Homebrew packages — but **not** the local CA trust.

## Two consequences worth knowing

- **The checkout is managed.** The repo at `/opt/sparkdock/http-proxy` is
  force-updated to `origin/main` by sparkdock (local changes are discarded).
  Never assume a user has a custom checkout there, and don't tell them to edit it.
- **The mkcert CA may not be trusted yet.** Provisioning installs the mkcert
  _package_ but does not run `mkcert -install`. The CA gets set up either by
  running `spark-http-proxy generate-mkcert <domain>` (which runs `mkcert -install`
  for you) or by the explicit recipe below. If a user sees a TLS trust warning
  even after generating a cert, the CA trust step is the likely gap.

## Relevant sjust recipes

SparkFabrik wraps common tasks in `sjust` (macOS) recipes:

| Recipe                            | What it does                                                                                                                               |
| --------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------ |
| `sjust http-proxy-install-update` | Update `/opt/sparkdock/http-proxy` to latest `origin/main` and reinstall + restart the proxy. Use this to update, not a manual `git pull`. |
| `sjust system-install-mkcert`     | `brew install mkcert nss` and run `mkcert -install` (sets up the local CA).                                                                |
| `sjust system-clear-dns-cache`    | Flush the macOS DNS cache (`dscacheutil -flushcache` + reset `mDNSResponder`). Useful after DNS changes.                                   |

There are no start/stop/restart/status recipes in sjust — lifecycle goes through
the `spark-http-proxy` CLI directly.
