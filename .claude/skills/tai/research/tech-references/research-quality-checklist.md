# Research Quality Checklist

Verify every item before delivering research output. If any check fails, fix the
output before presenting it to the user.

## Sourcing

- [ ] All quantitative claims have a source or are labeled as estimates
- [ ] Sources include URLs, dates, and brief descriptions
- [ ] Sources are grouped by type (Official/Benchmark/Community/Case Study)
- [ ] At least 2-3 sources cross-referenced for critical claims
- [ ] Official docs and primary sources preferred over blog posts
- [ ] Data older than 18 months is flagged with `[YYYY data — may be outdated]`

## Triangulation (Standard/Deep only)

- [ ] Major claims verified from 2+ source types
- [ ] Single-source-type findings are flagged with confidence level
- [ ] Source types explicitly noted for each major claim

## Objectivity

- [ ] At least one contrarian argument or risk included per major finding
- [ ] Fact, inference, and recommendation are labeled separately
- [ ] No unacknowledged bias toward a particular tool/approach
- [ ] "Popular" is not treated as "correct" — GitHub stars != quality
- [ ] Survivorship bias considered — failure stories searched, not just successes

## Adversarial Depth (Standard/Deep only)

- [ ] Red team section present with steel-manned alternatives
- [ ] Worst-case scenario for recommendation is described with specifics
- [ ] Conditions where recommendation is wrong are stated explicitly
- [ ] Confidence calibration (High/Medium/Low) is present with reasoning

## Decision Orientation

- [ ] The output makes a specific decision easier, not just "more informed"
- [ ] Recommendation is concrete and actionable (not "it depends")
- [ ] Conditions for choosing differently are stated explicitly
- [ ] Tradeoffs are specific (not "performance vs flexibility" — say what performance)

## Technical Rigor

- [ ] Benchmark data includes methodology and conditions, not just numbers
- [ ] Version numbers are specified for all tools/libraries discussed
- [ ] Breaking changes and migration paths are noted where relevant
- [ ] Licensing implications are mentioned for library comparisons
- [ ] Second-order effects considered (hiring, ecosystem trajectory, upgrade path)

## Depth Indicators

- [ ] Forcing questions were applied (check mode-specific list in SKILL.md)
- [ ] ASCII diagrams present for non-trivial concepts (Deep mode: mandatory)
- [ ] "Where it breaks" / failure modes described with specific boundary conditions
- [ ] Recommendation changes conditions are concrete, not vague

## Completeness

- [ ] Web search was used for real-time data (not just training data)
- [ ] Documentation lookup attempted (context7/chub) where applicable
- [ ] Executive summary captures the headline finding in 3-5 sentences
- [ ] Sources section is present with numbered URLs grouped by type
- [ ] Completion summary dashboard is present
