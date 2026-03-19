# Template: Comparison Post

Help the reader decide between two or more options. Be honest, specific, and
opinionated — a comparison that doesn't pick a winner is useless.

## Structure

### Title
Format: "{X} vs {Y}: {what matters}" or "{X} vs {Y} for {use case}"
Examples: "Typer vs Click: Choosing a Python CLI Framework"

### Introduction (1-2 paragraphs)
- What decision does the reader face?
- Why is this comparison relevant now?
- Spoiler the recommendation upfront: "TL;DR: Use X if {condition}, Y if {condition}."

### Quick Comparison Table
A scannable table comparing the key dimensions:

| Dimension | X | Y |
|-----------|---|---|
| {dim 1}   | {value} | {value} |
| {dim 2}   | {value} | {value} |
| ...       | ... | ... |

### Detailed Comparison (one section per dimension)
For each dimension:
1. **What it means** — why this dimension matters for the decision
2. **X's approach** — with code example or evidence
3. **Y's approach** — with code example or evidence
4. **Verdict** — which wins on this dimension and why

### When to Choose X
Concrete scenarios: "Choose X when you need {specific requirement}, your team has
{specific background}, or you're building {specific type of project}."

### When to Choose Y
Same format. Be fair — every tool has its strengths.

### The Verdict
State your recommendation clearly:
- "For most teams building {use case}, we recommend {X} because {reason}."
- Acknowledge the tradeoff: "You give up {thing} but gain {thing}."

### Visualization Opportunities
- Architecture comparison: side-by-side diagrams showing how each option structures
  the same system.
- Decision flowchart: a "which should I choose?" flowchart based on the reader's
  constraints (team size, use case, performance needs).

## Writing Rules
- Be opinionated. "It depends" is not a conclusion.
- Use real code for both options. Show the same task implemented in each.
- Acknowledge your biases upfront if you have a clear favorite.
- Don't force balance. If one option is clearly better for most use cases, say so.
- Include "I was wrong about..." or "I expected X but found Y" if applicable —
  surprising findings are the most valuable part of a comparison.
- Date the comparison. Tools change. State which versions you're comparing.
