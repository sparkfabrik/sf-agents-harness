# DNS and domain resolution

The proxy ships a built-in DNS server (UDP+TCP, port 19322) that resolves the
configured TLDs to localhost, so `*.loc` names work with no `/etc/hosts` edits.
Two things are involved: which domains the server answers for, and how the OS is
told to ask it.

## Which domains are served

Controlled by `HTTP_PROXY_DNS_TLDS` (default `loc`). It accepts TLDs or specific
domains, comma-separated:

| Value               | Resolves                                                 |
| ------------------- | -------------------------------------------------------- |
| `loc` (default)     | any `*.loc`, which includes the `*.spark.loc` convention |
| `loc,dev`           | any `*.loc` and `*.dev`                                  |
| `spark.loc,api.dev` | only those specific domains (and their subdomains)       |

The default `loc` already covers the SparkFabrik `*.spark.loc` convention, since
`spark.loc` is a subdomain of `loc`. You only need to change `HTTP_PROXY_DNS_TLDS`
to serve a different TLD (such as `dev`).

Set it when starting the proxy:

```bash
HTTP_PROXY_DNS_TLDS=loc,dev spark-http-proxy start
```

Other env vars: `HTTP_PROXY_DNS_TARGET_IP` (default `127.0.0.1`),
`HTTP_PROXY_DNS_PORT` (default `19322`), and `HTTP_PROXY_DNS_FORWARD_ENABLED` /
`HTTP_PROXY_DNS_UPSTREAM_SERVERS` to forward non-matching queries upstream
instead of refusing them.

## Wire the OS to use it

The easy path is `spark-http-proxy configure-dns`, which sets up the right
mechanism per OS (and avoids `/etc/hosts` editing). What it does under the hood:

### macOS (`/etc/resolver`)

```bash
sudo mkdir -p /etc/resolver
echo "nameserver 127.0.0.1" | sudo tee /etc/resolver/loc
echo "port 19322"           | sudo tee -a /etc/resolver/loc
```

One file per TLD; the filename is the TLD.

### Linux (systemd-resolved)

```bash
sudo mkdir -p /etc/systemd/resolved.conf.d
sudo tee /etc/systemd/resolved.conf.d/http-proxy.conf > /dev/null <<EOF
[Resolve]
DNS=127.0.0.1:19322
Domains=~loc
EOF
sudo systemctl restart systemd-resolved
```

The DNS server publishes port 19322 on all interfaces, so `127.0.0.1` reaches
it. systemd-resolved may still route
some unrelated queries to the proxy, producing harmless `REFUSED` log lines;
that is expected and does not affect resolution.

## Test resolution without touching system DNS

```bash
dig @127.0.0.1 -p 19322 myapp.spark.loc        # UDP
dig @127.0.0.1 -p 19322 +tcp myapp.spark.loc   # TCP (Lima and other VMs)
curl --resolve myapp.spark.loc:80:127.0.0.1 http://myapp.spark.loc   # bypass system DNS
```

A correct answer is an A record pointing at the target IP (`127.0.0.1` by
default). If `dig` works but the browser does not resolve the name, the OS is not
wired to the proxy DNS yet — run `configure-dns`.
