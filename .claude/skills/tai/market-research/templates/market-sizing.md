# Market Sizing Template

## Market Size: {Product/Category}

**Research date:** {YYYY-MM-DD}
**Depth level:** {quick / standard / deep}
**Geography:** {global / region / country}
**Segment:** {B2B / B2C / enterprise / SMB / specific vertical}

### Market Definition

| Dimension | Answer |
|-----------|--------|
| Product/service category | {what is being sold} |
| Buyer | {who pays — role and company type} |
| End user | {who uses — if different from buyer} |
| Geography | {which markets} |
| Inclusion boundary | {what counts as "in" this market} |
| Exclusion boundary | {what is explicitly "out"} |

### TAM (Total Addressable Market) — Top-Down

| Source | Market Size | CAGR | Year | Geography | Notes |
|--------|-------------|------|------|-----------|-------|
| {Analyst firm} | ${X}B | X% | YYYY | {scope} | {methodology notes} |
| {Second source} | ${Y}B | Y% | YYYY | {scope} | {methodology notes} |

**Discrepancy analysis:** If sources disagree by >20%, explain why (different definitions, different geographies, different methodologies).

**TAM estimate:** ${X}B [{source, date}]

### SAM (Serviceable Addressable Market) — Filtered

```
TAM: ${X}B
  × Geographic filter ({regions}):           ×{0.XX}
  × Segment filter ({B2B/enterprise/SMB}):   ×{0.XX}
  × Product capability filter:               ×{0.XX}
  × Regulatory/licensing filter:             ×{0.XX}
  ─────────────────────────────────────────
  = SAM: ${Y}B
```

**Assumptions:** {list each filter's rationale — sourced where possible}

### SOM (Serviceable Obtainable Market) — Bottom-Up

| Channel | Reachable Customers | Conversion Rate | ARPU | Annual Revenue |
|---------|--------------------|--------------------|------|----------------|
| {channel 1} | {number} | {X%} [{source}] | ${X} | ${X} |
| {channel 2} | {number} | {X%} [{source}] | ${X} | ${X} |
| **Total SOM (Year 1)** | | | | **${X}** |

**Year 3 projection:**

| Driver | Year 1 | Year 3 | Assumption |
|--------|--------|--------|------------|
| Customers | {N} | {N} | {growth driver} |
| ARPU | ${X} | ${X} | {pricing evolution} |
| Revenue | ${X} | ${X} | |

### Sanity Checks

| Check | Result | Status |
|-------|--------|--------|
| SOM < 5% of SAM in Year 1? | {X%} | OK / WARNING |
| SOM < SAM < TAM? | {yes/no} | OK / WARNING |
| Comparable company at similar stage did ${X} ARR? | {company, amount} | OK / WARNING |
| Growth rate realistic vs comparable companies? | {X% vs Y%} | OK / WARNING |
| What would need to be true for SOM to be 10x wrong? | {scenario} | — |

### Market Dynamics (standard + deep only)

| Force (Porter's) | Strength | Evidence |
|-------------------|----------|----------|
| Buyer power | Low / Med / High | {why} |
| Supplier power | Low / Med / High | {why} |
| Threat of substitutes | Low / Med / High | {why} |
| Threat of new entrants | Low / Med / High | {why} |
| Competitive rivalry | Low / Med / High | {why} |

### Contrarian Analysis

| Bullish Assumption | Bear Case | What Would Prove It Wrong |
|--------------------|-----------|--------------------------|
| {assumption} | {why it might not hold} | {leading indicator to watch} |

### Summary

```
TAM: ${X}B  ({source, date}, CAGR {X%})
 └─ SAM: ${Y}B  (filters: {list})
     └─ SOM: ${Z}M (Year 1) → ${W}M (Year 3)
         └─ Key assumptions: {top 2-3}
         └─ Biggest risk: {one sentence}
```

### Sources
1. {URL} — {brief description} [{Date}]
