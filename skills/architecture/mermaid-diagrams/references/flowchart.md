# Flowchart / graph

The workhorse for components, dependencies, decisions, and layered architecture.
Apply the design principles from SKILL.md (dedupe edges, group, encode meaning,
trim labels) — this file is syntax and idioms.

## Declaration and direction

`graph` and `flowchart` are synonyms. Pick direction by meaning: `TB`/`TD`
top-down for hierarchy and dependency; `LR` left-right for pipelines and flow.

```
flowchart LR
  A --> B --> C
```

## Node shapes (use them to mean something — see SKILL.md table)

```
rect["process / component"]
round(["start / end"])
sub[["module / library / package"]]
db[("datastore — ONLY for data")]
dec{"decision?"}
hex{{"preparation"}}
```

Always quote labels with special characters: `n["build (prod)"]`, not
`n[build (prod)]` — the parens break the parser.

## Edges

```
A --> B            solid: primary relationship / flow
A -.-> B           dotted: secondary / optional / cross-cutting
A ==> B            thick: a different kind of relationship (emphasis, other mechanism)
A -->|"label"| B   labelled edge
A --- B            line without arrowhead
```

## Subgraphs (grouping) and the de-hairball pattern

Give the subgraph an **id** so you can draw a single edge from the whole group —
this is how you collapse many identical edges into one.

```
flowchart TB
  subgraph features["Feature modules"]
    direction LR
    a["a"]
    b["b"]
    c["c"]
  end
  base["base"]
  features -->|"depends on"| base   %% one edge = all members depend on base
```

`direction` inside a subgraph needs Mermaid ≥ 9.x (fine on GitHub/GitLab).

## Styling

```
classDef important fill:#bff0c8,stroke:#1a7f37,color:#000
class base,core important          %% apply a class to nodes
style features fill:#eef6ff,stroke:#1f6feb,color:#000   %% style a subgraph by id
linkStyle 0,1 stroke:#b25e00,stroke-width:2px           %% style edges by index
```

Use mid-tone fills + explicit `color:#000` so the diagram is legible in both light
and dark renderers. Make color redundant with grouping/shape/label, never the only
signal.

## Common pitfalls

- Unquoted special characters in labels (`()`, `#`, `:`, `;`, `&`) → parse error.
  Quote the label.
- One arrow per node into a shared target → hairball. Group and draw one edge.
- Cylinder shape for a non-database thing → misleads. Use `[[...]]` for modules.
- Cramming a field list into a node → bloated boxes. Put detail in prose/tables.
- Manual node ordering to force layout → fragile. Choose the right `direction`
  instead.
- `end` as a bare node id → reserved word, breaks the graph. Quote or rename.
