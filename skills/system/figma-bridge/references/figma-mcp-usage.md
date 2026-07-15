# Figma MCP Usage Reference

How to use the official Figma MCP server (`com.figma.mcp/mcp`) to extract design token data from Figma frames.

---

## URL Parsing

Extract `fileKey` and `nodeId` from Figma URLs:

| URL Pattern | Extraction |
|---|---|
| `figma.com/design/:fileKey/:fileName?node-id=:nodeId` | Use `fileKey`, convert `-` to `:` in `nodeId` |
| `figma.com/design/:fileKey/branch/:branchKey/:fileName` | Use `branchKey` as `fileKey` |
| `figma.com/make/:makeFileKey/:makeFileName` | Use `makeFileKey` |
| `figma.com/board/:fileKey/:fileName` | FigJam file — use `get_figjam` |

**Example:**
```
URL: https://www.figma.com/design/ABCdef123/Project-Design?node-id=1234-5678
  → fileKey: ABCdef123
  → nodeId: 1234:5678  (replace - with :)
```

---

## Primary Tool: `get_design_context`

**When to use**: Always start here. Returns code reference, screenshot, and contextual hints.

**Parameters**:
- `fileKey` (required): The Figma file key
- `nodeId` (required): The node ID (with `:` separator)

**Returns**:
- React+Tailwind reference code (use as visual reference only, not for implementation)
- Screenshot of the node
- Design annotations from the designer
- Code Connect snippets (if configured)
- Component documentation links
- Design tokens as CSS variables (if available)

**What to extract for token verification**:
1. **Colors**: Look for `fill`, `background-color`, `color`, `border-color` values
2. **Typography**: Look for `font-family`, `font-size`, `font-weight`, `line-height` values
3. **Spacing**: Look for `padding`, `margin`, `gap` values
4. **Border radius**: Look for `border-radius` values
5. **Shadows**: Look for `box-shadow` values
6. **Token references**: Look for Figma variable names in annotations

---

## Supporting Tool: `get_metadata`

**When to use**: To get the full layer hierarchy (XML structure) of a Figma node.

**Parameters**:
- `fileKey` (required)
- `nodeId` (required)
- `depth` (optional): How deep to traverse child layers

**Returns**: XML-like structure with:
- Node names and types (FRAME, TEXT, RECTANGLE, INSTANCE, etc.)
- Layer hierarchy (useful for comparing with Twig DOM structure)
- Component instance references

**Use for**: DOM structure comparison — map Figma layer names to BEM class names in the SDC component.

---

## Supporting Tool: `get_variable_defs`

**When to use**: To get the variable definitions (token names → values) used in the file.

**Parameters**:
- `fileKey` (required)

**Returns**: Variable collections with:
- Variable names (e.g., `color/brand/primary/500`)
- Resolved values per mode (light/dark, or variant-specific)
- Variable types (COLOR, FLOAT, STRING)

**Use for**: Cross-referencing Figma variable names with the token mapping table.

---

## Supporting Tool: `get_screenshot`

**When to use**: When you need a visual reference of a specific node.

**Parameters**:
- `fileKey` (required)
- `nodeId` (required)
- `format` (optional): `png`, `svg`, `pdf`

**Returns**: Image of the node.

**Use for**: Visual comparison with the rendered component.

---

## Extraction Workflow

### Step 1 — Get design context
```
Call: get_design_context(fileKey, nodeId)
Extract: Screenshot + CSS properties + token references
```

### Step 2 — Get layer hierarchy (if needed for DOM comparison)
```
Call: get_metadata(fileKey, nodeId, depth=3)
Extract: Layer names, types, nesting structure
```

### Step 3 — Resolve token names (if design context uses variables)
```
Call: get_variable_defs(fileKey)
Extract: Variable name → resolved hex/px value
```

### Step 4 — Map to SCSS

For each extracted CSS property, look up in the token mapping (if available):

| Figma CSS | Lookup Strategy |
|---|---|
| `background-color: #HEX` | Search hex in Colors tables → find corresponding SCSS variable |
| `font-size: 52px` | Search `52px` in Typography tables → find corresponding placeholder |
| `padding: 80px` | Search `80px` in Spacing tables → find corresponding mixin/token |
| `border-radius: 0` | Confirm 0 matches current radius tokens |
| `box-shadow: 0 1px 2px...` | Match against shadow variables |

### Step 5 — Compare with component SCSS

Read the component's `.scss` file and trace token usage:

```scss
// If component uses:
@extend %heading-h2;
// → Verify Figma shows the typography values for this heading level

// If component uses:
@include component-padding(padding-top, large);
// → Verify Figma shows the expected padding-top value

// If component uses:
background-color: $color-primary-500;
// → Verify Figma shows the corresponding fill colour
```

---

## Common Figma-to-SCSS Discrepancy Patterns

| Pattern | What to look for |
|---|---|
| **Hardcoded hex** | Component SCSS uses a raw hex instead of the corresponding colour variable |
| **Missing responsive** | Figma shows desktop values but component lacks `@include media-breakpoint-up()` |
| **Wrong token level** | Component uses a foundation variable directly instead of the project alias |
| **Pixel vs rem** | Component uses `px` values instead of going through `rem-calc()` or token system |
| **Missing mixin** | Component uses raw `padding` values instead of the spacing mixin |
| **Theme variant mismatch** | Component applies different colour for a theme variant vs Figma frame |
| **Spacer arithmetic** | Component uses `$spacer * N` arithmetic — verify Figma matches the computed value |
