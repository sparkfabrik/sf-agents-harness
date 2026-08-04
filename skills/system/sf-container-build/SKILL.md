---
name: sf-container-build
description: 'Design, modify, review, and debug Dockerfiles and container build pipelines using SparkFabrik platform, security, supply-chain, caching, and runtime conventions. Use this skill whenever work touches a Dockerfile, generated image template, container entrypoint, BuildKit or buildx configuration, image publishing workflow, or native artifact installed in an image, even when multi-platform support is not explicitly mentioned. Also trigger for requests such as "build this image" and for architecture, libc, arm64, amd64, Alpine, musl, rootless, image size, SBOM, provenance, or container supply-chain problems.'
---

# SparkFabrik container builds

Treat supported platforms as a tested contract. An image supports a target only
when it builds, starts, and performs its minimum function on that target OS,
architecture, variant, and libc or ABI.

Use this skill for implementation, diagnosis, and review. Respect the user's
requested mode: inspect and report without editing when asked for a review or
diagnosis only.

## Start with project discovery

Read the closest project instructions before proposing a change. Then inspect
the Dockerfile, its build context, publishing workflow, deployment manifests,
and task runner together.

- **Find the source of truth.** Detect generated headers, `.twig` templates,
  package ownership, and generator scripts. Change the source or generator,
  never a file that the next package install will overwrite.
- **Classify the image.** Identify whether it is a service, CLI, build tool,
  development environment, test image, or artifact carrier. Different image
  purposes need different runtime and publishing rules.
- **Derive the platform contract.** Read CI matrices, buildx commands, base
  manifests, deployment nodes, and registry tags. Do not infer targets from the
  machine running the agent.
- **Identify runtime constraints.** Record the expected user, writable paths,
  read-only filesystem requirements, ports, signals, health mechanism, and
  whether Kubernetes must support an arbitrary UID.
- **Preserve intentional scope.** Do not force multi-platform output onto an
  explicitly single-platform image. Make the single-platform constraint clear
  and prevent accidental publication for other targets.

## Define the platform contract

Record each target as a tuple that includes OS, architecture, optional variant,
and libc or ABI. `linux/arm64` alone is incomplete when an installed binary
distinguishes glibc from musl.

Use BuildKit target arguments for target decisions:

- `BUILDPLATFORM`
- `TARGETPLATFORM`
- `TARGETOS`
- `TARGETARCH`
- `TARGETVARIANT`

Never use `uname`, the build host architecture, or a hardcoded `amd64` value to
choose a target artifact. Map vendor-specific names such as `x86_64`, `aarch64`,
or `armv7` explicitly, and fail when a tuple is unsupported.

Read [multi-platform builds](references/multi-platform.md) before changing
architecture selection, cross-compilation, native binary downloads, buildx
matrices, per-platform caches, or manifest assembly.

## Choose the build strategy deliberately

Prefer the simplest strategy that meets the declared platform contract:

1. **Platform-neutral installation.** Prefer an ecosystem package manager or a
   platform-neutral artifact when it supports every target. Still execute the
   installed tool on each platform because transitive dependencies may be
   native.
2. **Cross-compilation.** Pin a builder to `$BUILDPLATFORM` only when its
   toolchain genuinely emits binaries for `$TARGETOS/$TARGETARCH`. Confirm CGO,
   native extensions, and linked libraries do not invalidate that assumption.
3. **Target-platform builds.** Run the builder on the target platform when the
   build executes target-native tools or cannot cross-compile safely.
4. **Emulation.** Use QEMU as a compatibility aid, not as proof of production
   behavior. Prefer native runners for compute-heavy builds and runtime tests.

## Structure stages and cache

Use stages to separate concerns when they reduce the final image or isolate
trust boundaries. Common stages are development, dependency, build, test, and
runtime.

- **Keep the runtime stage narrow.** Copy only runtime files and libraries. Do
  not carry compilers, package caches, credentials, or source into the final
  image without a runtime need.
