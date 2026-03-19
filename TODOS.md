# TODOs

## Python-native hooks (ruff, pytest, mypy)

**What:** Write Python-specific post-edit hooks that run `ruff check`, `mypy`, or `pytest` after file edits — equivalent to ECC's JS-specific hooks but for Python.

**Why:** The curated hook set skips JS-specific hooks (Prettier, tsc). Python devs would benefit from equivalent quality tooling hooks.

**Context:** Natural follow-up after base hook infrastructure lands. These hooks would be written fresh (in JS or Python), not ported from ECC. Need to handle tool detection (is ruff installed?) gracefully.

**Depends on:** setup-hooks feature landing first.

