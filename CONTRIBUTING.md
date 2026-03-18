# Contributing

## Setup

```bash
git clone https://github.com/TrustedAI-CO/trusted-ai-cli.git
cd trusted-ai-cli
uv sync --all-extras        # Install all dependencies including dev
```

Requires Python 3.11+ and [uv](https://docs.astral.sh/uv/).

## Running tests

```bash
pytest                      # Full suite with 80% coverage check
pytest tests/test_config.py # Single file
pytest -k "test_login"      # By name
pytest --no-cov             # Skip coverage (faster iteration)
```

Coverage must stay at or above 80%. The CI will fail if it drops below.

## Project structure

```
tai/
├── main.py          # Entry point
├── core/            # Shared library (auth, config, errors, http, etc.)
├── commands/        # CLI command groups (one file per group)
├── hooks/           # Claude Code hooks (Node.js scripts)
└── plugins/         # Entry-point plugin discovery
tests/
├── conftest.py      # Shared fixtures
├── test_*.py        # Core module tests
└── commands/        # Command-level tests
```

## Development workflow

1. Create a feature branch from `develop`
2. Write tests first (TDD) — see [testing rules](#testing-rules)
3. Implement the feature
4. Run `pytest` and verify 80%+ coverage
5. Commit with [conventional commits](https://www.conventionalcommits.org/): `feat:`, `fix:`, `refactor:`, etc.
6. Open a PR against `develop`

## Testing rules

- Write the test before the implementation
- Every new function gets a test
- Every bug fix gets a regression test
- Mock external services (`respx` for HTTP, `pytest-httpx` for httpx)
- Never hardcode secrets or API keys in tests — use fixtures

## Code style

- Python 3.11+ with type hints
- Immutable data: use `model_copy()` or new objects, never mutate in place
- Small functions (< 50 lines), small files (< 400 lines)
- Error handling: raise `TaiError` subclasses with a `hint` for the user
- `--json` support: every user-facing command should support JSON output

## Adding a new command

1. Create `tai/commands/mycommand.py` with a `typer.Typer()` app
2. Register it in `tai/main.py` via `app.add_typer()`
3. Add tests in `tests/commands/test_mycommand_cmd.py`
4. Update `tai/docs.py` with the new command's reference

## Adding a new skill

1. Create `.claude/skills/tai/my-skill/SKILL.md` with YAML frontmatter:
   ```yaml
   ---
   name: my-skill
   version: 1.0.0
   description: |
     One-line description of what this skill does.
   allowed-tools:
     - Read
     - Grep
     - Glob
     - Bash
   ---
   ```
2. Write the skill instructions in markdown below the frontmatter
3. Run `tai claude setup-skills --force` to install it locally
4. Test the skill in Claude Code with `/my-skill`

## Commit messages

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
feat: add new command for X
fix: handle empty response in tasks list
refactor: extract auth token refresh to helper
docs: update README with new skills table
test: add coverage for secret rotation
chore: update dependencies
```
