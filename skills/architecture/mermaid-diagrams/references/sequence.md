# Sequence diagram

For actors/services exchanging messages over time: API calls, auth flows,
protocols, event chains. A sequence diagram reads message order far better than a
flowchart of arrows, so prefer it whenever "who calls whom, in what order" is the
point.

## Core syntax

```
sequenceDiagram
  autonumber
  participant U as User
  participant API as API Gateway
  participant DB as Database

  U->>API: POST /login
  API->>DB: lookup user
  DB-->>API: row
  API-->>U: 200 + token
```

- Declare participants up front with `as` aliases to keep messages short and
  control left-to-right order.
- `autonumber` numbers the messages — helps the prose reference steps ("step 3").

## Arrows (each means something)

```
->>   solid arrowhead: synchronous call / request
-->>  dashed arrowhead: response / return
-)    open arrowhead: async / fire-and-forget message
-x    cross: a lost or failed message
```

## Grouping and control flow

```
alt success / failure        %% mutually exclusive branches
  API-->>U: 200
else error
  API-->>U: 401
end

opt cache hit                 %% optional block
  API-->>U: cached
end

loop every 30s                %% repetition
  Worker->>Queue: poll
end

par fan-out                   %% concurrent messages
  API->>SvcA: call
and
  API->>SvcB: call
end
```

## Readability idioms

- Use `Note over A,B: ...` to annotate, not extra messages.
- `activate`/`deactivate` (or `->>+` / `-->>-`) show lifelines/processing spans;
  use them when "who is busy" matters, skip them when they just add noise.
- Keep participant count low. More than ~6 lifelines gets hard to follow — split
  into multiple diagrams by phase.
- Order participants by first interaction to minimize crossing arrows.

## Pitfalls

- Too many participants → unreadable. Split by phase or subsystem.
- Using a flowchart for what is really a message exchange → loses ordering and
  request/response semantics. Use a sequence diagram.
- Long message text → wraps badly. Keep messages terse; put detail in prose.
