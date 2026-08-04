# SparkFabrik container patterns

Use these patterns as company precedents, not as templates to copy without
checking their current code, platform contract, and tests.

## Package ownership

SparkFabrik packages can generate and synchronize project Dockerfiles. Read the
closest `AGENTS.md`, generated headers, package manifest, and build scripts
before editing.

When a project Dockerfile is package-owned:

1. Find its `.twig` template or package source.
2. Change the source repository when the improvement belongs to every consumer.
3. Use the documented project override only when behavior is project-specific.
4. Regenerate through `fs-cli` only with the required skill and user approval.
5. Never present a direct edit to a generated consumer file as persistent.

## Native multi-platform publication

The maintained PHP image repositories provide a useful publication model:

- [docker-php-base-image](https://github.com/sparkfabrik/docker-php-base-image)
- [docker-php-drupal-nginx](https://github.com/sparkfabrik/docker-php-drupal-nginx)

Their workflows build amd64 and arm64 variants on native GitHub runners, push
each result by digest, upload digest metadata, and assemble the final manifest in
a separate job. They also keep root and rootless flavors distinct.

Reuse these properties:

- **Native runners.** Prefer native amd64 and arm64 runners for builds that
  execute target binaries or compile expensive native code.
- **Digest handoff.** Treat a platform digest as the immutable output of its
  matrix job and fail manifest assembly when any required digest is missing.
- **Scoped caches.** Include architecture, image target, and flavor in cache
  scope to prevent incompatible layers from crossing jobs.
- **Separate flavors.** Test root and rootless variants independently when both
  are published.

Do not inherit one current gap: publishing an arm64 image after only amd64
runtime tests. Every published platform needs its own smoke test.

## Dependency and runtime stages

Package-managed application images can use these boundaries:

- **Composer stage.** Install locked PHP dependencies through a BuildKit secret
  mount for `COMPOSER_AUTH` and a cache mount for downloaded packages.
- **Build stage.** Compile application assets and prepare only files needed by
  the distribution image.
- **Runtime stage.** Install runtime packages, copy built output, remove
  development-only configuration, and switch to the expected non-root user.
- **Static server stage.** Copy only public static assets into nginx when PHP
  executes in a separate service.

Keep these boundaries when they match the project. Do not create stages that add
indirection without reducing runtime content or separating a trust boundary.

## Base pinning and build-time tests

Pin versioned release bases by multi-platform manifest digest and leave version
plus digest updates to Renovate. BuildKit bind mounts can provide deterministic
test input without retaining that input in an image layer.

This pattern works when the test is deterministic and does not depend on an
external service. Keep deployment-level integration tests outside the Dockerfile.

## Patterns to reject during review

- **Hardcoded target architecture.** `GOARCH=amd64`, `binaryArch=amd64`, or a
  fixed `x86_64` download in an image published for arm64.
- **Host-based selection.** `uname -m` used to select an artifact for
  `$TARGETPLATFORM`.
- **Unchecked downloads.** Architecture-specific binaries or installer scripts
  without target-specific checksums or signatures.
- **Tag-only release bases.** Mutable tags without a reviewed update policy.
- **Untested libc assumptions.** Alpine selected for size while installed tools
  expect glibc, or a musl binary accepted because extraction succeeded.
- **Build-only multi-platform claims.** A manifest lists several architectures,
  but CI executes behavior on only one.
- **Permission shortcuts.** `chmod 777`, writable application code, or rootless
  labels without an actual non-root runtime test.

## Task runners and safety

Use repository-provided `just`, `make`, and package scripts. Follow project
command safety rules before builds, package regeneration, publication, or
registry changes. Building locally is not permission to publish an image.
