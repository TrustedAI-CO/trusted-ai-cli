---
id: contributing
type: contributing
parent: null
children: []
related: []
derived: true
---

> ⚠️ Derived doc — generated/maintained post-ship by an agent; may lag the code. Source of truth is `docs/specs/` + `docs/prd.md`. Regenerate, don't hand-edit as canon.

# Contributing

## Local Development
```bash
uv sync --all-extras
```

## Tests
```bash
pytest          # 80% coverage required
```

## Doc-first rule
Change the governing spec under `docs/specs/` *before* the code, in the same PR.
Code under a spec's `code:` path does not merge until that spec is `status: approved`.
