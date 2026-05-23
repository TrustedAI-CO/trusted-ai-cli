# Template: How-To Guide

Task-oriented, practical instructions. The reader has a specific goal and wants
to achieve it with minimum friction.

## Structure

### Title
Format: "How to {verb} {thing} [with/using {tool}]"
Examples: "How to Deploy a Python App with Railway", "How to Set Up Voice Profiles"

### Prerequisites (optional)
Bulleted list of what the reader needs before starting. Include versions.
Skip if obvious.

### Steps
Numbered steps, each with:
1. **What to do** — one clear action per step
2. **How to do it** — code snippet, command, or screenshot
3. **What you should see** — expected output or result
4. **Troubleshooting** (if applicable) — common failure and fix, indented under the step

### Verify It Works
A quick check the reader can run to confirm success. Command + expected output.

### Next Steps (optional)
2-3 links to related guides or features the reader might want next.

### Visualization Opportunities
- Before the steps: a flowchart overview of the full process so the reader knows
  where they're headed.
- At decision points: a decision tree when the reader must choose between alternatives
  (e.g., "Docker vs native install").

## Writing Rules
- One action per step. If a step has "and" in it, split it.
- Show the command AND the output. Don't make the reader guess.
- Test every command you include. Use real output, not placeholder.
- Keep prerequisite lists short — if there are >5 prereqs, the guide scope is too wide.
- Time estimate in the intro: "This takes about 10 minutes."
