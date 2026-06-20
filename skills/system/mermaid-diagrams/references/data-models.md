# Data models: ER, class, state

Three related types for modeling data and behavior. Pick by what you're showing:
ER for persistent data and cardinality, class for OO structure, state for
lifecycle.

## Entity-relationship (ER)

For database schemas and domain models. Its strength over a generic graph is
**cardinality** — it shows one-to-many, many-to-many precisely.

```
erDiagram
  CUSTOMER ||--o{ ORDER : places
  ORDER ||--|{ LINE_ITEM : contains
  PRODUCT ||--o{ LINE_ITEM : "ordered in"

  CUSTOMER {
    int id PK
    string email
  }
  ORDER {
    int id PK
    int customer_id FK
    datetime created_at
  }
```

Cardinality notation (left + right of `--`):

```
|o  zero or one        ||  exactly one
}o  zero or many       }|  one or many
```

So `||--o{` = one-to-(zero-or-many). Label every relationship with a verb.

## Class diagram

For object-oriented structure: classes, attributes, methods, inheritance.

```
classDiagram
  class Repository~T~ {
    <<interface>>
    +find(id) T
    +save(entity) void
  }
  class NodeRepository {
    +find(id) Node
  }
  Repository <|.. NodeRepository : implements
  NodeRepository --> Node : manages
```

Relationships:

```
<|--  inheritance        *--  composition
<|..  realization        o--  aggregation
-->   association        ..>  dependency
```

Visibility: `+` public, `-` private, `#` protected. `<<interface>>` /
`<<abstract>>` stereotypes. `~T~` for generics.

## State diagram

For lifecycle and status machines: order status, request lifecycle, workflow.

```
stateDiagram-v2
  [*] --> Draft
  Draft --> Review : submit
  Review --> Published : approve
  Review --> Draft : request changes
  Published --> [*]

  state Review {
    [*] --> Pending
    Pending --> Voting
  }
```

- `[*]` is the start/end pseudo-state.
- Nest states for composite/sub-states.
- Label transitions with the triggering event.
- `note right of State: ...` for annotations.

## Pitfalls

- ER without cardinality or without relationship verbs → just boxes; the value is
  the relationship semantics, so include them.
- Class diagrams that dump every getter/setter → noise. Show the methods that
  matter to the reader's question.
- State diagrams that are really sequential steps → a list or flowchart is
  clearer. Use state diagrams when there are real transitions, branches, or
  cycles between named states.
