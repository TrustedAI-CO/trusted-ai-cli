# Visualization Guide

When to add a diagram, what type to use, and how to keep it useful.

## Diagram Type Decision Matrix

Match the content pattern to the right diagram type:

| Content Pattern | Diagram Type | Mermaid Keyword |
|---|---|---|
| Sequential steps or workflow | Flowchart | `flowchart TD` |
| Component relationships or system overview | Flowchart or block diagram | `flowchart LR` |
| Request/response or multi-actor interaction | Sequence diagram | `sequenceDiagram` |
| Lifecycle or state transitions | State diagram | `stateDiagram-v2` |
| Before/after or feature comparison | Two side-by-side flowcharts | `flowchart LR` |
| Timeline or project phases | Gantt or timeline | `gantt` |
| Class or data model relationships | Class diagram | `classDiagram` |
| Decision logic with branches | Flowchart with decision nodes | `flowchart TD` |

**Default to flowchart.** It covers 70% of cases. Only reach for specialized types
when the content genuinely involves sequences (actors exchanging messages) or states
(an object transitioning between modes).

## Quality Checklist

Before including a diagram, verify:

- [ ] **Adds information.** The diagram reveals structure, sequence, or relationships
  that prose alone doesn't communicate clearly. If the text already says it plainly,
  skip the diagram.
- [ ] **Readable at a glance.** A reader should understand the main flow in under
  10 seconds. If they need to study it, it's too complex.
- [ ] **Labeled clearly.** Node labels use plain language, not internal variable names
  or abbreviations the reader hasn't seen.
- [ ] **Right number of nodes.** 4-12 nodes is the sweet spot. Under 4 is too trivial
  to diagram. Over 12 needs to be split or simplified.
- [ ] **Has a caption.** A one-line description above or below the diagram explaining
  what the reader is looking at.

## Anti-Patterns

- **Decorative diagrams.** A diagram that restates a 2-sentence paragraph adds clutter,
  not clarity. Only diagram what's hard to describe linearly.
- **Kitchen-sink diagrams.** Cramming every detail into one diagram. Split complex
  systems into focused views (overview + detail diagrams).
- **Unlabeled arrows.** Every connection should have a label or be obvious from context.
  An arrow from A to B without explanation forces the reader to guess the relationship.
- **Diagram-only explanations.** A diagram supports prose — it doesn't replace it.
  Always include a text explanation alongside the diagram.
