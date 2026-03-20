---
title: Partnership Proposal
subtitle: AI Safety Collaboration
author: Thien Nguyen
date: March 19, 2026
---

# Background

TrustedAI has been building developer tools that integrate safety checks
directly into the software development lifecycle. We believe combining
our practical engineering experience with research expertise could
accelerate adoption of safety practices across the industry.

The AI safety landscape has evolved significantly over the past two years.
Organizations are moving beyond theoretical frameworks toward practical,
deployable solutions that can be embedded in everyday engineering workflows.
This shift creates an opportunity for partnerships that bridge the gap
between academic research and production-grade tooling.

Our experience working with enterprise clients has revealed a consistent
pattern: teams understand the importance of safety testing, but lack the
infrastructure to make it routine. The friction of switching between
development tools and safety auditing platforms means that checks are
performed sporadically — if at all.

## Proposed Collaboration

We propose collaboration in three areas:

### 1. Evaluation Frameworks

Standardized benchmarks for measuring model safety across common deployment
scenarios. Current evaluation methods are fragmented — each organization
develops proprietary test suites that cannot be compared across teams or
projects. We propose a shared framework that:

- Defines a common taxonomy of safety dimensions (toxicity, bias,
  hallucination, privacy leakage, prompt injection)
- Provides reference implementations for each evaluation category
- Supports both automated scoring and human-in-the-loop review
- Integrates with popular ML experiment tracking platforms

The framework would be versioned and extensible, allowing the community
to contribute new evaluation modules as the threat landscape evolves.

### 2. Developer Tooling

CLI and IDE integrations that surface safety metrics during the development
process, not just in post-deployment audits. The key insight is that
safety feedback must arrive at the same time as functional feedback —
in the developer's terminal, alongside test results and linting output.

We envision a pipeline where:

1. The developer writes or modifies a prompt template
2. The CLI automatically runs the template against the evaluation suite
3. Results appear inline, with actionable recommendations
4. Blocking issues prevent deployment through CI/CD gate checks

This approach mirrors the shift-left movement in security, where
vulnerability scanning moved from quarterly audits to continuous
integration. Safety deserves the same treatment.

### 3. Open Datasets

Curated datasets for red-team testing that can be shared across the
research community. High-quality adversarial datasets are expensive to
produce, and most organizations cannot justify the investment individually.
A collaborative approach would:

- Pool resources across participating organizations
- Ensure diversity of attack vectors and languages
- Maintain versioning and provenance tracking
- Include both synthetic and human-generated examples

> Our goal is to make safety checks as natural as running tests —
> integrated into every developer's workflow, not bolted on after the fact.

## Technical Architecture

The proposed system follows a modular architecture with three layers:

**Data Layer** — Stores evaluation datasets, model outputs, and scoring
results. Uses a schema designed for reproducibility, with content-addressed
storage for immutable test cases.

**Evaluation Layer** — Orchestrates test execution across multiple
backends (local models, API endpoints, batch inference). Supports parallel
execution and result caching to minimize redundant computation.

**Reporting Layer** — Generates dashboards, trend analyses, and
compliance reports. Designed for both technical audiences (engineers
reviewing individual test cases) and executive stakeholders (aggregate
safety scores over time).

## Timeline and Milestones

| Phase | Duration | Deliverable |
|-------|----------|-------------|
| Discovery | 4 weeks | Joint requirements document |
| Prototype | 8 weeks | MVP evaluation framework |
| Pilot | 6 weeks | Integration with 3 partner teams |
| Launch | 4 weeks | Public release and documentation |

## Expected Outcomes

- Shared evaluation framework published as open-source
- Joint research paper on developer-facing safety tooling
- Community benchmark dataset with 10k+ test cases
- Reference integration for 2 major CI/CD platforms
- Onboarding guide for new contributing organizations

## Budget and Resources

We estimate the initial phase requires a combined investment of
approximately 400 engineering hours across both organizations. TrustedAI
will contribute the tooling infrastructure and integration expertise,
while the research partner provides evaluation methodology and dataset
curation capabilities.

Ongoing maintenance is estimated at 40 hours per month per organization,
primarily for dataset updates and framework version releases.

## Risk Assessment

The primary risks to this collaboration are:

1. **Scope creep** — The breadth of AI safety concerns could expand the
   project beyond feasible timelines. Mitigation: strict phase gates and
   a defined MVP scope.

2. **Data sensitivity** — Adversarial datasets may contain harmful content
   by design. Mitigation: access controls, content warnings, and
   responsible disclosure protocols.

3. **Adoption friction** — Developers may resist additional tooling in
   their workflow. Mitigation: focus on seamless integration and
   demonstrable value through pilot programs.

## Next Steps

We would welcome the opportunity to discuss this proposal further.
Our team is available for a call at your convenience. Specific agenda
items for an initial meeting:

1. Alignment on evaluation dimensions and priority ordering
2. Data sharing agreements and IP considerations
3. Technical integration points and API design
4. Communication cadence and project governance

Please reach out to schedule a 60-minute introductory session.
We look forward to building something meaningful together.
