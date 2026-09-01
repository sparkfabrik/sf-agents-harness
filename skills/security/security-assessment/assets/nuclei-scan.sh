#!/usr/bin/env bash
#
# nuclei-scan.sh -- run a Nuclei template/CVE scan against a URL, the safe way.
#
# Docker-based (no host install). Updates templates into a cached dir, asserts
# the template count is non-zero (an empty dir makes Nuclei "succeed" with 0
# matches while testing nothing), then scans. Local hostnames (.loc/.local/etc.)
# are auto-mapped to the Docker host so the container can reach them.
#
# Usage:
#   nuclei-scan.sh <target-url> [output-dir]
#
# Env overrides:
#   TAGS=drupal,cve                     template tags (empty = full set, noisy)
#   SEVERITY=low,medium,high,critical   severity filter
#   RL=50                               requests/sec (lower for prod/WAF)
#   TEMPLATES_DIR=~/.cache/nuclei-templates   cached across runs
#   IMAGE=projectdiscovery/nuclei:latest
#   LOCAL=auto                          auto|1|0 -- map the host to the Docker host
#   BASIC_AUTH=user:pass                HTTP Basic auth (staging behind a gate)
#   HEADER="Name: value"                one extra header (e.g. a bypass token)
#
# Exit codes: 0 ok, 1 usage, 2 no templates installed, 3 scan error, 4 auth preflight failed.

# No `set -u`: macOS bash 3.2 treats "${empty_array[@]}" as an unbound variable,
# and this script uses several optional arrays (headers, host map, tags).
set -eo pipefail

TARGET="${1:-}"
OUT_DIR="${2:-./nuclei-out}"
if [ -z "$TARGET" ]; then
  echo "usage: $0 <target-url> [output-dir]" >&2
  exit 1
fi

TAGS="${TAGS:-drupal,cve}"
SEVERITY="${SEVERITY:-low,medium,high,critical}"
RL="${RL:-50}"
# Throttle / resilience knobs. Defaults are gentle enough for a remote, WAF'd or
# basic-auth-gated host: the key one is MHE -- Nuclei skips a host after this many
# errors (default 30), which is what aborts a slow remote scan at "unresponsive
# permanently". C (concurrency) caps simultaneous connections; lower it before RL
# when an edge drops connections.
C="${C:-15}"           # parallel templates (nuclei default 25)
MHE="${MHE:-100}"      # max errors before a host is skipped (nuclei default 30; 0 = never skip)
RETRIES="${RETRIES:-1}"
TIMEOUT="${TIMEOUT:-15}"
# Protocol types to run. The input is a URL, so default to http only: tcp/ssl/etc.
# templates probe service ports the web target doesn't expose, producing nothing
# but connection-timeout errors. Set TYPES="" to run every protocol.
TYPES="${TYPES:-http}"
IMAGE="${IMAGE:-projectdiscovery/nuclei:latest}"
TEMPLATES_DIR="${TEMPLATES_DIR:-$HOME/.cache/nuclei-templates}"
LOCAL="${LOCAL:-auto}"

mkdir -p "$TEMPLATES_DIR" "$OUT_DIR"
TEMPLATES_DIR="$(cd "$TEMPLATES_DIR" && pwd)"
OUT_DIR="$(cd "$OUT_DIR" && pwd)"

# Extract the host from the URL (strip scheme, path, port).
host="${TARGET#*://}"; host="${host%%/*}"; host="${host%%:*}"

# Decide whether to map the host to the Docker host gateway. Local-only TLDs are
# resolvable on the workstation but not inside the container; public hosts must
# NOT be remapped or the scan would hit the wrong target.
map_host=0
case "$LOCAL" in
  1) map_host=1 ;;
  0) map_host=0 ;;
  auto)
    case "$host" in
      *.loc|*.local|*.test|*.localhost|*.internal|localhost|127.*) map_host=1 ;;
    esac ;;
esac
HOST_ARGS=()
if [ "$map_host" = 1 ]; then
  HOST_ARGS=(--add-host "$host:host-gateway")
  echo ">> mapping $host -> host-gateway (local target)"
fi

# Build the header args (Basic auth + one optional extra header). A global header
# is sent on every request and every template, which is what you want behind a
# gate -- otherwise the gate 401s everything and Nuclei reports a false "0 matches".
HEADER_ARGS=()
CURL_AUTH=()
if [ -n "${BASIC_AUTH:-}" ]; then
  b64="$(printf '%s' "$BASIC_AUTH" | base64 | tr -d '\n')"
  HEADER_ARGS+=(-H "Authorization: Basic $b64")
  CURL_AUTH=(--user "$BASIC_AUTH")
  echo ">> using HTTP Basic auth for ${BASIC_AUTH%%:*}"
