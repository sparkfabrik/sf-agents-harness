---
name: figma-bridge
description: >
  Generic Figma access skill. Handles URL parsing, Figma MCP tool usage
  (get_design_context, get_metadata, get_variable_defs, get_screenshot), and
  adaptive token mapping discovery. Automatically loads the project's
  figma-token-mapping.md if present and uses it as a lookup table; falls back
  to raw Figma values if no mapping exists. Use when any skill or workflow
  needs to connect to Figma, extract design properties, or resolve design
  tokens. Also use when the user mentions "figma url", "get figma data",
  "figma tokens", "leggi figma", "read figma", or when a Figma URL is
  provided as input to any verification or generation workflow.
author: SparkFabrik
version: 1.0.0
---

# Figma Bridge

Generic skill for connecting to Figma via the MCP server, extracting design
properties, and resolving design tokens against a project token mapping when
available.

## Prerequisites

- **Figma MCP server** (`com.figma.mcp/mcp`) must be active and authenticated
- User provides a **Figma URL** of the frame/component to access

## Reference Documents

| Document | Location | When to Read |
|---|---|---|
| **Figma MCP Usage** | `references/figma-mcp-usage.md` (relative to this skill) | Always — explains URL parsing, MCP tool parameters, and extraction workflow |

**Read the reference document before executing any Figma MCP call.**

---

## Step 1 — Parse Figma URL

Parse the provided Figma URL to extract `fileKey` and `nodeId` following the
rules in `references/figma-mcp-usage.md`.

---

## Step 2 — Discover Token Mapping (adaptive)

Before making any MCP call, check whether a project-level Figma token mapping
exists.

### How to locate the mapping

1. If the caller provides a **theme name or component path**, derive the theme
   folder from it. The typical pattern is:
   `src/drupal/web/themes/custom/{theme_name}/`

2. Look for the token mapping file at:
   `src/drupal/web/themes/custom/{theme_name}/docs/figma-token-mapping.md`

3. If no theme context is provided, search the workspace for any file named
   `figma-token-mapping.md`.

### Decision

| Situation | Action |
|---|---|
| `figma-token-mapping.md` found | Read it fully. Use it as the lookup table for all token resolution in Steps 4–5. |
| File not found | Proceed without a mapping. Report raw Figma values. Note in the output that no token mapping was found. |
| File found but outdated | Use it, but flag any hex values from Figma that do not match any entry. Suggest re-running `drupal-theme-setup` Phase B to regenerate the mapping. |

---

## Step 3 — Extract Figma Properties

Follow the extraction workflow in `references/figma-mcp-usage.md`:

1. Call `get_design_context(fileKey, nodeId)` — extract colors, typography,
   spacing, border-radius, shadows, and layer structure
2. Call `get_metadata(fileKey, nodeId, depth=3)` — extract layer hierarchy for
   DOM comparison (if requested by the caller)
3. Call `get_variable_defs(fileKey)` — resolve Figma variable references to
   concrete values (if the design context uses variables)

Record every extracted value in a working table:

```
| Layer/Element | Property | Figma Value | Figma Variable (if any) |
```

---

## Step 4 — Resolve Tokens (if mapping available)

If a `figma-token-mapping.md` was found in Step 2, resolve each Figma value
to its corresponding SCSS token:

```
Figma: background-color #HEX
  → Lookup in Colors table → $color-primary-500

Figma: font-size 52px (desktop)
  → Lookup in Typography table → %heading-h2

Figma: padding 80px at lg breakpoint
  → Lookup in Spacing table → component-padding-standard
```

If a value cannot be matched in the mapping, check the raw foundation files
(`scss/foundations/compiled/`) to determine whether the mapping is outdated.

---

## Step 5 — Return Extracted Data

Return a structured dataset to the calling skill or workflow:

```
Figma Properties:
  Colors:       [ { layer, property, figmaValue, scssToken } ]
  Typography:   [ { layer, property, figmaValue, scssToken } ]
  Spacing:      [ { layer, property, figmaValue, scssToken } ]
  Radius:       [ { layer, property, figmaValue, scssToken } ]
  Shadows:      [ { layer, property, figmaValue, scssToken } ]
  LayerTree:    (if get_metadata was called)

Token Mapping: loaded | not found
Unresolved:   [ { figmaValue, reason } ]
```

---

## Standalone Use

When used directly (not called by another skill), present the extracted data
as a readable summary in the chat, including:

- Figma file name and node ID
- Token mapping status (loaded / not found)
- Extracted properties table
- Unresolved values (if any)
