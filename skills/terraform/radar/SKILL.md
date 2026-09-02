---
name: radar
description: "Debug Kubernetes clusters with Radar (skyhook-io/radar), the dashboard and MCP server shipped in the pkg_terraform CLI image. Use this skill whenever the user mentions radar, radar-start, the radar MCP server, or wants to triage, debug, or inspect a cluster managed by a pkg_terraform project - live issues, pod logs, events, recent changes, Helm releases, metrics, or topology. Also use it to set up Radar locally, register its MCP endpoint in Claude Code, interpret Radar timeline symbols, or judge whether a Radar finding is a real problem or a known GKE false positive (gateway-api alpha webhook, gmp-system services scaled to zero, PDB matching Jobs, node-shutdown pod leftovers)."
---

# Radar: cluster debugging from a pkg_terraform project

Radar ([skyhook-io/radar](https://github.com/skyhook-io/radar)) is an open-source Kubernetes UI with a built-in MCP server. `pkg_terraform` ships it inside the terraform CLI image and manages its lifecycle with Just recipes. It runs under the same kubeconfig identity as the CLI container, with the cluster auto-configured from the project's environment.

## Local setup

Start, inspect, and stop Radar with the package recipes:

```bash
just radar-start   # start the container, wait for the dashboard, print the URL
just radar-list    # list running Radar instances with their URLs
just radar-logs    # container logs (auth or cluster-config failures show here)
just radar-stop    # stop the instance for this project
```

With `spark-http-proxy` running, the dashboard is served at `https://<project_name>-<project_id>.radar.sparkfabrik.loc`. Without the proxy it falls back to `http://localhost:9280` (override the port with `RADAR_PORT`).

The MCP endpoint is the dashboard URL plus `/mcp` (streamable HTTP, no auth: it is reachable only through the local proxy). `radar-start` detects Claude Code and offers to register the endpoint itself (`claude mcp add radar --scope local --transport http <url>/mcp`). Accept it, or run the command manually. Two things to know:

- **Tools appear at the next session.** MCP servers connect at session start; a registration made mid-session needs a new session (or `/mcp` reconnect) to expose the `mcp__radar__*` tools.
- **Re-register when the URL changes.** The FQDN embeds the project name and ID, so a package update that changes the naming scheme leaves a stale registration behind. Symptom: the radar MCP server fails to connect with `ENDPOINT_NOT_FOUND` while `just radar-list` shows the instance healthy at a different URL. Fix: `claude mcp remove radar`, then re-add with the URL that `radar-list` prints.

## Triage flow

Radar exposes about 30 MCP tools. Follow this order instead of jumping to logs:

- **`issues`** answers "what is broken right now": a ranked list of live failures across workloads, Jobs, HPAs, PVCs, Nodes, and dangling references. Start here for any broad symptom.
- **`get_dashboard`** gives an inventory-style overview of a namespace (counts, failing pods, warning-event groups, Helm status) when issues are empty or you need context.
- **`diagnose`** bundles resource state, current and previous logs, warning events, and recent changes for one broken workload in a single call. Prefer it over chaining get_resource, get_events, and log calls.
- **`get_pod_logs` / `get_workload_logs`** filter to diagnostically relevant lines by default; pass `grep` for a known error string and `previous: true` to read the log of a container that already restarted.
- **`get_changes`** answers "what changed": spec and ConfigMap diffs plus Helm operations, ranked. Use it when the symptom is "this worked before".
- **`search`** finds resources by content (config keys, env refs, images, CRD fields) when you do not know which object holds a string.
- **`top_resources` / `query_prometheus`** cover metric questions. Run `discover_metrics` before writing PromQL; never guess metric names.

The mutating tools (`apply_resource`, `patch_resource`, `manage_workload`, `manage_cronjob`, `manage_gitops`, `manage_rollout`, `manage_node`) change cluster state. Treat them as dangerous commands: explicit user confirmation before every call.

**Empty issues do not mean healthy.** Kubernetes only sees probe and exit-code failures. A process that exits 0 and restarts (for example a server with a max-requests-before-restart limit) looks healthy to the control plane while causing real outage windows. When an alert exists but `issues` is empty, go straight to container logs and previous-container logs, and correlate timestamps across namespaces.

**Radar has no acknowledge feature for issues.** The issues engine (OSS, verified on 1.12.1) cannot silence or acknowledge a finding. Only audit checks (`get_cluster_audit`) support hiding checks and ignoring namespaces. A known false positive must be documented (project docs, board issue), not acked away.

## Known GKE false positives and benign findings

Check this list before escalating a Radar finding on a GKE cluster.

### `webhook_backend_down` on `gateway-api-alpha-readonly.networking.gke.io` (critical)

Radar reports a critical missing-backend issue: the ValidatingWebhookConfiguration references Service `gateway-api-alpha-deprecated-use-beta-version` in `kube-system`, which does not exist, with `failurePolicy=Fail`.

This is a false positive on every GKE cluster with the Gateway API enabled (`gateway_api_channel = "CHANNEL_STANDARD"`). The webhook is installed by the GKE `gateway-api-crds` addon and the missing Service is intentional: a poison pill that makes writes to the deprecated `v1alpha2` Gateway API fail, as the Service name itself states. Impact is zero because the Gateway API CRDs serve only `v1` and `v1beta1`, so the API server rejects `v1alpha2` requests before admission and the webhook can never fire.

Do not delete the webhook: it carries `addonmanager.kubernetes.io/mode: Reconcile`, so the GKE addon manager recreates it. Verify with:

```bash
kubectl get validatingwebhookconfiguration gateway-api-alpha-readonly.networking.gke.io -o yaml
kubectl get crd gateways.gateway.networking.k8s.io -o jsonpath='{range .spec.versions[?(@.served==true)]}{.name}{"\n"}{end}'
```

### `service_no_endpoints` in `gmp-system` and `kube-system` (warning)

`gmp-system/alertmanager`, `gmp-system/rule-evaluator`, and `kube-system/antrea` select workloads intentionally scaled to zero in the default GKE managed-Prometheus and dataplane setup. Benign unless the team actively uses those components.

### `CalculateExpectedPodCountFailed` events (warning, high count)

A PodDisruptionBudget whose selector also matches Jobs emits this event repeatedly (`jobs.batch does not implement the scale subresource`). Noise, not an outage. The fix is narrowing the PDB selector so it matches only the long-running workload.

### Failed pods after node shutdown

Pods in `Failed`/`Error` phase with message `Pod was terminated in response to imminent node shutdown.` are leftovers of a node preemption or scale-down (common with spot nodes). The owning ReplicaSet already created replacements and ignores terminal pods; the objects persist until the control-plane GC threshold (default 12500 terminated pods) or a manual `kubectl delete pod`. A cadaver, not an active failure. StatefulSet pods do not leave these leftovers (same name is reused), so a double-hash pod name here always means a Deployment.

## Reading the timeline view

In the Timeline UI, per-resource rows use these markers: dots with `xN` are grouped change or rescale events, blue `▼` markers are deletions, the prohibition icon marks Warning events (probe failures), yellow diamonds are isolated warnings, and green row segments mean the resource was healthy for that span. A ReplicaSet row alternating deletions and warnings every few minutes usually indicates HPA flapping: check the HPA row for rescale events driven by two conflicting metrics (for example scale-up on CPU, scale-down on memory).

## Troubleshooting

- **Prometheus tools fail with "not connected".** Radar auto-discovers a Prometheus in the cluster and can pick the wrong service (for example cert-manager). Set the URL explicitly in Settings, Prometheus in the UI, or start Radar with `--prometheus-url` (plus `--prometheus-header` for auth).
- **Kinds misreported as denied on clusters with more than 20 namespaces.** Radar caps its RBAC namespace probe fanout at 20 by default. The `radar-start` recipe already passes `-max-scope-candidates 80`; raise `RADAR_MAX_SCOPE_CANDIDATES` further for bigger clusters.
- **Dashboard empty, no cluster configured.** `radar-start` prints a warning when cluster auto-config failed (missing `CLUSTER_TYPE` or credentials). Check `just radar-logs` and the project's `infra/terraform/.env`.