fi
if [ -n "${HEADER:-}" ]; then
  HEADER_ARGS+=(-H "$HEADER")
fi

# Preflight: confirm the creds actually get past the gate. If the target still
# 401s with the header, abort -- scanning would just report a false clean.
if [ ${#HEADER_ARGS[@]} -gt 0 ]; then
  RESOLVE=()
  [ "$map_host" = 1 ] && RESOLVE=(--resolve "$host:443:host-gateway" --resolve "$host:80:host-gateway")
  echo ">> auth preflight on $TARGET"
  code="$(docker run --rm "${HOST_ARGS[@]}" curlimages/curl:latest \
    -sk -o /dev/null -w '%{http_code}' "${CURL_AUTH[@]}" "$TARGET" 2>/dev/null || echo 000)"
  echo ">> preflight HTTP $code"
  if [ "$code" = "401" ] || [ "$code" = "403" ]; then
    echo "FATAL: target still returns $code with the supplied auth -- check BASIC_AUTH. Aborting." >&2
    exit 4
  fi
fi

echo ">> updating templates in $TEMPLATES_DIR"
docker run --rm -v "$TEMPLATES_DIR:/root/nuclei-templates" \
  "$IMAGE" -update-templates 2>&1 | tail -2

count="$(find "$TEMPLATES_DIR" -name '*.yaml' | wc -l | tr -d ' ')"
echo ">> templates installed: $count"
if [ "$count" -le 0 ]; then
  echo "FATAL: 0 templates installed -- a scan now would be a false negative. Aborting." >&2
  exit 2
fi

# Most staging/prod is HTTPS-only. Scanning http:// against an HTTPS-only host
# makes :80 time out, Nuclei marks the host unresponsive, and the scan aborts
# early with a misleading "0 matches". Warn unless this is a local target.
case "$TARGET" in
  http://*)
    if [ "$map_host" = 0 ]; then
      echo ">> WARNING: target is http://. If the host is HTTPS-only, port 80 will time out and the scan will be dropped. Prefer https://." >&2
    fi ;;
esac

echo ">> scanning $TARGET (tags=${TAGS:-<all>} types=${TYPES:-<all>} severity=$SEVERITY rl=$RL c=$C mhe=$MHE retries=$RETRIES timeout=${TIMEOUT}s)"
TAG_ARGS=()
[ -n "$TAGS" ] && TAG_ARGS=(-tags "$TAGS")

# MHE=0 -> never skip the host on errors (-no-mhe), so no template is dropped no
# matter how slow/flaky the target is. Otherwise cap at MHE errors.
MHE_ARGS=()
if [ "$MHE" -eq 0 ] 2>/dev/null; then MHE_ARGS=(-no-mhe); else MHE_ARGS=(-mhe "$MHE"); fi

TYPE_ARGS=()
[ -n "$TYPES" ] && TYPE_ARGS=(-pt "$TYPES")

RUN_LOG="$OUT_DIR/nuclei-run.log"
# The scan runs in a daemon-owned container. Without this, Ctrl+C kills the local
# docker client but the container keeps scanning. Name it and kill it on INT/TERM.
CONTAINER="nuclei-scan-$$"
trap 'echo; echo ">> interrupted -- stopping container $CONTAINER"; docker kill "$CONTAINER" >/dev/null 2>&1; exit 130' INT TERM
set +e
docker run --rm --name "$CONTAINER" "${HOST_ARGS[@]}" \
  -v "$TEMPLATES_DIR:/root/nuclei-templates" \
  -v "$OUT_DIR:/out" \
  "$IMAGE" \
  -u "$TARGET" \
  "${TAG_ARGS[@]}" \
  "${TYPE_ARGS[@]}" \
  "${HEADER_ARGS[@]}" \
  -severity "$SEVERITY" \
  -rl "$RL" -c "$C" "${MHE_ARGS[@]}" -retries "$RETRIES" -timeout "$TIMEOUT" \
  -stats -disable-update-check \
  -je /out/nuclei.json \
  -se /out/nuclei.sarif \
  -elog /out/nuclei-errors.txt 2>&1 | tee "$RUN_LOG"
scan_rc=${PIPESTATUS[0]}
set -e
trap - INT TERM
[ "$scan_rc" -ne 0 ] && { echo "nuclei exited non-zero ($scan_rc)" >&2; exit 3; }

echo
echo ">> results: $OUT_DIR/nuclei.json"

# Request errors (timeouts, refused, TLS, unreachable paths) are transport
# failures, NOT vulnerabilities. -elog captured them; tally by cause so you can
# tell "the target is slow/blocking" from "real coverage".
if [ -s "$OUT_DIR/nuclei-errors.txt" ]; then
  echo ">> request errors: $OUT_DIR/nuclei-errors.txt (these are failed requests, not findings)"
  grep -oiE "i/o timeout|connection refused|no such host|context deadline exceeded|connection reset|tls|EOF|no address|403|429|502|503|504" \
    "$OUT_DIR/nuclei-errors.txt" 2>/dev/null | sort | uniq -c | sort -rn | sed 's/^/   /' | head
fi

# Trust check: if the host went unresponsive, the run is incomplete and a
# 0-match result means nothing. Surface that loudly.
if grep -q "unresponsive permanently" "$RUN_LOG" 2>/dev/null; then
  pct="$(grep -oE 'Requests: [0-9]+/[0-9]+ \([0-9]+%\)' "$RUN_LOG" | tail -1)"
  echo ">> UNRELIABLE: the host went unresponsive mid-scan (i/o timeout); only completed ${pct:-a fraction}." >&2
  echo ">> A '0 matches' here is NOT a clean result. Likely causes: wrong scheme (try https://), rate too high (lower RL), or a WAF dropping connections." >&2
fi

# Count matches. `-je` writes a JSON array, so [] is 0 (not 1, as `jq -s length` wrongly reports).
matches=0
if command -v jq >/dev/null 2>&1 && [ -s "$OUT_DIR/nuclei.json" ]; then
  matches="$(jq 'if type=="array" then length else 1 end' "$OUT_DIR/nuclei.json" 2>/dev/null || echo 0)"
  echo ">> matches: $matches"
  jq -r '(if type=="array" then .[] else . end) | "  [\(.info.severity)] \(."template-id") -> \(."matched-at")"' "$OUT_DIR/nuclei.json" 2>/dev/null || true
else
  echo ">> matches: 0 (empty output)"
fi

# Emit a coverage entry for the report's "Tests performed" section. Pulls the
# executed-template count and final error count from the run log.
executed="$(grep -oE 'Templates loaded for current scan: [0-9]+' "$RUN_LOG" 2>/dev/null | grep -oE '[0-9]+' | tail -1)"
executed="${executed:-0}"
errored="$(grep -oE 'Errors: [0-9]+' "$RUN_LOG" 2>/dev/null | grep -oE '[0-9]+' | tail -1)"
errored="${errored:-0}"
status="pass"; [ "$matches" -gt 0 ] 2>/dev/null && status="findings"
[ "$status" = "pass" ] && [ "$errored" -gt 0 ] 2>/dev/null && status="partial"
cat > "$OUT_DIR/coverage.json" <<JSON
[{"track":"PT","tool":"nuclei","category":"Nuclei templates (${TAGS:-all})","executed":${executed},"findings":${matches},"errored":${errored},"status":"${status}","note":"severity ${SEVERITY}; rl=${RL} c=${C}"}]
JSON
echo ">> coverage: $OUT_DIR/coverage.json (executed=$executed findings=$matches errored=$errored status=$status)"

# Emit a per-template checklist (Detailed test log): list the templates this run
# selected, mark each ok unless it produced a match. Cheap -tl call, no scan.
docker run --rm -v "$TEMPLATES_DIR:/root/nuclei-templates" "$IMAGE" \
  -tl "${TAG_ARGS[@]}" "${TYPE_ARGS[@]}" -severity "$SEVERITY" -disable-update-check 2>/dev/null \
  | sed -E 's/\x1b\[[0-9;]*m//g' | grep -E '\.yaml$' > "$OUT_DIR/nuclei-templates-run.txt" || true
if command -v jq >/dev/null 2>&1 && [ -s "$OUT_DIR/nuclei-templates-run.txt" ]; then
  matched_ids="$(jq -r '(if type=="array" then .[] else . end)."template-id"' "$OUT_DIR/nuclei.json" 2>/dev/null | sort -u)"
  python3 - "$OUT_DIR/nuclei-templates-run.txt" "$OUT_DIR/checklist.json" <<PYEOF 2>/dev/null || true
import json,sys
runf,out=sys.argv[1],sys.argv[2]
matched=set("""$matched_ids""".split())
rows=[]
for l in open(runf):
    t=l.strip()
    if not t: continue
    name=t.rsplit("/",1)[-1].replace(".yaml","")
    rows.append({"track":"PT","tool":"nuclei","name":name,"result":"problem" if name in matched else "ok"})
json.dump(rows,open(out,"w"))
print(len(rows))
PYEOF
  echo ">> checklist: $OUT_DIR/checklist.json ($(wc -l < "$OUT_DIR/nuclei-templates-run.txt" | tr -d ' ') templates)"
fi
