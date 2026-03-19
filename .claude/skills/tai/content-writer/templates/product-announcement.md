# Template: Product Announcement / Release Notes

Communicate what shipped, why it matters, and what the reader can do now.
Works for release announcements, feature launches, and update posts.

## Structure

### Title
Format: "{Product}: {headline benefit}" or "Announcing {feature}"
Examples: "tai v0.3: Write Content Like You Mean It", "Announcing Voice Profiles"

### Hook (1-2 paragraphs)
Start with the user's problem or desire, not the feature name.
Bad: "We're excited to announce..."
Good: "Writing blog posts used to take 3 hours. Now it takes 15 minutes."

### What's New
For each feature or change:
1. **What it does** — one sentence, user-facing language
2. **Why it matters** — the problem it solves or the value it unlocks
3. **How to use it** — one code snippet or action
4. **Before/after** (optional) — concrete comparison

Group related changes under subheadings. Lead with the biggest improvement.

### For Release Notes Specifically
Use this format for each entry:
- **{Feature name}** — {one-line description of what the user can now do}
  {Optional: 1-2 sentences of context or a code snippet}

Separate user-facing changes from internal/contributor changes.

### What's Next (optional)
1-2 sentences about the roadmap. Be specific: "Next up: multi-platform repurposing"
not "We have exciting things planned."

### Get Started
Clear call to action: install command, link to docs, upgrade instructions.

### Visualization Opportunities
- What's New: an architecture or flow diagram for major new features, showing how
  the feature fits into the product.
- Before/after: a side-by-side diagram when the change restructures a workflow.
- Usually skip diagrams for minor releases or simple feature additions.

## Writing Rules
- Lead with value, not implementation details.
- "You can now..." not "We refactored the..."
- Every feature gets a concrete example, not just a description.
- Release notes should make users think "I want to try that."
- Keep individual entries scannable — bold the feature name, keep descriptions to 1-2 lines.
- For git-aware mode: pull real commit messages, PR titles, and CHANGELOG entries as source
  material, then rewrite in user-facing language.
