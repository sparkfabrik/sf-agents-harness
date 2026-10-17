#!/usr/bin/env bash
# Self-test for leakscan.py. Builds throwaway repositories so each case is exact,
# rather than hoping a real commit happens to contain the shape under test.
#
# Run: bash selftest.sh
set -uo pipefail

SCAN="$(cd "$(dirname "$0")" && pwd)/leakscan.py"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

pass=0
fail=0

# case <name> <expected-exit> <file-content> [allowlist-line]
case_run() {
  local name="$1" want="$2" content="$3" allow="${4:-}"
  local dir="$TMP/$name"
  mkdir -p "$dir"
  git -C "$dir" init -q
  git -C "$dir" config user.email t@e; git -C "$dir" config user.name t
  printf '%s\n' "placeholder" > "$dir/seed"
  git -C "$dir" add -A; git -C "$dir" commit -qm seed
  printf '%s\n' "$content" > "$dir/file.txt"
  [ -n "$allow" ] && printf '%s\n' "$allow" > "$dir/.leakcheck-allow"
  git -C "$dir" add -A

  local out rc
  out="$(python3 "$SCAN" --repo "$dir" --staged 2>&1)"; rc=$?
  if [ "$rc" -eq "$want" ]; then
    pass=$((pass+1)); printf '  ok    %-34s exit %d\n' "$name" "$rc"
  else
    fail=$((fail+1)); printf '  FAIL  %-34s exit %d, want %d\n%s\n' "$name" "$rc" "$want" "$out"
  fi
}

echo "leak-check self-test"
echo
echo "No origin remote, so visibility is unknown and findings block — the safe default:"

# A credential blocks wherever it is going.
case_run "aws-key"            1 'AWS_KEY = "AKIAIOSFODNN7EXAMPLE"'   # leakcheck: ignore — synthetic fixture
case_run "private-key"        1 '-----BEGIN RSA PRIVATE KEY-----'   # leakcheck: ignore — synthetic fixture
case_run "gitlab-pat"         1 'token: glpat-abcdefghij1234567890'   # leakcheck: ignore — synthetic fixture
case_run "hardcoded-password" 1 'password = "hunter2hunter2"'   # leakcheck: ignore — synthetic fixture

# Internal resources block when visibility is not established.
case_run "service-account"    1 'sa: builder@my-project.iam.gserviceaccount.com'   # leakcheck: ignore — synthetic fixture
case_run "registry-path"      1 'img=europe-west1-docker.pkg.dev/proj/repo/name:latest'   # leakcheck: ignore — synthetic fixture
case_run "saas-url"           1 'see https://acme.atlassian.net/wiki/spaces/INT/pages/12345'   # leakcheck: ignore — synthetic fixture
case_run "self-hosted-forge"  1 'clone from https://gitlab.acme.com/team/project.git'   # leakcheck: ignore — synthetic fixture
case_run "internal-host"      1 'host: db01.corp'   # leakcheck: ignore — synthetic fixture
case_run "private-ip"         1 'upstream 10.4.12.9:8080'   # leakcheck: ignore — synthetic fixture
case_run "cluster-dns"        1 'svc: api.prod.svc.cluster.local'   # leakcheck: ignore — synthetic fixture

echo
echo "Not findings:"

# Documentation and placeholders must not cry wolf, or the check gets ignored.
case_run "example-domain"     0 'curl https://example.com/api'   # leakcheck: ignore — synthetic fixture
case_run "env-var-reference"  0 'registry: ${ARTIFACT_REGISTRY}/image:tag'   # leakcheck: ignore — synthetic fixture
case_run "placeholder-token"  0 'token: YOUR_TOKEN_HERE'   # leakcheck: ignore — synthetic fixture
case_run "redacted"           0 'sa: REDACTED@REDACTED.iam.gserviceaccount.com'   # leakcheck: ignore — synthetic fixture
case_run "prose-mentioning"   0 '# e.g. a service account like builder@x.iam.gserviceaccount.com'   # leakcheck: ignore — synthetic fixture

# An allowlisted string is legitimate for that repository.
case_run "allowlisted"        0 'img=europe-west1-docker.pkg.dev/proj/repo/x' 'europe-west1-docker.pkg.dev/proj/repo/x'   # leakcheck: ignore — synthetic fixture

echo
echo "  $pass passed, $fail failed"
[ "$fail" -eq 0 ]
