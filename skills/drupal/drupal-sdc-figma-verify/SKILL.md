---
name: drupal-sdc-figma-verify
description: >
  Verify that an SDC component implementation matches the Figma design for colors,
  typography, spacing, border-radius, shadows, and DOM structure. Requires the official
  Figma MCP server (com.figma.mcp/mcp). Use when the user mentions "verify figma",
  "check tokens", "compare with figma", "design token audit", "SDC verify",
  "figma compliance", "token mismatch", "spacing check", "typography check",
  "color check", "does this match figma", or provides a Figma URL alongside a
  component name.
author: SparkFabrik
version: 1.2.0
---

# SDC ↔ Figma Token Verification

Verify that a Drupal SDC component implementation correctly uses design tokens matching the corresponding Figma frame. Produces an inline markdown report of mismatches and anti-patterns.

This skill delegates Figma access and token mapping discovery to the `figma-bridge`
skill (`.agents/skills/figma-bridge/SKILL.md`). Load it first to handle Phase B.

## Prerequisites

- **Figma MCP server** (`com.figma.mcp/mcp`) must be active and authenticated
- User provides a **Figma URL** of the frame/component to verify
- User provides the **SDC component name** (e.g., `lc-heading`, `lc-component-text-media`)

## Reference Documents

| Document | Location | When to Read |
|---|---|---|
| **Token Mapping** | `docs/figma-token-mapping.md` inside the **theme folder** | Always — contains the project-specific Figma→SCSS mapping for colors, typography, spacing, radius, shadows |
| **Figma MCP Usage** | `.agents/skills/figma-bridge/references/figma-mcp-usage.md` | Always — explains how to use MCP tools and extract/map CSS properties |

**Read both reference documents before starting any verification.**

### Locating the Token Mapping

The token mapping is stored **inside the Drupal theme**, not in this skill directory. To find it:

1. Identify the theme folder from the component path. The component path follows the pattern:
   `src/drupal/web/themes/custom/{theme_name}/components/{component_name}/`
2. The token mapping file is at:
   `src/drupal/web/themes/custom/{theme_name}/docs/figma-token-mapping.md`
3. If the file does not exist, inform the user that a token mapping must be created for this theme before verification can proceed. Offer to generate one by reading the theme's `scss/foundations/compiled/` and `scss/_settings.*.scss` files.

## Theme Path

Determined dynamically from the SDC component name. The typical structure is:
```
src/drupal/web/themes/custom/{theme_name}/
```

Components: `components/{component_name}/`
Foundations: `scss/foundations/compiled/`
Settings: `scss/_settings.*.scss`
Token Mapping: `docs/figma-token-mapping.md`

---

## Workflow

### Phase A — Collect Inputs

Ask the user for the following information (skip any already provided):

1. **Figma URL**: The full URL of the Figma frame or component to verify
   - Example: `https://www.figma.com/design/ABCdef123/Project-Design?node-id=1234-5678`

2. **SDC component name**: The component machine name (without theme namespace prefix)
   - Example: `lc-component-text-media`

3. **Breakpoint**: Which breakpoint does the Figma frame represent?
   - Options: `xxs` (mobile), `md` (tablet), `lg` (desktop), `xxl` (large desktop)
   - Default: `lg` if not specified

4. **Theme variant** (optional): If the component has theme variants
   - Options: `corporate`, `homepage`, `graduate`, `undergraduate`
   - Default: `corporate` if not specified

### Phase B — Extract Figma Properties

Load and execute the `figma-bridge` skill (`.agents/skills/figma-bridge/SKILL.md`).

Provide it with:
- The Figma URL from Phase A
- The theme name (derived from the component path)

`figma-bridge` will handle:
- URL parsing (`fileKey` / `nodeId` extraction)
- Token mapping discovery and loading
- MCP calls (`get_design_context`, `get_metadata`, `get_variable_defs`)
- Building the working table of extracted Figma values

Receive back the structured dataset (colors, typography, spacing, radius, shadows,
layer tree, token mapping status, unresolved values) and use it in Phase C onward.

### Phase C — Analyze SDC Component

Read the component files from the workspace:

1. **Component definition**: `components/{name}/{name}.component.yml`
   - Extract: props (especially theme/variant/layout props), slots

2. **SCSS styles**: `components/{name}/{name}.scss`
   - Extract all token references:
     - `@extend %placeholder-name` → look up in Typography/Radius tables
     - `@include mixin-name($property, $variant)` → look up in Spacing tables
     - `$color-*` or `$foundation-*` variables → look up in Color tables
     - `$shadow-*` variables → look up in Shadow table
     - Raw hex values (e.g., `#003a70`) → flag as potential hardcoded tokens
     - Raw px/rem values not using token variables → flag as potential hardcoded spacing
     - `$spacer * N` arithmetic → compute: N × 8px

