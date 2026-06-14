# Domain Language for Agents

Use this file to keep product and engineering language consistent. Update it when a term becomes important to implementation, tests, issue titles, or PR descriptions.

## Glossary

| Term | Meaning | Avoid saying | Notes |
|---|---|---|---|
| `<CanonicalTerm>` | `<Definition>` | `<Ambiguous synonyms>` | `<Examples>` |

## Bounded contexts

| Context | Owns | Does not own | Main directories |
|---|---|---|---|
| `<ContextName>` | `<Domain responsibilities>` | `<Out of scope>` | `<paths>` |

## Cross-context relationships

- `<ContextA> -> <ContextB>`: `<event/API/shared model>`

## Decision log pointers

ADRs live in `docs/adr/`. Use short ADRs. Record only decisions that future agents and engineers must remember.
