# TODOs

## Python-native hooks (ruff, pytest, mypy)

**What:** Write Python-specific post-edit hooks that run `ruff check`, `mypy`, or `pytest` after file edits — equivalent to ECC's JS-specific hooks but for Python.

**Why:** The curated hook set skips JS-specific hooks (Prettier, tsc). Python devs would benefit from equivalent quality tooling hooks.

**Context:** Natural follow-up after base hook infrastructure lands. These hooks would be written fresh (in JS or Python), not ported from ECC. Need to handle tool detection (is ruff installed?) gracefully.

**Depends on:** None (setup-hooks has landed).

## Additional PDF template types (invoice, letter, contract)

**What:** Add more Typst document templates beyond the initial Proposal and Technical Report.

**Why:** Broader template coverage means more team use cases handled without ad-hoc formatting — sales pipeline (invoice/quote), legal (contract), formal correspondence (letter).

**Pros:** Same infrastructure, incremental effort per template. Each template is self-contained.

**Cons:** Each template needs design work (layout, sections, brand integration) and testing.

**Context:** The `tai pdf` command group ships with Proposal and Technical Report templates. Adding more types follows the exact same pattern — create a new directory under `tai/data/templates/`, add TEMPLATE.yaml metadata, write the .typ file. Priority: P2. Effort: S per template (human: ~4h / CC: ~15 min each).

**Depends on:** `tai pdf` feature shipping first (thien-trustedai/typst-pdf-tool).

## Context monitor hook (agent-facing context warnings)

**What:** A PostToolUse hook that reads context window usage metrics and injects warnings into the agent's conversation at 35% and 25% remaining context.

**Why:** Long-running skills (/plan-ceo, /qa, /ship) consume significant context. The agent has no awareness it's running low until it hits the wall mid-task. GSD (38K stars) solved this with a context monitor that makes the agent itself aware of context pressure.

**Pros:** Immediate quality improvement for every long-running skill. Simple hook, no architectural changes.

**Cons:** Requires a statusLine hook to produce a bridge file (PostToolUse hooks do NOT receive context_window data — verified via spike 2026-03-22). Claude Code only supports one statusLine handler, so this conflicts with any existing statusLine config (e.g., @wyattjoh/claude-status-line). A wrapper approach works but adds complexity.

**Context:** Inspired by GSD's `gsd-context-monitor.js`. TAI has `suggest-compact.js` but it notifies the user, not the agent. This hook would inject warnings into the model's conversation so the AI can proactively save state. Priority: P2 (downgraded from P1 due to statusLine conflict). Effort: M (human: ~1 week / CC: ~30 min) — includes statusLine wrapper component.

**Spike findings (2026-03-22):** PostToolUse stdin contains tool_name, tool_input, tool_response, session_id, cwd — NO context_window data. Only statusLine hooks receive `context_window.remaining_percentage`. GSD uses a two-component bridge: statusLine writes `/tmp/claude-ctx-{session_id}.json`, PostToolUse reads it. The wrapper approach (TAI statusLine reads metrics + writes bridge file, then shells out to existing statusLine for display) is the cleanest path but was deferred due to invasiveness.

**Depends on:** None, but conflicts with existing statusLine configuration.

## File-based project state (.tai/ directory)

**What:** A local directory structure for persisting structured skill outputs (review results, QA reports, codebase maps, plan decisions) that survive context resets.

**Why:** TAI skills produce valuable analysis that is lost when the context window resets. A file-based state directory makes skill outputs persistent, git-trackable, and readable by other skills. GSD's `.planning/` directory is the proven pattern.

**Pros:** Foundation for skill interconnection — /review can check if /qa passed, /ship can verify review status, /tai-map output feeds into planning. State survives `/clear`.

**Cons:** Needs careful schema design to avoid fragmentation. Must define gitignore behavior (default ignored, user opts in). Existing skills need incremental updates to read from .tai/ (check-if-exists pattern, no big-bang migration).

**Context:** Directory structure: `.tai/state.md`, `.tai/map/`, `.tai/reviews/`, `.tai/qa/`, `.tai/init/`. Each skill writes to its own subdirectory. Integration contract: "check if file exists, load if present, otherwise proceed without." Priority: P1. Effort: M (human: ~1 week / CC: ~30 min).

**Depends on:** None (but items below depend on this).

## Codebase mapping skill (/tai-map)

**What:** A skill that spawns subagents to analyze an existing codebase and produces structured context documents (stack, architecture, conventions, concerns).

**Why:** Every TAI skill that touches code re-discovers the same codebase context. A one-time mapping produces reusable structured analysis that feeds into planning, review, and initialization skills. GSD's `/gsd:map-codebase` is the proven pattern.

**Pros:** Run once, benefit everywhere. Parallel agent analysis covers stack, architecture, conventions, and concerns in separate focused passes. Output is human-readable Markdown.

**Cons:** Analysis can become stale as codebase evolves. Needs a staleness detection mechanism or re-run trigger.

**Context:** Writes output to `.tai/map/` (4 files: stack.md, architecture.md, conventions.md, concerns.md). Each subagent has a focused scope — no overlap. Priority: P2. Effort: M (human: ~1 week / CC: ~30 min).

**Depends on:** File-based project state (.tai/ directory).

## Project initialization skill (/tai-init)

**What:** A skill that takes a project idea through structured discovery (adaptive questioning) -> research -> scoped requirements -> phased roadmap, producing structured documents in `.tai/init/`.

**Why:** TAI has planning and review skills but no build pipeline entry point. GSD's `/gsd:new-project` proves that structured initialization dramatically improves AI coding consistency. This is the most strategic addition — it gives TAI a complete lifecycle from idea to shipped code.

**Pros:** Fills TAI's biggest gap vs GSD. Produces requirements with unique IDs and a phased roadmap that downstream skills can reference. Research phase surfaces pitfalls before coding starts.

**Cons:** Largest item (L effort). Adaptive questioning is non-deterministic — needs a hard question cap (~15) and a coverage checklist. Research subagent scope needs tight boundaries to avoid bloat.

**Context:** Output: `.tai/init/project.md`, `requirements.md`, `roadmap.md`, `research/`. If `/tai-map` has been run, loads `.tai/map/` files as context during discovery. Priority: P2. Effort: L (human: ~2 weeks / CC: ~1 hour).

**Depends on:** File-based project state (.tai/ directory). Optionally reads /tai-map output.

## Fresh-context architecture for long-running skills

**What:** Rethink skill architecture so multi-section workflows (/plan-ceo, /qa) can orchestrate each section as a fresh subagent with file-based state passing via .tai/.

**Why:** Long-running skills suffer from context rot — quality degrades as the context window fills. GSD's core architectural insight is spawning fresh 200K context windows per task. This would bring the same benefit to TAI's mega-reviews.

**Pros:** Eliminates context rot for the most complex skills. Each section gets full context budget.

**Cons:** Fundamental architecture change. Requires rethinking how skills communicate state. L-XL effort.

**Context:** Deferred from GSD adoption CEO review (2026-03-22). Requires understanding Claude Code's subagent context isolation model. Priority: P3. Effort: XL (human: ~2-3 weeks / CC: ~2-4 hours).

**Depends on:** File-based project state (.tai/ directory).