3. **Twig template**: `components/{name}/{name}.twig`
   - Extract: DOM structure (element nesting, BEM class names)
   - Note inline styles or class conditionals based on props

#### Resolving Token Chains

For each token reference found in the SCSS, resolve to its final value using the token mapping:

```
@extend %heading-h2
  → %heading-h2 definition in _settings.typography.variables.scss
  → Mobile: font-size 36px, line-height 32px, weight 700, family ProjectSans
  → Desktop: font-size 52px, line-height 48px, weight 700, family ProjectSans

@include component-padding(padding-top, large)
  → component-padding-large in _settings.spacing.scss
  → xxs: 40px, md: 80px, lg: 104px, xxl: 104px

background-color: $color-primary-500
  → $foundation-color-brand-primary-500
  → resolved hex value from token mapping
```

### Phase D — Compare

For each property extracted from Figma (Phase B), find the corresponding SCSS token (Phase C) and compare values.

**Comparison rules:**

1. **Color comparison**: Compare hex values case-insensitively. Shorthand `#012` equals `#001122`.
2. **Size comparison**: Compare at the breakpoint specified by the user (Phase A, step 3). Convert rem to px (× 16) when comparing.
3. **Typography comparison**: Match font-size AND line-height AND font-weight AND font-family together as a set.
4. **Shadow comparison**: Normalize `rgba()` values and compare offset/blur/spread/color.
5. **Structure comparison**: Map Figma layer names to BEM class names. Check nesting depth matches.

**Classification:**

| Status | Meaning |
|---|---|
| ✅ Match | Figma value matches the resolved SCSS token value |
| ⚠️ Partial | Value matches but implementation uses hardcoded value instead of token variable/mixin |
| ❌ Mismatch | Figma value does NOT match the resolved SCSS value |
| ❓ Not found | Property exists in Figma but has no corresponding SCSS rule (or vice versa) |

**Anti-pattern detection:**

Flag these issues even when values match:
- **Hardcoded hex**: SCSS uses a raw hex instead of the corresponding colour variable
- **Hardcoded px**: SCSS uses a raw px value instead of the spacing mixin
- **Wrong token level**: SCSS uses a `$foundation-*` variable directly instead of the project alias
- **Missing responsive**: SCSS sets a value for one breakpoint but lacks responsive media queries when the token system provides multi-breakpoint values
- **Direct spacer math**: SCSS uses `$spacer * N` for a value that matches a named token

### Phase E — Report

Generate a **concise** report as inline markdown in the chat. The report must be **issues-only**: do NOT list properties that match (✅). Only report ❌ Mismatch, ⚠️ Partial, and ❓ Not found items, with a summary count at the top.

#### Report Format

```markdown
# SDC ↔ Figma Verification Report

**Component**: `lc-component-text-media`
**Figma**: [frame name](url)
**Breakpoint**: `xxs` (376px) / `lg` (1440px) · Variant: corporate · Date: YYYY-MM-DD

**Result**: N ✅ · N ⚠️ · N ❌ · N ❓

---

## Issues

### ❌ [Short title describing the mismatch]

Brief explanation of why it's a mismatch and what's affected.

| Property | Figma | SCSS | Resolved |
|---|---|---|---|
| padding-y | 8px (`token/name`) | none | 0px |

**Fix** in `component-file.scss`:
⁣```scss
// suggested fix code
⁣```

### ⚠️ [Short title describing the partial match]

Brief explanation. Mention if it requires design team confirmation.

### ❓ [Short title describing the not-found item]

Brief explanation of what's missing and potential impact.
```

#### Rules for the report

1. **Header**: Single line with component name, Figma link, breakpoints, variant, date
2. **Result line**: Total counts for all 4 statuses on one line
3. **Issues section**: One `###` subsection per issue, ordered by severity (❌ → ⚠️ → ❓)
4. **Each issue includes**: Title, brief explanation, property comparison table (only for mismatched values), and a fix suggestion when applicable
5. **Do NOT include**: Full tables of matching properties, category-by-category breakdowns of ✅ items, or verbose descriptions
6. **If all properties match**: Report only the header and result line, followed by "No issues found."

---

## Handling Edge Cases

### Component not found
If the SDC component directory does not exist under `components/`, inform the user and list available components matching partial name.

### Multiple theme variants in Figma
If the Figma frame contains multiple variant examples, ask the user which variant to verify, or run verification for each variant sequentially.

### Nested SDC components
If the Twig template includes other SDC components via `{% include %}` or `{{ include() }}`, note them in the report but do NOT recursively verify them unless the user explicitly asks.

### Dynamic values
If SCSS uses Twig variables or CSS custom properties set at runtime (e.g., `var(--theme-border-color)` set via variant class), trace the value through the variant class to find the resolved value.

### Token mapping outdated
If a hex value from Figma does not match any entry in the token mapping, read the actual foundation files (`scss/foundations/compiled/_colors.scss`, etc.) to check if the token mapping is outdated. Report the discrepancy.
