# Cloud Monitoring dashboards API — full normalization inventory

What `dashboards.googleapis.com` (v1) does to your JSON between submit
(create/patch) and GET. Every "stripped" entry is a perpetual-drift cause if
present in Terraform config; every "injected" entry is harmless because
provider 5.0.0 and later suppresses it.

## Contents

1. [Computed fields (injected, top level)](#1-computed-fields-injected-top-level)
2. [proto3 zero-value stripping](#2-proto3-zero-value-stripping)
3. [Server-injected non-zero defaults](#3-server-injected-non-zero-defaults)
4. [Value / format canonicalization](#4-value--format-canonicalization)
5. [Provider diff-suppression mechanics](#5-provider-diff-suppression-mechanics)
6. [GitHub issue index](#6-github-issue-index)
7. [Workaround catalog](#7-workaround-catalog)

## 1. Computed fields (injected, top level)

| Field                      | Behavior                                                                                                        |
| -------------------------- | --------------------------------------------------------------------------------------------------------------- |
| `name`                     | Server-assigned `projects/NUM/dashboards/UUID`                                                                  |
| `etag`                     | Changes on every update; provider copies it from state into PATCH bodies automatically — never put it in config |
| `createTime`, `updateTime` | Computed timestamps                                                                                             |

Google's own export script strips exactly `name` and `etag`:
`gcloud monitoring dashboards describe ID --format=json | jq 'del(.name, .etag)'`
(monitoring-dashboard-samples `scripts/dashboard/dashboard.sh`).

## 2. proto3 zero-value stripping

The API omits every proto3 default from its responses. If your config
contains any of these, plan drifts forever (issue #16173 — the provider only
suppresses state-side extras, not config-side extras).

| What                    | Examples                                                                                                                                                                              |
| ----------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Zero integers (int32)   | `mosaicLayout.tiles[].xPos: 0`, `yPos: 0`                                                                                                                                             |
| Empty arrays            | `dashboardFilters: []`, dataSet `breakdowns: []` / `dimensions: []` / `measures: []`, `thresholds: []`, `aggregation.groupByFields: []`                                               |
| Empty objects           | top-level `labels: {}`                                                                                                                                                                |
| Empty strings           | `thresholds[].label: ""`, `labelKey: ""`, `stringValue: ""`                                                                                                                           |
| `false` booleans        | `pieChart.showLabels`, `sectionHeader.dividerBelow`, `collapsibleGroup.collapsed`, `columnSettings[].visible`, `timeSeriesQuery.outputFullDuration`, `chartOptions.displayHorizontal` |
| Explicit `null`         | any `"key": null` (proto3 JSON treats null as unset; `"targetAxis": null` does NOT work as a workaround)                                                                              |
| Zero-value enums        | see list below                                                                                                                                                                        |
| Legacy / unknown fields | `category: "CUSTOM"`, `timeSeriesQuery.apiSource: "DEFAULT_CLOUD"` (both emitted by the console "Copy JSON" button, both dropped by the API)                                          |
| Field-specific quirks   | `pieChart.dataSets[].minAlignmentPeriod` stripped (kept on `xyChart` dataSets); `scorecard.blankView: {}` not preserved (#15245)                                                      |

### Zero-value enums (dropped when set to the first enum value)

From the v1 discovery document (35 enum fields total); the ones commonly hit:

| Field                                                         | Zero value                         |
| ------------------------------------------------------------- | ---------------------------------- |
| `aggregation.crossSeriesReducer`                              | `REDUCE_NONE`                      |
| `aggregation.perSeriesAligner` (incl. `secondaryAggregation`) | `ALIGN_NONE`                       |
| `dataSets[].plotType`                                         | `PLOT_TYPE_UNSPECIFIED`            |
| `dataSets[].targetAxis`                                       | `TARGET_AXIS_UNSPECIFIED`          |
| `thresholds[].direction`                                      | `DIRECTION_UNSPECIFIED`            |
| `thresholds[].color`                                          | `COLOR_UNSPECIFIED`                |
| `yAxis.scale` / `xAxis.scale`                                 | `SCALE_UNSPECIFIED`                |
| `sparkChartView.sparkChartType`                               | `SPARK_CHART_TYPE_UNSPECIFIED`     |
| `text.format`                                                 | `FORMAT_UNSPECIFIED`               |
| `chartOptions.mode`                                           | `MODE_UNSPECIFIED`                 |
| `timeSeriesTable.metricVisualization`                         | `METRIC_VISUALIZATION_UNSPECIFIED` |
| `pieChart.chartType`                                          | `PIE_CHART_TYPE_UNSPECIFIED`       |
| `singleViewGroup.displayType`                                 | `DISPLAY_TYPE_UNSPECIFIED`         |
| `dashboardFilters[].filterType`                               | `FILTER_TYPE_UNSPECIFIED`          |
| `dimensions[]/breakdowns[].sortOrder`                         | `SORT_ORDER_UNSPECIFIED`           |

Rule of thumb: anything ending in `_UNSPECIFIED` or named `*_NONE` at enum
position 0 gets dropped. Never write these; omit the key instead.

## 3. Server-injected non-zero defaults

Suppressed by provider >= 5.0.0. Safe to include in config (matching the API)
or to omit (suppression hides them). They only show up in a plan diff as
`-` lines when something else already broke the comparison.

| Field                           | Injected value | Notes                                                                      |
| ------------------------------- | -------------- | -------------------------------------------------------------------------- |
| `xyChart.dataSets[].targetAxis` | `"Y1"`         | Server-side since 2021-08 (issue #9976); also on `thresholds[].targetAxis` |
| `text.style`                    | `{}`           | Empty TextStyle message returned on GET                                    |
| `dashboardFilters[].valueType`  | `"STRING"`     | When neither `valueType` nor `defaultValue` given                          |

## 4. Value / format canonicalization

| Field                                                                            | Behavior                                                                                                                                                                |
| -------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `gridLayout.columns`, `rowLayout.rows[].weight`, `columnLayout.columns[].weight` | int64 → returned as JSON **strings** (`"2"`). Write them as strings. Mosaic tile `xPos/yPos/width/height` are int32 and stay numeric.                                   |
| `thresholds[].value`                                                             | Rounded through float32: `0.995` → `0.99500000476837158`, `0.6` → `0.6000000238418579` (issue #8225, open, API-side). Use float32-exact values or commit the long form. |
| Duration fields (`alignmentPeriod`, `minAlignmentPeriod`, `timeshiftDuration`)   | Canonicalized to `"Ns"` google-duration strings. `timeshiftDuration: "0s"` is retained, not stripped.                                                                   |
| Enum casing                                                                      | Uppercase only; lowercase input rejected/renormalized (issue #8334).                                                                                                    |

## 5. Provider diff-suppression mechanics

Source: `google/services/monitoring/resource_monitoring_dashboard.go`
(handwritten; identical in google-beta).
Permalink: <https://github.com/hashicorp/terraform-provider-google/blob/abf19328c38821e204e95f0bc6763d47e7088ade/google/services/monitoring/resource_monitoring_dashboard.go>

- `dashboard_json` has a `DiffSuppressFunc`, a `StateFunc` running
  `NormalizeJsonString` (whitespace/key order never matter), and
  `UseJSONNumber: true`.
- The suppress function parses both strings, runs
  `removeComputedKeys(oldMap, newMap)` — recursively deleting every key
  present in **state** but absent from **config**, descending into maps and
  positionally into slices — then `reflect.DeepEqual`.
- One-directional by design: state-side extras suppressed, config-side extras
  (anything the API stripped) NOT suppressed → perpetual diff.
- No allowlist: `etag`/`name` are suppressed by the same generic rule.
- Documented consequence (registry docs warning): **legitimate remove-only
  diffs are also suppressed** — a key removal is only detected when paired
  with a non-removal change.
- No type coercion: `"columns": 2` (number) vs `"2"` (string from API) still
  diffs.
- Update PATCHes with the etag copied from prior state.
- History: suppression shipped in v5.0.0 (2023-09, PR #16014). Open rewrite
  proposals: magic-modules #15359 (bidirectional compare + hardcoded computed
  fields, open), #16878 (default-field whitelist, closed unmerged).
  Maintainers propose splitting into `dashboard_json` (intent) +
  `effective_dashboard_json` (computed) for a future major release
  (issue #16173, internal bug b/304483210).

## 6. GitHub issue index

| Issue / PR                                                                                                                                                                 | State  | Content                                                                                                                          |
| -------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------ | -------------------------------------------------------------------------------------------------------------------------------- |
| [terraform-provider-google#7242](https://github.com/hashicorp/terraform-provider-google/issues/7242)                                                                       | closed | Original perma-diff mega-thread: etag/name, xPos/yPos 0, REDUCE_NONE, ALIGN_NONE, apiSource, category, gridLayout columns string |
| [#9976](https://github.com/hashicorp/terraform-provider-google/issues/9976)                                                                                                | closed | `targetAxis: "Y1"` server-injected default                                                                                       |
| [#16173](https://github.com/hashicorp/terraform-provider-google/issues/16173)                                                                                              | open   | Post-5.0.0 perma-diffs: empty arrays/strings/maps in config; workarounds and 8.0 overhaul plan                                   |
| [#24650](https://github.com/hashicorp/terraform-provider-google/issues/24650)                                                                                              | open   | Drift with console-exported JSON                                                                                                 |
| [#15245](https://github.com/hashicorp/terraform-provider-google/issues/15245)                                                                                              | open   | `scorecard.blankView: {}` and `outputFullDuration: true` not preserved                                                           |
| [#8225](https://github.com/hashicorp/terraform-provider-google/issues/8225)                                                                                                | open   | Threshold values float32-rounded by the API                                                                                      |
| [#8334](https://github.com/hashicorp/terraform-provider-google/issues/8334)                                                                                                | open   | Enum case normalization                                                                                                          |
| [#16439](https://github.com/hashicorp/terraform-provider-google/issues/16439), [#17440](https://github.com/hashicorp/terraform-provider-google/issues/17440)               | closed | Crashes inside `removeComputedKeys` (fixed)                                                                                      |
| [magic-modules#9065](https://github.com/GoogleCloudPlatform/magic-modules/pull/9065) → [provider#16014](https://github.com/hashicorp/terraform-provider-google/pull/16014) | merged | The 5.0.0 suppression                                                                                                            |
| [magic-modules#15359](https://github.com/GoogleCloudPlatform/magic-modules/pull/15359)                                                                                     | open   | Bidirectional suppression rewrite                                                                                                |

## 7. Workaround catalog

Ordered by preference:

1. **Canonical-form config** (what this skill and its normalizer script do):
   commit exactly what the API returns, minus `name`/`etag`. Zero drift, full
   drift detection retained.
2. **Round-trip export**:
   `gcloud monitoring dashboards describe ID --format=json | jq 'del(.name,.etag)'`
   as the source of truth. Equivalent to 1 for consumers of console-designed
   dashboards.
3. **State dump**: `terraform show -json | jq -r '...dashboard_json'` pasted
   back into the file after a first apply.
4. **`ignore_changes` + `replace_triggered_by`** keyed on `filesha256` of the
   JSON (via `random_id` keepers or `null_resource` triggers): local edits
   force replacement, server noise ignored. Cost: dashboard is destroyed and
   recreated (new UUID/URL) on every edit, and console drift goes undetected.
5. **Plain `ignore_changes = [dashboard_json]`**: avoid; masks everything.
6. **Layout dodge**: `rowLayout`/`columnLayout` instead of `mosaicLayout`
   eliminates the xPos/yPos class entirely.

Validation: `gcloud monitoring dashboards create --config-from-file=f.json
--validate-only` is the only official validator (server-side). The
machine-readable schema is the discovery doc:
`https://monitoring.googleapis.com/$discovery/rest?version=v1`.

Template library: <https://github.com/GoogleCloudPlatform/monitoring-dashboard-samples>
(100+ ready dashboards under `dashboards/`, directly usable as `file()`
inputs; also a Grafana→Cloud Monitoring importer under
`scripts/dashboard-importer/`).
