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

