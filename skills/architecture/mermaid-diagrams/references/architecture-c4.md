# Architecture diagrams: C4 and architecture-beta

For system architecture. The discipline that makes architecture diagrams useful is
**one zoom level per diagram** — don't mix a 10,000-foot context view with
class-level detail. C4 formalizes those levels.

## C4 levels — one per diagram

1. **Context** — the system as one box, plus the people and external systems it
   talks to. Audience: everyone.
2. **Container** — the deployable/runnable units inside the system (web app, API,
   DB, queue). Audience: technical.
3. **Component** — the major parts inside one container. Audience: developers of
   that container.
4. **Code** — class-level; usually generated, rarely hand-drawn.

Draw the level your reader needs. Most docs want Context or Container.

## C4 in Mermaid

```
C4Context
  title System context — Business School site

  Person(editor, "Content editor", "Manages programmes and news")
  System(site, "BS Website", "Drupal 11 site")
  System_Ext(crm, "Dynamics CRM", "Leads & applications")

  Rel(editor, site, "Authors content")
  Rel(site, crm, "Submits forms", "HTTPS")
```

- `Person` / `System` / `System_Ext` (external) / `Container` / `Component`.
- `Rel(from, to, "label", "technology")` — name the protocol; it's high-value.
- `Boundary(id, "name") { ... }` to group containers within a system boundary.
- C4 support in Mermaid is solid but evolving — verify it renders in the target
  tool; if unsupported, fall back to a `flowchart` styled into C4-like layers.

## architecture-beta (cloud/service topology)

Newer Mermaid type for service/infrastructure topology with grouped resources:

```
architecture-beta
  group api(cloud)[API]
  service db(database)[Postgres] in api
  service server(server)[App] in api
  server:R --> L:db
```

It is **beta** — not all renderers support it. Only use it when you've confirmed
the target (e.g. recent GitHub) renders it; otherwise use a grouped `flowchart`.

## Falling back to flowchart

When C4/architecture-beta aren't supported, a `flowchart` with subgraphs as
boundaries and `classDef` for node categories (internal vs external, by layer)
gives a portable architecture diagram. Apply all the SKILL.md principles: group by
boundary, one edge per group where relationships are uniform, shapes for
datastore vs service vs external, and a legend.

## Pitfalls

- Mixing zoom levels in one diagram → the classic architecture-diagram failure.
  Split into context + container.
- Unlabeled relationships → a box-and-line picture that says little. Name what
  flows and over what protocol.
- Relying on `C4`/`architecture-beta` without checking renderer support → may not
  display. Verify, or fall back to flowchart.
