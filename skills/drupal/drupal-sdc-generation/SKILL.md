---
name: drupal-sdc-generation
description: >
  Generate Single Directory Components (SDC) for a Drupal 11 theme following
  project conventions. Produces .component.yml, .twig, .scss, README.md, and
  optionally a Drupal paragraph template. When the component maps a Drupal
  paragraph, this skill invokes drupal-paragraph-generation for the config
  YAML files. Use when the user says "create SDC", "generate component",
  "new SDC", "scaffold component", "create SDC for paragraph", or provides
  a component name to build (e.g., "create an SDC called card", "generate
  the feature-box component").
---

# SDC Generation

Generate well-structured, accessible, and maintainable Single Directory
Components (SDC) for Drupal 11 following the project's strict conventions
and best practices.

Reference the main project instructions: `AGENTS.md` and `.agents/AGENTS.project.md`.

## Component Name

If the component name is not explicitly provided in the user's prompt,
**always ask the user** before proceeding. Never infer or guess the name
from context.

## Before You Start — Load Project Conventions

**MANDATORY**: Before generating any file, locate and read the project
conventions file. Search for it in this order:

1. `<theme>/docs/project-conventions.md`
2. `docs/project-conventions.md`

If the conventions file **does not exist**, tell the user:
> "No project conventions file found. Run the `drupal-theme-setup` skill
> first to generate one, or provide the following information: component
> prefix, theme namespace, theme path, SCSS import path."

All placeholder values below (marked with `{CONVENTION:*}`) must be replaced
with values from the conventions file.

Also check for a Figma token mapping file at `<theme>/docs/figma-token-mapping.md`.
If it exists, use it for Figma → SCSS token resolution.

---

## Core Principles

1. **Naming Convention**:
   - All SDCs use kebab-case with `{CONVENTION:prefix}` prefix
   - **When mapping a Drupal paragraph**: Use `{CONVENTION:paragraph_prefix}[NAME]` format
   - For utility/generic components: Use `{CONVENTION:prefix}[NAME]` format
2. **Language**: ALL code comments, documentation, and props MUST be in English
3. **BEM Methodology**: Use `.{CONVENTION:prefix}component`, `.{CONVENTION:prefix}component__element`, `.{CONVENTION:prefix}component--modifier`
4. **Accessibility First**: WCAG compliance is mandatory
5. **Mobile First**: Always responsive design

## Required Files Structure

Each SDC in `{CONVENTION:sdc_path}` must include:

```
{CONVENTION:prefix}{component-name}/
├── {CONVENTION:prefix}{component-name}.component.yml
├── {CONVENTION:prefix}{component-name}.twig
├── {CONVENTION:prefix}{component-name}.scss
└── README.md
```

---

## 1. Component Schema (.component.yml)

### Template Structure
```yaml
'$schema': 'https://git.drupalcode.org/project/drupal/-/raw/10.1.x/core/modules/sdc/src/metadata.schema.json'
name: "Component Human Name"
status: "stable"
slots:
  {prefix}component_name_slot_name:
    title: 'Slot Title'
    description: 'Optional slot description'
props:
  type: object
  properties:
    {prefix}component_name_attributes:
      type: ['object', 'array', 'string', 'null']
      title: attributes
      description: 'Additional HTML attributes for the component wrapper.'
      examples:
        - class: ['{prefix}component-name', '{prefix}component-name--variant']
          id: 'component-id'
    # ... other props
```

### Naming Rules (from conventions file)
- **Props**: `snake_case` prefixed with `{CONVENTION:prop_prefix}` (e.g., `{CONVENTION:prop_prefix}heading_title`)
- **Slots**: `snake_case` prefixed with component name, suffixed with `{CONVENTION:slot_suffix}`
- **MANDATORY**: Every component MUST have `{component}_attributes` property for extensibility

### Type Definitions
- Always allow `null` type: `type: ['string', 'null']`, `type: ['object', 'null']`
- Usually add a slot for media elements (images, videos) if needed
- If the SDC should have a heading paragraph, add a slot for that too

### Slider/Carousel Components
When creating a slider component, include dependencies from the conventions file (`{CONVENTION:slider_dependencies}`). Add props for navigation controls as documented in the conventions.

### Common Prop Patterns

#### Text Property
```yaml
{prefix}component_text:
  type: ['string', 'null']
  title: 'Text content'
  description: 'The text to display'
  examples:
    - 'Sample text'
```

#### Enum Property
```yaml
{prefix}component_variant:
  type: ['string', 'null']
  title: 'Visual variant'
  description: 'Choose the visual style of the component'
  enum:
    - 'default'
    - 'highlighted'
    - 'minimal'
  examples:
    - 'default'
```

#### Link Property
```yaml
{prefix}component_link:
  type: ['object', 'array', 'null']
  title: 'Link object'
  description: 'Link with URL, title, and external flag'
  properties:
    url:
      type: ['string', 'null']
      title: 'Link URL'
      examples:
        - '/about'
        - 'https://example.com'
    title:
      type: ['string', 'null']
      title: 'Link Title'
      examples:
        - 'Learn more'
    external:
      type: ['boolean', 'null']
      title: 'External Link'
      default: false
```

**IMPORTANT**: When a component includes link properties or renders clickable
elements, you MUST also add a standalone `data_tracking` property for analytics:

```yaml
{prefix}component_data_tracking:
  type: ['string', 'null']
  title: 'Data tracking'
  description: 'Optional data-tracking attribute for analytics integration'
```

This property should be a **separate, standalone property** (not nested inside
link objects), named `{component}_data_tracking`, used as
`data-tracking="{{ {prefix}component_data_tracking }}"` on the clickable element.

#### Boolean Property
```yaml
{prefix}component_flag:
  type: ['boolean', 'null']
  title: 'Flag name'
  description: 'Whether to enable feature'
  default: false
  examples:
    - true
    - false
```

---

## 2. Template File (.twig)

### Template Structure

Start twig templates with file header comment and `create_attribute` setup:

````twig
{%- set {prefix}component_attributes = {prefix}component_attributes ?? create_attribute() -%}

<div{{ {prefix}component_attributes.addClass('{prefix}component-name') }}>
  {% if {prefix}component_title %}
    <h2 class="{prefix}component-name__title">{{ {prefix}component_title }}</h2>
  {% endif %}

  {% block {prefix}component_content_slot %}
  {% endblock {prefix}component_content_slot %}
</div>
````

Note: Always include proper Twig file header comment with `@file` documentation
at the top.

### Best Practices
- **Always** use `create_attribute()` for the main attributes variable
- **Conditional rendering for props**: Check prop existence before rendering
  (use `{% if variable %}`, NOT `{% if variable is defined %}`)
- **CRITICAL — Slots rendering**: NEVER use `{% if %}` conditionals on slots
  in SDC templates — slots are always defined and the check doesn't work
  correctly. Render slots directly with `{% block slot_name %}{% endblock %}`
  without any conditional wrapper
- **BEM classes**: Use `__element` for child elements, `--modifier` for variants
- **Icons**: Use the icon system documented in the conventions file (`{CONVENTION:icon_api}`)
- **Accessibility**: Include ARIA labels, roles, and semantic HTML

### Common Patterns

#### Conditional Class Modifiers
````twig
{%- set classes = [
  '{prefix}component',
  {prefix}component_variant ? '{prefix}component--' ~ {prefix}component_variant : null,
  {prefix}component_size ? '{prefix}component--size-' ~ {prefix}component_size : null,
] -%}

<div{{ {prefix}component_attributes.addClass(classes) }}>
````

#### Link Rendering
````twig
{% if {prefix}component_link %}
  <a href="{{ {prefix}component_link.url }}"
     class="{prefix}component__link"
     {% if {prefix}component_link.external %}target="_blank" rel="noopener noreferrer"{% endif %}>
    {{ {prefix}component_link.title }}
  </a>
{% endif %}
````

---

## 3. Styles File (.scss)

### Template Structure (no Figma URL)
```scss
/**
 * @file
 * Style for Component Name.
 */

{CONVENTION:scss_import}

.{prefix}component-name {
  // Component wrapper styles

  &__element {
    // Element styles
  }

  &--modifier {
    // Modifier styles
  }
}
```

### Template Structure (with Figma tokens)

When design tokens were extracted from Figma, write the SCSS file using the
resolved SCSS variables, placeholders and mixins **directly** inside the BEM
selectors — do NOT create intermediate maps. Each Figma value must be
translated to its SCSS equivalent via the token mapping file before writing
any line of SCSS.

**Token resolution rules**: Read the token resolution table from
`{CONVENTION:token_mapping_path}`. Apply the documented mappings for
colors → `$color-*`, typography → `@extend %placeholder`,
spacing → `@include mixin()`, shadows → `$shadow-*`,
border-radius → `@extend %border-radius-*`.

### SCSS Guidelines
- **ALWAYS** import dependencies: `{CONVENTION:scss_import}`
- **If no Figma URL**: Leave all selectors empty with only the BEM structure
  (class names, no properties)
- **If Figma tokens extracted**: Write properties directly in the correct BEM
  selectors using resolved variables/placeholders/mixins — no hardcoded
  hex/px values, no intermediate maps
- **Colors**: always project color variables, never hex literals
- **Typography**: always `@extend %placeholder`, never raw
  `font-size`/`font-weight` values
- **Spacing**: always spacing mixins, never raw px/rem values when a mixin exists
- **Mobile-first**: Base styles, then use `@include media-breakpoint-up(md) { }`
- **Never add** a Figma URL reference or token resolution table in the
  `@file` docblock
- **Never add** inline comments explaining token mapping on CSS properties

### Common Patterns

#### Spacing with Bootstrap
```scss
.{prefix}component {
  padding: $spacer * 2;
  margin-bottom: $spacer * 3;
  gap: $spacer;

  @include media-breakpoint-up(md) {
    padding: $spacer * 4;
  }
}
```

#### Flexbox Grid
```scss
.{prefix}component {
  display: flex;
  flex-direction: column;
  gap: $spacer;

  @include media-breakpoint-up(lg) {
    flex-direction: row;
    gap: $spacer * 2;
  }
}
```

---

## 4. Documentation (README.md)

### Template Structure
```markdown
# Component Name

Brief description of what this component does and when to use it.

## Usage

Basic example:
\```twig
{{ include('{CONVENTION:namespace}:{prefix}component-name', {
  '{prefix}component_title': 'Sample Title',
  '{prefix}component_text': 'Sample text content'
}) }}
\```

Advanced example with slot:
\```twig
{% embed '{CONVENTION:namespace}:{prefix}component-name' with {
  '{prefix}component_title': 'Sample Title',
} %}
  {% block {prefix}component_content_slot %}
    <p>Custom content here</p>
  {% endblock %}
{% endembed %}
\```

## Props

- **{prefix}component_title** (string|null): The title
- **{prefix}component_attributes** (object|array|string|null): Additional HTML attributes

## Slots

- **{prefix}component_content_slot**: Main content area

## Dependencies

- List other SDCs, libraries, or systems used

## Accessibility

- Semantic HTML5 elements
- ARIA labels for interactive elements
- Keyboard navigation support
- Color contrast compliance (WCAG AA)
```

### Documentation Rules
- **Always in English** — no exceptions
- **Include realistic examples** — show common use cases
- **Document all props and slots** — with types and descriptions
- **List dependencies** — other SDCs, libraries, or systems used
- **Accessibility notes** — WCAG compliance features
- **Never mention Figma** — no URLs, node IDs, token names, or design references

---

## Prerequisites

- **Figma MCP server** (`com.figma.mcp/mcp`) should be active and authenticated
  to extract design tokens from Figma.
- Figma URL is **optional but strongly recommended**: if provided, SCSS token
  maps will be populated with real design values instead of being left empty.
- **Token mapping reference**: `{CONVENTION:token_mapping_path}` — always read
  this to resolve Figma variables → SCSS variables.

---

## Generation Workflow

When generating the SDC component:

1. **Analyze Requirements**
   - **MANDATORY — Component name**: If the SDC name was not explicitly stated,
     ask for it. Never infer it.
   - Component purpose and usage context
   - Required props (text, images, links, flags)
   - Ask if user needs a heading paragraph
   - Ask if user needs media slot (image, video)
   - Determine if slots are needed for flexible content
   - **MANDATORY — Drupal entity mapping**: Ask the user whether this SDC
     should map a Drupal entity (paragraph, taxonomy term, node, etc.).
     **Never search `src/drupal/config/sync` autonomously**. If the user
     confirms a mapping, ask them for the exact entity type machine name and
     the list of fields. If no mapping info is provided, generate only the
     SDC files.
   - **Ask for a Figma URL** (optional): "Do you have a Figma frame URL for
     this component? If so, I'll extract the design tokens and populate the SCSS."
   - **MANDATORY — Props/fields discovery**:
     - If the user has **not** explicitly listed the props:
       - **If a Figma URL was provided**: call `get_design_context` first,
         infer the list of props from the design, then **present the proposed
         prop list to the user and ask for confirmation before proceeding**.
       - **If no Figma URL was provided**: ask the user to list the props.
         Do not proceed until at least a minimal list is provided.
   - **MANDATORY — Variants discovery**: Ask the user whether the component
     has visual variants. If yes, ask for the Figma URL(s) for each variant.
   - **If component is a slider/carousel**: Ask which navigation elements
     are needed.

1b. **Extract Figma Design Tokens** *(only if a Figma URL was provided)*

   Parse the URL to extract `fileKey` and `nodeId` (replace `-` with `:` in
   node IDs).

   Then:
   1. Call `get_design_context` with `fileKey` + `nodeId` — extract all colors,
      typography, spacing, border-radius, and shadow values
   2. Call `get_variable_defs` with `fileKey` — resolve Figma variable names
      to hex/value
   3. Read `{CONVENTION:token_mapping_path}` to translate each extracted Figma
      value → SCSS variable
   4. Build a working table:

   ```
   | Element        | CSS Property     | Figma Value | SCSS Token             |
   |----------------|------------------|-------------|------------------------|
   | wrapper        | background-color | #003a70     | $color-primary-500     |
   | __title        | font-size        | 36px        | %heading-h2            |
   ```

   5. Group the resolved tokens by **component variant** (if applicable).

2. **Generate Schema (.component.yml)**
   - Include mandatory `_attributes` property
   - Define all props with proper types (always include `null`)
   - Add slots if content needs to be injectable
   - Provide meaningful examples for each prop

3. **Create Template (.twig)**
   - Start with file header comment (in English)
   - Set up `create_attribute()` for main wrapper
   - Build semantic HTML structure with BEM classes
   - Add conditional rendering for optional props
   - Include accessibility attributes (ARIA, roles)

4. **Write Styles (.scss)**
   - Import dependencies as first line
   - Mobile-first approach (base → breakpoints)
   - Follow BEM naming in selectors
   - **When NO Figma URL was provided**: Create only the BEM structure with
     empty selectors — NO actual CSS rules
   - **When Figma tokens WERE extracted**: Write CSS properties directly using
     resolved SCSS variables. Never hardcode hex/px/font values.
   - **Never add** Figma references or token mapping comments in the file

5. **Document (README.md)**
   - Clear description and use cases
   - Multiple practical examples (basic + advanced)
   - Complete props/slots reference with types
   - List any dependencies
   - **Never mention Figma**

6. **Generate Drupal Paragraph Template (if mapping a paragraph)**
   - Create the paragraph template in `{CONVENTION:templates_path}paragraph/`
   - File naming: `paragraph--[paragraph-machine-name].html.twig`
   - Template structure:
     - Include full Drupal paragraph header comment
     - Map all paragraph fields to SDC props
     - Use `{% embed %}` syntax with slots for complex content
     - Handle multi-value fields with loops
     - Access field values using the patterns from the conventions file
       (`{CONVENTION:field_access_patterns}`)
     - Check field existence before rendering

   Common mapping patterns:
   ```twig
   {# Single text field #}
   {prefix}component_title: content.field_title.0['#context'].value

   {# List field (select) #}
   {prefix}component_variant: content.field_variant.0['#markup'] ?: 'default'

   {# Boolean check #}
   {prefix}component_has_image: content.field_image.0 is not empty

   {# Multiple links #}
   {% set links = [] %}
   {% if content.field_links['#items'] %}
     {% for key, item in content.field_links if key matches '/^\\d+$/' %}
       {% set links = links|merge([{
         url: item['#url_title'],
         title: item['#title'],
         external: item['#url'].external ?? false,
       }]) %}
     {% endfor %}
   {% endif %}

   {# Slot for paragraph reference — NO if wrapper, check inside block #}
   {% block {prefix}component_heading_slot %}
     {% if content.field_heading.0 is not empty %}
       {{ content.field_heading.0 }}
     {% endif %}
   {% endblock %}

   {# Slot for media reference — NO if wrapper, check inside block #}
   {% block {prefix}component_image_slot %}
     {% if content.field_image.0 is not empty %}
       {{ content.field_image.0 }}
     {% endif %}
   {% endblock %}
   ```

7. **Verify Conventions**
   - [ ] All files use project prefix
   - [ ] Props use project prop prefix (snake_case)
   - [ ] Slots use project slot suffix
   - [ ] BEM classes follow project pattern
   - [ ] SCSS imports dependencies
   - [ ] All comments/docs in English
   - [ ] `_attributes` property exists
   - [ ] README includes usage examples
   - [ ] If slider: includes project slider dependencies
   - [ ] **If paragraph mapping**: Drupal paragraph template created
   - [ ] **If Figma URL provided**: SCSS uses resolved tokens — no hardcoded values
   - [ ] **If no Figma URL**: SCSS selectors are all empty

8. **Build and Test**
   Run the project's cache clear and theme build commands from the conventions
   file (`{CONVENTION:build_commands}`).

---

## Composition

### When mapping a Drupal paragraph

After generating the SDC files and paragraph template (steps 1-8), if the user
confirmed that this SDC maps a Drupal paragraph entity, invoke the
`drupal-paragraph-generation` skill to create the Drupal configuration YAML
files (paragraph type, field storage, field instances, form/view displays,
language settings).

Pass to the skill:
- The paragraph **machine name** (derived from the SDC name)
- The **list of fields** (from the props/slots gathered in step 1)
- The **content type** to attach the paragraph to

> "The SDC files are ready. Now let's generate the Drupal paragraph
> configuration. Invoking the `drupal-paragraph-generation` skill."

### When verifying against Figma

After building the component, if a Figma URL was used, suggest:
> "Want to verify the component matches the Figma design? Use the
> `drupal-sdc-figma-verify` skill with the same Figma URL."

---

## Common Mistakes to Avoid

1. **Missing `_attributes` property** — Every component needs it for extensibility
2. **Forgetting `null` type** — All props should accept null: `type: ['string', 'null']`
3. **Adding CSS rules without Figma tokens** — If no Figma URL was provided, NEVER add actual styles, only empty BEM structure
4. **Hardcoded hex/px/font values in SCSS** — Always resolve via token mapping file
5. **Creating intermediate SCSS maps** — Write properties directly in BEM selectors
6. **Adding Figma references to `@file` docblock** — The file comment must only describe the component
7. **Annotating CSS properties with token comments** — Write the rule directly, without explanation
8. **Mentioning Figma in README** — README is implementation documentation only
9. **Missing SCSS import** — Always import dependencies
10. **Italian comments** — Everything must be in English
11. **Direct icon SVG** — Use the project's icon system
12. **Missing BEM prefix** — All classes must start with project prefix
13. **Non-semantic HTML** — Use proper HTML5 elements
14. **Forgetting accessibility** — Add ARIA labels, alt text, semantic roles
15. **Incomplete README** — Must include props, slots, examples, dependencies
16. **Forgetting paragraph template** — When mapping a paragraph, always create the Drupal template
17. **Wrong field access in paragraph templates** — Use patterns from conventions file
18. **Not handling multi-value fields** — Use loops with regex check
19. **Adding BEM classes in Drupal templates** — **NEVER add BEM classes inside Drupal field/node/paragraph templates** (`.html.twig` files in `templates/`). BEM classes belong **exclusively** to SDC twig files (`components/`). If a grid layout needs a transparent wrapper per-item (e.g., to let Bootstrap col gutters show through a card background), add an `__inner` wrapper **inside the SDC** and move the background/styling there. The SDC root element stays transparent so the col padding is visible.
