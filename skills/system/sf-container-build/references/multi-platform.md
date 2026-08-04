# Multi-platform builds

Use this reference when a Dockerfile or publishing pipeline handles more than
one platform or installs architecture-specific artifacts.

## Platform model

Treat target compatibility as four related dimensions:

- **OS.** Usually Linux, but CLI artifact images may also carry Darwin or
  Windows outputs.
- **Architecture.** Common values include `amd64`, `arm64`, and `arm`.
- **Variant.** ARM targets may require a variant such as `v7`.
- **ABI.** Native Linux artifacts may distinguish glibc from musl even when OS
  and architecture match.

Base image manifests solve only the base-layer part of this contract. Every
binary copied, downloaded, compiled, or installed later must support the same
tuple.

## BuildKit arguments

BuildKit provides platform values automatically, but a stage must declare the
arguments it uses:

```dockerfile
# syntax=docker/dockerfile:1

FROM alpine:<supported-release> AS artifact
ARG TARGETOS
ARG TARGETARCH
ARG TARGETVARIANT

RUN printf 'target=%s/%s/%s\n' "$TARGETOS" "$TARGETARCH" "$TARGETVARIANT"
```

Use these values for target selection. `uname -m` reports the architecture of
the stage currently executing, which may be the build host under
`FROM --platform=$BUILDPLATFORM`.

Replace version placeholders with releases inside the vendor support window.
Keep them current through automated, reviewed updates.

## Vendor artifact mapping

Vendors use inconsistent platform names. Keep mapping visible and reject
unknown values:

```dockerfile
ARG TARGETARCH

COPY checksums/ /checksums/

RUN case "$TARGETARCH" in \
      amd64) vendor_arch="x86_64" ;; \
      arm64) vendor_arch="aarch64" ;; \
      *) echo "unsupported TARGETARCH: $TARGETARCH" >&2; exit 1 ;; \
    esac \
    && artifact="tool-${vendor_arch}-linux.tar.gz" \
    && checksum="/checksums/${artifact}.sha256" \
    && { test -s "$checksum" \
      || { echo "missing checksum file: $checksum" >&2; exit 1; }; } \
    && curl --fail --location --silent --show-error \
      "https://downloads.example.test/${artifact}" \
      --output "/tmp/${artifact}" \
    && (cd /tmp && sha256sum -c "$checksum") \
    && tar -xzf "/tmp/${artifact}" -C /usr/local/bin \
    && rm "/tmp/${artifact}"
```

Each committed checksum file lists the bare artifact filename, so the check runs
from the download directory. Use `sha256sum -c` rather than the `--check` long
option, which BusyBox `sha256sum` on Alpine does not support.

Store real checksums for every supported artifact. Do not use one checksum for
multiple architectures, and do not silently fall back to amd64.

For Linux binaries, add libc to selection when the vendor publishes separate
glibc and musl builds. If the vendor does not support the required tuple, use a
compatible base, install through a supported package manager, build from source,
or remove that tuple from the declared contract.

## Cross-compilation

Pin the builder to the native build platform only for a real cross-compiling
toolchain:

```dockerfile
FROM --platform=$BUILDPLATFORM golang:<supported-minor>-alpine AS build
ARG TARGETOS
ARG TARGETARCH

WORKDIR /src
COPY go.mod go.sum ./
RUN go mod download
COPY . .
RUN CGO_ENABLED=0 GOOS="$TARGETOS" GOARCH="$TARGETARCH" \
    go build -trimpath -o /out/service ./cmd/service
```

Do not copy this pattern blindly when CGO, native extensions, target executables,
or target-specific package hooks run during the build. Those builds may need a
target-platform stage, a native runner, or an explicit cross toolchain and
sysroot.

## Build and publish flow

A clear multi-platform publishing flow:

1. Build and test each target on a native runner where practical.
2. Keep cache keys scoped by target, stage, and image flavor.
3. Push each target by digest.
4. Fail if any required digest is absent.
5. Assemble the tag into a manifest list from those digests.
6. Inspect the published manifest and verify its platform set.

QEMU can execute foreign architecture stages, but it is slower for compilation
and compression. It also does not replace production-like runtime tests.

## Runtime smoke tests

Test behavior, not file presence. Depending on image purpose, run one or more of:

- **Service image.** Start the container, wait for readiness, send one request,
  and stop it through the expected signal path.
- **CLI image.** Execute `--version`, a help command, and one small functional
  operation.
- **Tooling image.** Execute every downloaded native tool at least once.
- **Artifact carrier.** Extract the artifact and execute or inspect each target
  output in its intended environment.

If CI cannot execute a target, label it unverified instead of presenting a
successful build as complete support.

## References

- [Docker multi-platform builds](https://docs.docker.com/build/building/multi-platform/)
- [Docker automatic platform arguments](https://docs.docker.com/reference/dockerfile/#automatic-platform-args-in-the-global-scope)
- [Docker buildx imagetools](https://docs.docker.com/reference/cli/docker/buildx/imagetools/)
