# Template: Tutorial / Technical Article

Teach the reader something they didn't know. Combine explanation with working code.
The reader should be able to follow along and end up with something that works.

## Structure

### Title
Format: "{Verb}ing {thing}: {subtitle with scope}"
or: "A Guide to {topic} [for {audience}]"
Examples: "Building a CLI Plugin System: From Entry Points to Auto-Discovery"

### Introduction (2-3 paragraphs)
- What will the reader learn?
- Why does it matter? (what can they build with this knowledge?)
- What should they already know? (prerequisites as prose, not a bullet list)
- What will we build? (describe the end result concretely)

### Sections (3-5, each self-contained)
Each section follows this pattern:
1. **Concept** — explain the idea in plain language (1-2 paragraphs)
2. **Code** — show the implementation with comments
3. **Output** — show what running the code produces
4. **Explanation** — walk through the code, connect it back to the concept

Build incrementally: each section extends the previous one. The reader should be able
to stop at any section and have a working (if incomplete) version.

### Putting It Together
Show the complete working example. If the sections built incrementally, this is the
final assembled version with all pieces connected.

### Visualization Opportunities
- After the Introduction: an architecture or component diagram showing how the pieces
  the reader will build fit together.
- Per-section: a sequence diagram or flowchart showing execution flow for complex
  interactions. Especially useful when multiple components communicate.
- Putting It Together: an updated architecture diagram reflecting the complete system.

### Going Further (optional)
- 2-3 ideas for extending what the reader built
- Links to advanced topics, related tutorials, or documentation

## Writing Rules
- Every code block must be runnable. No pseudocode unless explicitly labeled.
- Show the output of every command. Don't leave the reader guessing.
- When referencing a codebase, use actual file paths and real function names.
  Never fabricate API signatures.
- Explain "why" before "how." The reader needs to understand the concept before
  the syntax means anything.
- Use progressive disclosure: start simple, add complexity in layers. Don't
  dump the final solution upfront.
- Test your code examples. If you're in codebase-aware mode, verify against
  the actual source.
