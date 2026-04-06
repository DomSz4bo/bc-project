# Mermaid Sequence Diagram Reference

## Diagram Shell
```
sequenceDiagram
    ... statements ...
```
> ⚠️ The word `end` breaks parsing. Wrap it: `(end)`, `[end]`, `{end}`.

---

## Participants & Actors

```
participant A                          # rectangle (default)
participant A as "Long Display Name"   # with alias
actor B                                # stick figure
actor B as "User"
```

**Stereotypes** (use JSON config syntax):
```
participant A@{"type": "boundary"}    # boundary
participant A@{"type": "control"}     # control
participant A@{"type": "entity"}      # entity
participant A@{"type": "database"}    # cylinder
participant A@{"type": "collections"} # collections
participant A@{"type": "queue"}       # queue
```

**Grouping:**
```
box Aqua Group Label
    participant A
    participant B
end
box rgb(33,66,99)
    participant C
end
box transparent Aqua   # force transparent when name is a color word
    participant D
end
```

**Dynamic creation/destruction:**
```
create participant B
A --> B: Hello
destroy B
A -> B: Goodbye
```
> Only the *recipient* of a message can be created. Sender or recipient can be destroyed.

---

## Arrow Types

| Syntax | Style |
|--------|-------|
| `->` | Solid, no arrowhead |
| `-->` | Dotted, no arrowhead |
| `->>` | Solid, arrowhead |
| `-->>` | Dotted, arrowhead |
| `<<->>` | Solid, bidirectional |
| `<<-->>` | Dotted, bidirectional |
| `-x` | Solid, cross end |
| `--x` | Dotted, cross end |
| `-)` | Solid, async open arrow |
| `--)` | Dotted, async open arrow |

**Message syntax:** `ActorA->>ActorB: Message text`

---

## Activations

Explicit:
```
activate A
A->>B: call
deactivate A
```

Shorthand (preferred):
```
A->>+B: call
B-->>-A: reply
```

Stacked activations (same actor called multiple times):
```
A->>+B: first call
A->>+B: second call
B-->>-A: reply to second
B-->>-A: reply to first
```

---

## Notes
```
Note right of A: Text
Note left of A: Text
Note over A: Text
Note over A,B: Text spanning two actors
```
Line breaks in notes: use `<br/>` inside the text.

---

## Control Flow Blocks

**Loop:**
```
loop Loop condition
    A->>B: message
end
```

**Alt / else (conditional branches):**
```
alt Success case
    A->>B: proceed
else Failure case
    A->>B: handle error
end
```

**Opt (optional, no else):**
```
opt Only sometimes
    A->>B: optional message
end
```

**Parallel:**
```
par Action 1
    A->>B: msg1
and Action 2
    A->>C: msg2
end
```

**Critical (must-happen with contingencies):**
```
critical Acquire lock
    A->>DB: write
option Lock timeout
    A->>Log: record failure
option DB down
    A->>Queue: enqueue
end
```

**Break (exception / early exit):**
```
break Error occurred
    A->>B: abort
end
```

---

## Background Highlighting
```
rect rgb(0, 255, 0)
    A->>B: inside green rect
end
rect rgba(0, 0, 255, 0.1)
    B->>C: inside blue rect
end
```

---

## Sequence Numbers
Add to diagram code:
```
sequenceDiagram
    autonumber
    A->>B: first (gets #1)
    B->>A: second (gets #2)
```

---

## Actor Links (popup menus)
```
link A: Dashboard @ https://example.com/dashboard
link A: Repo @ https://github.com/org/repo
```

---

## Comments
```
%% This is a comment — ignored by parser
```

---

## Escaping Special Characters
Use HTML entity encoding: `#35;` = `#`, `#59;` = `;`
Example: `A->>B: Price #35;100`

---

## Line Breaks in Messages
```
A->>B: Line one<br/>Line two
```
For actor name line breaks, use an alias:
```
participant A as "Line one<br/>Line two"
```

---

## Key Rules & Common Mistakes
- All blocks (`loop`, `alt`, `par`, `critical`, `break`, `rect`, `box`) must close with `end`
- `else` and `and` and `option` are keywords inside blocks — do not use as actor names
- Participant order in diagram = order of first appearance (or explicit declaration order)
- Aliases defined with `as` take precedence over inline config aliases
- `create` must come before the first message to/from that participant
- Nested `par` and `critical` blocks are supported
