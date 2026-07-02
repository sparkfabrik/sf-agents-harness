---
name: terraform-gcp-dashboards
description: 'Create and manage Google Cloud Monitoring dashboards with Terraform (google_monitoring_dashboard) without perpetual plan drift. Use this skill whenever the user works with GCP monitoring dashboards in Terraform or any IaC context - creating a new dashboard, exporting a console dashboard to code, importing an existing dashboard into state, or debugging a terraform plan that keeps showing an in-place update on dashboard_json even right after apply. Trigger on mentions of google_monitoring_dashboard, dashboard_json, Cloud Monitoring / Stackdriver dashboards, dashboard drift, perma-diff, permadiff, "plan is never clean", mosaicLayout, or gcloud monitoring dashboards.'
---

# GCP Cloud Monitoring Dashboards with Terraform (drift-free)

The `google_monitoring_dashboard` resource takes a single JSON string
(`dashboard_json`). The Cloud Monitoring API **normalizes that JSON on every
write**: it strips proto3 default values, injects server-side defaults, and
adds computed fields. If the committed JSON does not match the API's canonical
form, every `terraform plan` shows an in-place update forever, even
immediately after `apply`.

## Why drift happens (read this first)

The provider (>= 5.0.0) compares old (state = API GET response) and new
(config) JSON semantically, after deleting from **state** every key that is
absent from **config** (`removeComputedKeys` in
`resource_monitoring_dashboard.go`). This makes the suppression
**one-directional**:

- Keys the API **injects** (`etag`, `name`, `targetAxis: "Y1"`, `style: {}`,
  `createTime`, `updateTime`) are suppressed automatically. They never cause
  drift on their own.
- Keys present in **config** that the API **strips** (`xPos: 0`, empty
  arrays/objects/strings, zero-value enums, `null`s, legacy fields) are NOT
  suppressed. Each one causes a perpetual diff. This is open provider issue
  hashicorp/terraform-provider-google#16173.

**Golden rule: the committed JSON must never contain a value the API will
omit from its response.** Anything the API adds on top is harmless.

Corollary: when a plan shows a dashboard diff, classify each changed line:

- `+ key = <zero/empty value>` (config-only) -> **remove it from your JSON**.
  This is the real cause.
- `- key = <value>` (state-only, e.g. `- etag`, `- targetAxis = "Y1"`) ->
  noise. It only appears because something else already broke the comparison.
  Fixing the config-only keys makes these disappear too.

## Quick fix for a drifting dashboard

Run the bundled normalizer on the JSON file, then re-plan:

```bash
python3 scripts/normalize_dashboard.py path/to/dashboard.json --write
terraform plan   # should now be clean
```

The script rewrites the file into API-canonical form (see
[the full rule list](references/normalization-rules.md)). `--check` mode
exits non-zero without writing, for CI. Applying the normalized file is a
no-op on the deployed dashboard: it only aligns the source with what is
already stored.

## Workflows

### A. New dashboard, authored by hand

1. Write minimal JSON: only non-default values. Do not write `xPos: 0`,
   `yPos: 0`, empty arrays (`dashboardFilters: []`, `thresholds: []`), empty
   strings, `null`s, or zero enums (`REDUCE_NONE`, `ALIGN_NONE`, anything
   `*_UNSPECIFIED`).
2. Run `scripts/normalize_dashboard.py file.json --check` to catch mistakes.
3. Validate server-side without creating anything:

   ```bash
   gcloud monitoring dashboards create --config-from-file=file.json \
     --validate-only --project=PROJECT_ID
   ```

4. Wire it up (this is also the recommended module shape used by Google's own
   monitoring-dashboard-samples repo):

   ```hcl
   resource "google_monitoring_dashboard" "main" {
     project        = var.project_id
     dashboard_json = file("${path.module}/dashboards/main.json")
   }
   ```

5. `terraform apply`, then run `terraform plan` again and confirm
   "No changes". A dashboard that drifts on the very next plan means step 1
   left a to-be-stripped value in; run the normalizer.

### B. Export an existing console dashboard to code

Design freely in the GCP console (use a scratch dashboard), then export the
**API canonical form**. Never use the console's "Copy JSON" button: it emits
console-only fields (`category: "CUSTOM"`, `apiSource: "DEFAULT_CLOUD"`) that
the API drops, guaranteeing drift.

