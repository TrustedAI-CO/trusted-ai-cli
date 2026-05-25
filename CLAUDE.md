# tai CLI — Project Instructions

## Project Structure

```
tai/
├── main.py          # Entry point, Typer app assembly
├── core/            # Shared library (auth, config, errors, http, keystore, updater)
├── commands/        # CLI command groups (one file per group)
├── hooks/           # Claude Code hooks (Node.js scripts)
├── data/            # Bundled templates, skills, brand assets
└── plugins/         # Entry-point plugin discovery
tests/
├── conftest.py      # Shared fixtures
└── commands/        # Command-level tests
docs/                # HTML documentation (see docs/index.html)
.claude/skills/tai/  # Claude Code skills (SKILL.md files)
```

## Commands

```bash
uv sync --all-extras       # Install dependencies
pytest                     # Run tests (80% coverage required)
uv build --wheel           # Build distribution wheel
tai update                 # Self-update from GitHub Releases
```

## Releasing a New Version

Version lives in `pyproject.toml` (line 7). `VERSION` file must match.
Users get updates via `tai update` which downloads the wheel from GitHub Releases.

**Steps:**

1. Bump version in `pyproject.toml` and `VERSION`
2. Commit: `git commit -m "chore: bump version to X.Y.Z"`
3. Push: `git push`
4. Build: `uv build --wheel`
5. Release: `gh release delete vX.Y.Z --yes 2>/dev/null && gh release create vX.Y.Z dist/trusted_ai_cli-X.Y.Z-py3-none-any.whl --title "vX.Y.Z" --notes "..."`
6. Verify: `tai update`

**If pushing fixes after a release:** rebuild wheel, delete and recreate the release.
The release tag must match the version string (e.g., `v0.36.0`).

## Key Architecture Decisions

- **Auth:** Google OAuth PKCE with `id_token` for Hub API, auto-refreshes via `get_id_token()`
- **Config:** TOML-based, XDG paths, profile-based (dev/staging/prod)
- **Hub:** All workspace commands under `tai hub` — uses `_hub_client()` and `_hub_request()` pattern
- **Skills:** Markdown files with YAML frontmatter in `.claude/skills/tai/`
- **Updates:** `tai update` checks GitHub Releases, compares `importlib.metadata.version()` against latest release tag

## Code Style

- Python 3.11+ with type hints
- Immutable data (use `model_copy()`, never mutate)
- Small functions (<50 lines), small files (<400 lines)
- Errors: raise `TaiError` subclasses with a `hint` field
- All user-facing commands support `--json`
