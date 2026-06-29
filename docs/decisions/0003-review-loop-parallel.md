---
id: 0003-review-loop-parallel
type: decision
status: accepted
parent: architecture
children: []
related: []
supersedes: none
---

# 0003-review-loop-parallel: Review loop = 2 parallel reviewers, finish on one clean round

## Context
`/tai-review` runs blind subagent reviewers (no prior-findings bias). The original loop
used **K=2 sequential** clean rounds: review → fix → review → fix … until two consecutive
rounds find nothing CRITICAL/HIGH. In practice (this session's dashboard work) that ran
3–5 sequential rounds per change — correct but slow, because each confirming round waits
for the previous to finish.

The blind-reviewer rule (each reviewer gets only the current diff + specs, never prior
findings) is sound and is kept regardless.

## Decision
Change the loop to **two blind reviewers per round, run in parallel**, and **finish on the
first round where BOTH come back with nothing CRITICAL/HIGH** (one clean round, K=1).
- Each round: spawn 2 fresh blind reviewers concurrently, given complementary angles where
  useful (e.g. security/XSS vs correctness/regressions).
- Clean = both reviewers report no CRITICAL/HIGH → DONE.
- Any CRITICAL/HIGH from either → fix, commit, run another parallel round.
- Round cap 4; LOW/INFO nits → `backlog.md`, never block.

## Consequences
- **Faster:** two independent eyes per round in parallel replaces a sequential second
  confirming round — same regression-catching coverage (two cold reads of the final state),
  less wall-clock.
- **Cost:** 2 reviewer subagents every round (more tokens per round) — acceptable for the
  speed and the dual-perspective coverage.
- Supersedes the K=2 sequential rule in `review/SKILL.md`.

## Alternatives considered
- Keep K=2 sequential — rejected: slower for equivalent assurance.
- Single reviewer, one round — rejected: loses the second independent perspective that
  catches blind spots + fix-introduced regressions.