```bash
# find the dashboard ID
gcloud monitoring dashboards list --project=PROJECT_ID \
  --format="table(name, displayName)"

# export canonical JSON, strip computed fields
gcloud monitoring dashboards describe DASHBOARD_ID --project=PROJECT_ID \
  --format=json | jq 'del(.name, .etag)' > dashboards/main.json
```

Run the normalizer anyway (`--check`): `describe` output is already
canonical, but the pass costs nothing and catches API/tooling changes.

To adopt the live dashboard instead of recreating it:

```bash
terraform import google_monitoring_dashboard.main \
  projects/PROJECT_NUMBER/dashboards/DASHBOARD_UUID
```

After import, `terraform plan` must be clean before you touch anything else.

### C. Update a managed dashboard

Never edit the Terraform-managed dashboard in the console (Google documents
that console edits rescale the layout, and any edit is silent drift). Two
sane paths:

- Edit the JSON file directly, normalize, plan, apply.
- Clone to a scratch dashboard in the console, edit visually, re-export as in
  workflow B, replace the file.

**Remove-only edits are silently ignored.** The provider's suppression cannot
distinguish "user deleted this key" from "API never returned it", so a diff
that only removes keys shows "No changes". Pair every pure removal with any
real change (e.g. bump `displayName`), or `terraform apply -replace=...` the
resource.

## Terraform patterns and their trade-offs

| Pattern                                           | Use when                                     | Caveats                                                                                                   |
| ------------------------------------------------- | -------------------------------------------- | --------------------------------------------------------------------------------------------------------- |
| `file("d.json")`                                  | Default choice                               | JSON stays byte-comparable with `gcloud describe` exports and usable with `--validate-only`               |
| `templatefile("d.json.tpl", {...})`               | Need to inject project IDs, filters          | Escape literal `${...}` in MQL/PromQL as `$${...}`; rendered output no longer round-trips with gcloud     |
| `jsonencode({ ... })` (HCL object)                | Small dashboards, want structural plan diffs | Loses gcloud round-trip and offline file validation; drift rules identical (comparison is on parsed JSON) |
| `lifecycle { ignore_changes = [dashboard_json] }` | Avoid                                        | Masks all drift including console edits and blocks intentional updates; a bandaid, not a fix              |

Require provider `hashicorp/google >= 5.0.0` (the suppression shipped there;
before it, even API-injected fields perma-diffed). `google-beta` uses the
identical code, no benefit for dashboards.

## Known pitfalls beyond key stripping

- **Threshold float rounding**: the API rounds `thresholds[].value` through
  float32 (`0.995` -> `0.99500000476837158`). Use float32-exact values
  (0.25, 0.5, 0.75, 1, ...) or commit the long form the API returns.
  Provider issue #8225, unfixable client-side.
- **int64 fields are strings**: `gridLayout.columns`, `rowLayout.rows[].weight`,
  `columnLayout.columns[].weight` come back as JSON strings (`"2"` not `2`).
  Write them as strings. (Mosaic tile `xPos/yPos/width/height` are int32 and
  stay numbers.)
- **Enums are uppercase**: `"line"` is not `"LINE"`; lowercase values are
  rejected or renormalized.
- **`pieChart.dataSets[].minAlignmentPeriod`** is silently dropped by the API
  (kept on `xyChart` dataSets). Do not set it on pie charts.
- **`scorecard.blankView: {}`** is not preserved on write (issue #15245);
  don't rely on it.
- **`mosaicLayout` is the drift-heavy layout** (xPos/yPos zeros). `rowLayout`
  / `columnLayout` avoid that whole class if precise tile placement is not
  needed.

## When the plan still is not clean

1. Extract only the real signal: config-only additions (`+`) in the diff.
2. Check each against
   [references/normalization-rules.md](references/normalization-rules.md) -
   the full inventory of stripped, injected, and canonicalized fields with
   sources (provider source walkthrough, discovery-doc enum list, GitHub
   issue index).
3. Last-resort escape hatch: dump the state's normalized JSON and use it as
   the new source of truth:

   ```bash
   terraform show -json \
     | jq -r '.values.root_module.resources[]
              | select(.address=="google_monitoring_dashboard.main")
              | .values.dashboard_json' \
     | jq 'del(.name, .etag)' > dashboards/main.json
   ```
