# TODOs

## tai claude setup-hooks --upgrade flag

**What:** Add a `--upgrade` flag that checks if bundled hooks are newer than what's in settings.json and only updates if changed.

**Why:** After upgrading tai, users need to re-run `setup-hooks` to get new hook versions. An `--upgrade` flag (or auto-detection) would make this smoother.

**Context:** Currently `setup-hooks` is idempotent — running it again replaces [tai] hooks with the latest. An explicit `--upgrade` would add a version check to skip unnecessary writes. Low priority since re-running `setup-hooks` is harmless. Would need version tracking (e.g., a `_tai_hooks_version` field in settings.json).

**Depends on:** None (setup-hooks has landed).

## Python-native hooks (ruff, pytest, mypy)

**What:** Write Python-specific post-edit hooks that run `ruff check`, `mypy`, or `pytest` after file edits — equivalent to ECC's JS-specific hooks but for Python.

**Why:** The curated hook set skips JS-specific hooks (Prettier, tsc). Python devs would benefit from equivalent quality tooling hooks.

**Context:** Natural follow-up after base hook infrastructure lands. These hooks would be written fresh (in JS or Python), not ported from ECC. Need to handle tool detection (is ruff installed?) gracefully.

**Depends on:** None (setup-hooks has landed).

