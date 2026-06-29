# Comparison Matrix Template

## {Candidate A} vs {Candidate B} [vs {Candidate C}...]

**Use case:** {what you're building and what matters most}

### Overview

| Dimension | {Candidate A} | {Candidate B} | Winner |
|-----------|--------------|--------------|--------|
| Maturity | {age, stability, semver status} | | |
| Performance | {benchmarks with numbers} | | |
| Ecosystem | {plugins, integrations, community size} | | |
| Maintenance | {commit freq, open issues, bus factor} | | |
| Learning curve | {docs quality, examples, complexity} | | |
| License | {license type, commercial implications} | | |
| Production adoption | {who uses it, at what scale} | | |
| Trajectory | {growing/stable/declining, based on trends} | | |

### Head-to-Head

#### Performance
{Real benchmark data with source citations. "X handles N req/s vs Y's M req/s [Source, Date]"}

#### Developer Experience
{API design, documentation, error messages, debugging tools}

#### Ecosystem & Community
{Package count, GitHub stars trend, Stack Overflow activity, corporate backing}

#### Maintenance Health
{Last release date, open issue count, PR merge time, bus factor, funding model}

#### Migration & Lock-in Risk
{How hard to switch away, proprietary APIs, data portability}

#### Second-Order Effects
{Hiring pool, long-term ecosystem trajectory, upgrade path pain, community culture}

### Adversarial Red Team

#### Case against the winner

**Steel-man for {Runner-up}:** {The strongest possible argument for choosing the runner-up instead. What would a passionate advocate say?}

**Worst known incident with {Winner}:** {Real production failure, critical bug, or community controversy. Source it.}

**When {Winner} is the wrong choice:** {Specific scenario where the recommendation flips.}

**Hidden costs:** {Operational burden, learning curve gotchas, migration pain that's easy to underweight.}

#### Confidence calibration

```
RECOMMENDATION CONFIDENCE: {High/Medium/Low}
Reason: {what the red team found and why it does/doesn't change the recommendation}
```

### Recommendation

**Use {Winner}** for this use case because {one-line reason}.

**Choose {Runner-up} instead if:** {specific conditions where the other choice wins}.

### Sources
1. {URL} — {brief description} [{Date}] [Type: Official/Benchmark/Community/Case Study]
