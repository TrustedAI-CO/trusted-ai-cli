---
id: SPEC-{area}-{name}
type: spec
status: draft            # draft → approved (human gate) → implemented
approved_at:             # ISO timestamp, set when human flips to approved (provenance)
implements: [prd]
parent: architecture
children: []
related: []
code: {dir or file under an architecture.md §4 container}
tests: {dir or file}
---

# {Surface Name} — Spec

> One spec = one public surface. Change the spec before the code, same PR. Precedence:
> Invariants > Interface > Behavior.

## Overview
What this surface does and its boundary.

## Invariants
- INV1: {property that must always hold}

## Interface
API contracts / CLI signatures / data models / events.

## Behavior

| ID | Given | When | Then |
|----|-------|------|------|
| R1 | {precondition} | {action, concrete values} | {observable result} |

## Acceptance
- [ ] Each Behavior row ID referenced by a passing test (`test_R1_*` or `# covers: SPEC-... R1`).
- [ ] Each Invariant has a property/assertion test.
- [ ] `code:`/`tests:` paths exist; `code:` sits under an architecture.md §4 container.

## Open questions
- ...
