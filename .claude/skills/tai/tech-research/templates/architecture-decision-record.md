# Architecture Decision Record

## ADR-{NNN}: {Decision Title}

**Status:** Proposed
**Date:** {YYYY-MM-DD}
**Deciders:** {who is making this decision}

### Context

{What is the problem or situation that requires a decision? What forces are at play?
Include constraints: timeline, team expertise, existing infrastructure, budget.}

### Decision Drivers

- {driver 1 — e.g., "Must handle 10k concurrent connections"}
- {driver 2 — e.g., "Team has no experience with Kafka"}
- {driver 3}

### Options Considered

#### Option A: {Name}

{Brief description of the approach.}

| Dimension | Assessment |
|-----------|-----------|
| Effort | {S/M/L — implementation time} |
| Operational complexity | {Low/Med/High — what it takes to run in prod} |
| Performance | {expected characteristics with numbers if available} |
| Scalability | {how it handles 10x/100x growth} |
| Team familiarity | {Low/Med/High} |
| Reversibility | {Easy/Hard — cost of switching away} |

**Pros:**
- {pro 1}

**Cons:**
- {con 1}

**Real-world evidence:** {case study, post-mortem, or production example with source}

#### Option B: {Name}

{Same structure as Option A}

### Decision

**We will use {Option X}** because {primary reason}.

### Consequences

**Positive:**
- {consequence 1}

**Negative:**
- {consequence 1}

### Revisit Triggers

Revisit this decision if:
- {condition 1 — e.g., "write volume exceeds 50k/sec"}
- {condition 2}

### Sources
1. {URL} — {brief description} [{Date}]
