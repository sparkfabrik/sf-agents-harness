# Supply chain and runtime

Use this reference when choosing base images, installing remote artifacts,
handling credentials, defining runtime users, or publishing images.

## Base images and updates

- **Choose trusted sources.** Prefer maintained official or verified images with
  a clear update and end-of-life policy.
- **Choose compatibility first.** Minimal images reduce surface area, but the
  runtime must provide the libc, certificates, timezone data, shells, and shared
  libraries the application needs.
- **Pin release inputs.** Use a meaningful version tag plus manifest digest for
  release images. Configure Renovate or equivalent automation to propose digest
  updates for review.
- **Rebuild regularly.** Digest pinning provides repeatability, not permanent
  security. Rebuild against reviewed base updates and rescan the result.
- **Avoid blind upgrades.** Prefer an updated base image over a broad
  `apt-get upgrade` or `apk upgrade`. Use a targeted package upgrade only when a
  documented issue requires it.

## Packages and remote artifacts

Keep package installation and cleanup in one layer:

```dockerfile
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
      ca-certificates \
      curl \
    && rm -rf /var/lib/apt/lists/*
```

Use `apk add --no-cache` on Alpine. Sort multiline package names so reviews can
detect additions and duplicates.

When a `RUN` instruction uses a pipeline, make failures from every command
observable. Use a shell with `pipefail`, or avoid the pipeline when the selected
shell does not support it.

For artifacts outside a package manager:

1. Pin an exact version or immutable revision.
2. Select the artifact from target platform values.
3. Verify a target-specific checksum or trusted signature before extraction.
4. Extract in a build stage when the archive is not needed at runtime.
5. Delete temporary files in the same layer.
6. Execute the installed tool during the target-platform smoke test.

Reject unchecked installer scripts and pipelines such as `curl | sh`. Current
Docker versions also support `ADD --checksum` for immutable remote downloads.
Use it only when its remote-fetch semantics are intentional.

## Third-party package repositories

Add third-party repositories only when the distribution packages cannot meet
the image contract. Use the vendor's HTTPS repository for the matching
distribution release and scope its trust to that repository.

For Debian and Ubuntu images:

- **Pin the trust anchor.** Install the vendor key in `/etc/apt/keyrings/` and
  verify its fingerprint against an independently published value before use.
- **Scope the key.** Reference the key with `signed-by=` in the repository
  entry. Do not add it to the global APT trust store.
- **Reject trust bypasses.** Do not use deprecated `apt-key add` or repository
  entries with `[trusted=yes]`.

For Alpine images, install only a verified vendor signing key in
`/etc/apk/keys/` and use a repository that matches the Alpine release. Do not
use `apk --allow-untrusted`.

## Build secrets

Do not put secrets in `ARG`, `ENV`, URLs, copied config files, or shell history.
Build arguments and environment variables can persist in image metadata or
layers.

Use BuildKit mounts for the instruction that needs the credential:

```dockerfile
RUN --mount=type=secret,id=composer_auth,env=COMPOSER_AUTH \
    composer install --no-interaction --no-dev
```

The `env` option of secret mounts requires Dockerfile frontend 1.10 or later.
Declare `# syntax=docker/dockerfile:1` on the first line of the Dockerfile to
get it.

Use `type=ssh` for private Git access. Confirm the build context and copied
artifacts do not retain the credential after the mount disappears.

## Runtime identity and permissions

Run as non-root unless the image has a documented reason not to. A fixed UID
such as `1001` is suitable only when it matches the deployment contract.
Kubernetes platforms may instead inject an arbitrary UID.

For arbitrary UID compatibility:

- **Keep executables immutable.** Application code and executables should be
  root-owned and not writable by the runtime user.
- **Declare writable paths.** Make only required state directories writable,
  often through the root group, and use `/tmp` for transient data.
- **Avoid world-writable fixes.** Do not use `chmod 777` to hide ownership
  problems.
- **Avoid runtime privilege tools.** Do not install or depend on `sudo` inside
  the image.
- **Test the policy.** Run the image with the expected fixed or arbitrary UID
  and, where applicable, a read-only root filesystem.

## Entrypoints and process behavior

Use JSON exec form so the application receives signals directly:

```dockerfile
ENTRYPOINT ["/usr/local/bin/docker-entrypoint"]
CMD ["serve"]
```

An entrypoint script should fail on command errors according to its shell and
replace itself with the final process:

```sh
#!/bin/sh
set -eu

# Runtime setup belongs here only when it cannot happen during the build.

exec "$@"
```

Add an init process only when the application cannot reap child processes or
handle PID 1 correctly. Keep containers stateless and inject runtime config and
secrets through the deployment system.

Give each service image one primary responsibility. Multiple cooperating
processes are acceptable when the image intentionally supervises them and tests
their combined lifecycle. Do not split or combine processes only to satisfy a
layer-count rule.

Docker or Swarm services may benefit from `HEALTHCHECK`. Kubernetes ignores the
Dockerfile health check, so define Kubernetes readiness, liveness, and startup
probes in deployment configuration instead of assuming the image check applies.

## Publication and runtime controls

Add OCI labels when values are available during CI:

- `org.opencontainers.image.source`
- `org.opencontainers.image.revision`
- `org.opencontainers.image.version`

Generate SBOM and provenance attestations during publication. Scan the final
image in CI and continue scanning published images as vulnerability data changes.
Use signatures and admission verification when the registry and deployment
platform support them.

Runtime controls often live outside the Dockerfile. Review the deployment for a
read-only root filesystem, `no-new-privileges`, dropped Linux capabilities,
seccomp or AppArmor profiles, resource limits, and Docker socket mounts. Expose
only ports required by the image contract.

## References

- [Docker build best practices](https://docs.docker.com/build/building/best-practices/)
- [Docker build secrets](https://docs.docker.com/build/building/secrets/)
- [Docker build cache optimization](https://docs.docker.com/build/cache/optimize/)
- [Docker build checks](https://docs.docker.com/build/checks/)
- [Sysdig Dockerfile best practices](https://www.sysdig.com/learn-cloud-native/dockerfile-best-practices)