- **Order for cache reuse.** Copy dependency manifests and lockfiles before
  volatile application source. Run locked installs before source-dependent
  build steps.
- **Use BuildKit mounts.** Use cache mounts for package caches and bind mounts
  for build-only inputs that should not become image layers. Scope shared CI
  caches by platform, stage, and flavor.
- **Keep context small.** Prefer an allowlist-oriented `.dockerignore` and
  explicit `COPY` instructions.
- **Use stable paths.** Set `WORKDIR` with an absolute path and keep filesystem
  ownership visible in the Dockerfile.
- **Optimize for clarity and correctness.** Do not collapse unrelated work into
  one large `RUN` instruction merely to reduce layer count. Group package index
  updates, installs, and cleanup when they must remain atomic.
- **Use `COPY` by default.** Use `ADD` only for intentional semantics, such as a
  remote immutable artifact protected with `--checksum`.

## Protect the supply chain and runtime

Read [supply chain and runtime](references/supply-chain-and-runtime.md) before
adding base images, remote downloads, secrets, package repositories, runtime
users, entrypoints, health checks, attestations, or scanners.

Apply these baseline rules:

- use maintained base images with versions and manifest digests for release
  images, backed by automated reviewed updates
- pin direct tool versions and use dependency lockfiles
- verify every downloaded artifact against a target-specific digest pinned in
  the repository, or verify its signature with a trusted public key pinned in
  the repository; do not fetch an unsigned checksum from the artifact's
  download location at build time
- use BuildKit secret or SSH mounts instead of `ARG`, `ENV`, or copied secrets
- run as non-root by default and keep executable content non-writable at runtime
- use exec-form `ENTRYPOINT` and `CMD`, with entrypoint scripts ending in
  `exec "$@"` or an equivalent final process
- publish OCI source, revision, and version labels when the pipeline knows them
- generate SBOM and provenance attestations, then scan the built image

Choose the base for compatibility, not size alone. Alpine is unsuitable when a
required native artifact supports only glibc. A slightly larger compatible
runtime is safer than an untested musl workaround.

## Validate the contract

Use project task runners such as `just` or `make` when they exist. Do not replace
project commands with ad hoc Docker commands.

Validation should cover, in order:

1. **Static checks.** Run `docker build --check .` and the configured Dockerfile
   linter. Treat actionable warnings as failures in CI.
2. **Per-platform builds.** Build every declared platform with isolated cache
   scopes. A successful manifest build proves only that layers were produced.
3. **Per-platform runtime tests.** Start each image and execute its minimum
   behavior. Test downloaded tools with `--version` or an equivalent command.
4. **Runtime policy tests.** Exercise rootless or arbitrary UID execution,
   writable paths, read-only root filesystems, signals, and health behavior when
   they belong to the image contract.
5. **Published manifest checks.** Inspect the registry manifest and fail when a
   required digest or platform is missing.
6. **Supply-chain checks.** Run vulnerability scanning and verify expected SBOM,
   provenance, and signatures.

Do not claim platform support when runtime testing was skipped. State which
targets were built, which were executed, and what remains unverified.

## Apply SparkFabrik conventions

Read [SparkFabrik patterns](references/sparkfabrik-patterns.md) when working in a
SparkFabrik repository. It documents package-owned templates, native runner
matrices, per-platform digest publication, root and rootless flavors, cache
scopes, and known patterns that should not be copied without their validation
gates.

## Report the result

Lead with the resulting platform contract and validation status. Include:

- **Targets.** Supported OS, architecture, variant, and libc or ABI tuples.
- **Strategy.** Platform-neutral install, cross-compilation, target-native build,
  or emulation, with the reason for the choice.
- **Ownership.** Source Dockerfile, template, package, or generator changed.
- **Verification.** Static checks, builds, runtime smoke tests, manifest checks,
  and supply-chain checks actually run.
- **Limits.** Unsupported or untested targets and the concrete reason.

For reviews, report findings by severity with file and line evidence. Distinguish
an observed failure from a platform risk that still needs execution evidence.
