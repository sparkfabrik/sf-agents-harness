# Dependencies and uninstall

## Checking what is installed

- **`spark-http-proxy` CLI** — `command -v spark-http-proxy`. Installed on every
  SparkFabrik machine; install steps are in `SKILL.md` if it is genuinely missing.
- **Docker** — required; the proxy is a Docker stack. `spark-http-proxy self-test`
  checks the daemon and reports problems.
- **mkcert** — only needed for trusted HTTPS. `command -v mkcert`. You usually do
  not check it yourself: `spark-http-proxy generate-mkcert` installs it
  automatically (Homebrew on macOS, pacman on Arch) and runs `mkcert -install` to
  add the local CA. On other Linux distros it cannot auto-install and prints
  manual steps, so install mkcert + nss first there. `mkcert -CAROOT` shows where
  the local CA lives.

## Where things live

| What                     | Location                                                                            |
| ------------------------ | ----------------------------------------------------------------------------------- |
| Config + cert dir        | `~/.local/spark/http-proxy` (`certs/` inside it)                                    |
| CLI entrypoint           | symlink `/usr/local/bin/spark-http-proxy`                                           |
| Source — sparkdock (Mac) | `/opt/sparkdock/http-proxy` (managed; force-updated to `origin/main`)               |
| Source — manual install  | `~/.local/spark/http-proxy/src`                                                     |
| mkcert local CA          | `$(mkcert -CAROOT)`                                                                 |
| Docker resources         | containers, the `traefik_dynamic`/metrics volumes, the `http-proxy_default` network |

The CLI source depends on how it was installed (see `provisioning.md`): a
sparkdock Mac uses `/opt/sparkdock/http-proxy`; the Linux provisioner drops just
the `bin/spark-http-proxy` script at `/usr/local/bin` (no source tree) plus a
compose file at `~/.local/spark/http-proxy/compose.yml`; a manual `install.sh`
uses `~/.local/spark/http-proxy/src`. A manual uninstall on a provisioned machine
is undone by the next provisioning run unless the provisioner is also adjusted.

## Uninstalling

There is no `uninstall` command; remove the pieces you want gone. Confirm
destructive steps with the user first — these delete data and trust state.

1. **Tear down the Docker stack** (containers, volumes, images):

   ```bash
   spark-http-proxy destroy   # prompts for confirmation
   ```

   Use `spark-http-proxy clean` for the lighter version (stop + remove volumes,
   keep images).

2. **Remove certificates** — delete the cert files, and remove the local CA only
   if nothing else relies on mkcert:

   ```bash
   rm -f ~/.local/spark/http-proxy/certs/*
   mkcert -uninstall   # removes the mkcert local CA from the system trust store
   ```

3. **Undo system DNS** — `configure-dns` wrote resolver config; remove it:
   - macOS: `sudo rm /etc/resolver/loc` (one file per configured TLD)
   - Linux: `sudo rm /etc/systemd/resolved.conf.d/http-proxy.conf && sudo systemctl restart systemd-resolved`

4. **Remove the CLI and config**:

   ```bash
   sudo rm -f /usr/local/bin/spark-http-proxy
   rm -rf ~/.local/spark/http-proxy
   ```

Skip any step the user wants to keep (for example, leave the mkcert CA in place
if other local TLS tooling depends on it).
