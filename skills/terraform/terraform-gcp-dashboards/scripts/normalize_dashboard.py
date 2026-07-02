#!/usr/bin/env python3
"""Normalize a Cloud Monitoring dashboard JSON file to the API canonical form.

The dashboards.googleapis.com API strips proto3 defaults (zero ints, empty
arrays/objects/strings, false booleans, zero-value enums, nulls) and legacy
fields from every write. The Terraform google provider (>= 5.0.0) suppresses
keys the API *adds*, but NOT keys the API *strips* from your config
(hashicorp/terraform-provider-google#16173). Any such key in the committed
JSON causes a perpetual plan diff.

This script rewrites the JSON so it matches what the API will return, which
makes `terraform plan` stay clean.

Usage:
    normalize_dashboard.py FILE            # print normalized JSON to stdout
    normalize_dashboard.py FILE --write    # rewrite FILE in place
    normalize_dashboard.py FILE --check    # exit 1 if FILE needs changes (CI)

Exit codes: 0 = clean / written, 1 = --check found differences, 2 = error.
"""

import argparse
import json
import re
import struct
import sys

# Top-level fields computed by the server. Never commit them.
COMPUTED_TOP_LEVEL = ("name", "etag", "createTime", "updateTime")

# Fields the API no longer knows about; silently dropped on write. The GCP
# console "Copy JSON" button still emits them.
LEGACY_KEYS = ("category", "apiSource")

# Zero-value enum members: proto3 omits them from responses. Everything
# ending in _UNSPECIFIED is also a zero value (checked separately).
ZERO_ENUMS = ("REDUCE_NONE", "ALIGN_NONE")

# Keys whose *empty object* value is meaningful widget content, not a
# strippable default. blankView is intentionally NOT here: the API does not
# preserve it (provider issue #15245), so keeping it in config would drift.
MEANINGFUL_EMPTY_OBJECTS = (
    "blank",
    "sectionHeader",
    "singleViewGroup",
    "logsPanel",
    "errorReportingPanel",
    "incidentList",
)

# int64-format fields: the API returns them as JSON strings.
INT64_STRING_KEYS = ("columns", "weight")

warnings = []


def warn(msg):
    warnings.append(msg)


def is_strippable(key, value):
    """True if the API would omit this key/value pair from its response."""
    if value is None:
        return True
    if value is False:
        return True
    if value == [] or value == "":
        return True
    if value == {} and key not in MEANINGFUL_EMPTY_OBJECTS:
        return True
    if key in ("xPos", "yPos") and value == 0:
        return True
    if isinstance(value, str):
        if value in ZERO_ENUMS or value.endswith("_UNSPECIFIED"):
            return True
    if key in LEGACY_KEYS:
        return True
    return False


def float32_exact(x):
    return struct.unpack("f", struct.pack("f", x))[0] == x


def normalize(node, path=""):
    """Recursively strip API-omitted values. Returns the normalized node."""
    if isinstance(node, dict):
        out = {}
        for key, value in node.items():
            child_path = f"{path}.{key}" if path else key
            value = normalize(value, child_path)

            # pieChart dataSets lose minAlignmentPeriod on write
            # (xyChart dataSets keep it).
            if key == "minAlignmentPeriod" and ".pieChart.dataSets" in f".{child_path}":
                warn(f"{child_path}: minAlignmentPeriod is dropped by the API "
                     "on pieChart dataSets; removed")
                continue

            if key == "blankView" and value == {}:
                warn(f"{child_path}: blankView {{}} is not preserved by the "
                     "API (provider issue #15245); removed")
                continue

            if is_strippable(key, value):
                continue

            # int64 fields come back as strings ("2", not 2).
            if key in INT64_STRING_KEYS and isinstance(value, int) and "mosaicLayout" not in path:
                value = str(value)

            # Threshold values pass through float32 on the API side.
            if key == "value" and re.search(r"thresholds\[\d+\]$", path) and isinstance(value, float):
                if not float32_exact(value):
                    rounded = struct.unpack("f", struct.pack("f", value))[0]
                    warn(f"{child_path}: {value} is not float32-exact; the "
                         f"API stores it as {rounded!r} (provider issue "
                         "#8225). Use a float32-exact value or commit the "
                         "long form.")

            # Enums must be uppercase.
            if isinstance(value, str) and value.islower() and key in (
                "plotType", "sparkChartType", "crossSeriesReducer",
                "perSeriesAligner", "targetAxis", "scale", "direction",
                "color", "format", "mode", "chartType",
            ):
                warn(f"{child_path}: enum value {value!r} is lowercase; the "
                     "API requires uppercase")

            out[key] = value
        return out

    if isinstance(node, list):
        # Normalize elements; drop elements that normalize to nothing.
        result = []
        for i, item in enumerate(node):
            item = normalize(item, f"{path}[{i}]" if path else f"[{i}]")
            if item == {} or item is None:
                continue
            result.append(item)
        return result

    return node


def main():
    parser = argparse.ArgumentParser(description=(__doc__ or "").splitlines()[0])
    parser.add_argument("file", help="dashboard JSON file")
    parser.add_argument("--write", action="store_true",
                        help="rewrite the file in place")
    parser.add_argument("--check", action="store_true",
                        help="exit 1 if the file needs normalization (CI)")
    args = parser.parse_args()

    try:
        with open(args.file) as fh:
            original = json.load(fh)
    except (OSError, json.JSONDecodeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    normalized = dict(normalize(original))
    for key in COMPUTED_TOP_LEVEL:
        normalized.pop(key, None)

    changed = normalized != original
    rendered = json.dumps(normalized, indent=2, ensure_ascii=False) + "\n"

    for message in warnings:
        print(f"warning: {message}", file=sys.stderr)

    if args.check:
        if changed:
            print(f"{args.file}: needs normalization (would cause perpetual "
                  "terraform drift)", file=sys.stderr)
            return 1
        print(f"{args.file}: canonical", file=sys.stderr)
        return 0

    if args.write:
        with open(args.file, "w") as fh:
            fh.write(rendered)
        state = "normalized" if changed else "already canonical"
        print(f"{args.file}: {state}", file=sys.stderr)
        return 0

    sys.stdout.write(rendered)
    return 0


if __name__ == "__main__":
    sys.exit(main())
