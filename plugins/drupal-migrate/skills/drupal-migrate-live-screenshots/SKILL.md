---
name: drupal-migrate-live-screenshots
description: "Take browser screenshots of live example pages resolved by drupal-migrate-resolve-examples. Optional step — run only when the user confirms or the invocation explicitly requests screenshots. Browser-tool-agnostic — uses the playwright-cli skill if enabled, else a Playwright (or other browser) MCP server, else asks the user which browser tool to use."
---

# Live screenshots of example pages

Take browser screenshots of the live example URLs produced by
`drupal-migrate-resolve-examples`. This is an **optional step** — run it only when the
user has confirmed it, or when the invocation prompt explicitly asks for screenshots
(the non-interactive `drupal-migration-analyst` agent passes that request through and
cannot ask mid-run).

The skill does not hardcode a browser engine. It selects whatever browser tool the
environment actually has, in a fixed preference order, and asks the user if none is
detected.

---

## Prerequisites

- `drupal-migrate-resolve-examples` has run and produced at least one URL.
- A browser tool is available — resolved in "Selecting the browser tool" below.

## Selecting the browser tool

Pick the first available, in this order, and use it for every screenshot in the run:

1. **`playwright-cli` skill** — if it is in the available skills list, use it. It is the
   preferred tool: invoke it to navigate and capture full-page screenshots.
2. **Playwright MCP server** — if a Playwright MCP is connected (search the available MCP
   tools for a `playwright`-named navigate/screenshot tool), use it.
3. **Another browser MCP server** — e.g. `chrome-devtools`. If present, use its
   navigate + screenshot tools.
4. **None detected** — do not guess or invent a mechanism. Ask the user:

   > "I need a browser tool to capture screenshots and don't see one enabled. Which
   > should I use — the `playwright-cli` skill, a Playwright MCP, or another browser MCP?
   > Enable it (or name the tool) and I'll proceed; otherwise I'll skip screenshots and
   > keep only the field analysis."

   Wait for the answer; do not fall back to an arbitrary tool.

Record which tool was selected and report it in the result.

---

## Inputs

- The **Live examples table** produced by `drupal-migrate-resolve-examples` (node type,
  node ID, URL).
- Source bundle name (used for screenshot filename generation).
- _(optional)_ A save directory from the invocation; otherwise default to the analysis
  save location (the same place the analysis report is written), e.g.
  `doc/Migrate/as-is/data/screenshots/`. Create it if needed.

---

## Steps

### 1. Confirm the request (mandatory gate)

The gate is satisfied in either of two ways:

- **Invocation requests it.** The prompt that started this run explicitly asks for
  screenshots (e.g. "screenshots: yes", "take live screenshots"). Proceed without asking;
  note "screenshots requested in the invocation" in the result.
- **Interactive run without an explicit request.** Ask:

  > "Should I take live screenshots of the example pages? This drives a browser and may
  > take some time. You can skip this step if you only need the field analysis."

  Proceed only if the user answers **yes**.

In a non-interactive run (subagent) with no explicit request, skip screenshots and say
so — never block the analysis waiting for an answer.

### 2. Select the browser tool

Resolve the tool per "Selecting the browser tool". If none is available and the user
does not name one, skip screenshots and say so — do not block the analysis.

### 3. Take screenshots

For each URL in the Live examples table, using the selected tool:

1. Navigate to the URL.
2. Wait for the page to fully load (network idle or a reasonable timeout).
3. Capture a full-page screenshot.
4. Save it to the resolved save directory.
5. Filename pattern: `screenshot-{bundle}-{node_bundle}-{nid}.png`
   - `{bundle}` = the bundle being analysed; `{node_bundle}` = the parent node type whose
     page is rendered; `{nid}` = the parent node ID.
   - Example (a paragraph embedded in an `article` node, nid 42):
     `screenshot-<bundle>-article-42.png`

### 4. Update the Live examples table

Add the `Screenshot` column to the existing table:

| Node type | Node ID | URL                            | Screenshot                           |
| --------- | ------- | ------------------------------ | ------------------------------------ |
| `article` | 42      | `https://www.example.com/path` | `screenshot-<bundle>-article-42.png` |

For pages that failed to load, note the reason in the Screenshot column instead of a
filename (e.g., `404 Not Found`, `Timeout`).

---

## Error Handling

- **No browser tool available**: ask the user which to use (see step 2). If none is
  provided, skip screenshots and continue with the field analysis — do not invent a
  mechanism.
- **Page returns 4xx/5xx**: note the HTTP status in the Screenshot column. Do not retry.
- **Page times out**: note `Timeout` in the Screenshot column. Continue with remaining
  URLs.
- **URL is `URL not found`**: skip — no screenshot possible.

## Guardrails

- **Optional and gated** — never run without the step-1 gate (user confirmation or an
  explicit request in the invocation); never block the field analysis on screenshots.
- **Browser-tool-agnostic** — select by availability in the fixed order; never hardcode a
  single engine, and ask the user when none is detected.
- **Read-only navigation** — navigate and capture only; never submit forms or trigger
  writes on the live site.
