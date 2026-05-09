# Repository Guidelines

## Project Structure & Module Organization

This repository contains the `trusted-ai-cli` Python package, exposed as the `tai` command. Core code lives in `tai/`: `main.py` defines the Typer entry point, `commands/` contains CLI command groups, and `core/` contains shared auth, config, HTTP, project, template, and utility logic. Packaged assets live in `tai/data/`, `tai/templates/typst/`, and `tai/hooks/`; keep these paths aligned with `pyproject.toml` force-includes. Tests live in `tests/` with shared fixtures in `tests/conftest.py` and module-focused files named `test_*.py`.

## Build, Test, and Development Commands

- `uv sync --all-extras` — install Python 3.11+ dependencies, including dev and optional sales extras.
- `uv run tai --help` — run the CLI locally through the project environment.
- `uv run pytest` — run the full test suite with coverage; `pyproject.toml` enforces `--cov=tai` and an 80% minimum.
- `uv run pytest tests/test_config.py` or `uv run pytest -k "test_login"` — run a focused test file or name match.
- `uv run pytest --no-cov` — faster local iteration when coverage is not needed.
- `uv build` — build distribution artifacts from `pyproject.toml`.

## Coding Style & Naming Conventions

Use Python 3.11+ idioms, type hints, and 4-space indentation. Keep functions small and files focused. Prefer immutable updates, especially for Pydantic models (`model_copy()` or new objects rather than in-place mutation). Raise `TaiError` subclasses with user-facing `hint` values for recoverable CLI failures. New command modules should be lowercase, registered in `tai/main.py`, and expose a `typer.Typer()` app. User-facing commands should support `--json` when practical.

## Testing Guidelines

Write tests before implementation for new behavior and regression tests for bug fixes. Use `pytest`, `pytest-httpx`, and `respx` to mock HTTP or external services. Do not hardcode secrets, tokens, or API keys; use fixtures or environment overrides. Keep coverage at or above 80%.

## Commit & Pull Request Guidelines

Git history follows Conventional Commits, for example `feat(skills): add tai-slides skill`, `fix: handle empty task response`, or `test: add config coverage`. PRs should include a concise summary, linked issue or context, test results (`uv run pytest`), and screenshots or terminal output for visible CLI changes.

## Agent CLI Setup

Claude Code assets are refreshed with `uv run tai claude setup-skills --force` and `uv run tai claude setup-hooks`. Codex assets are refreshed with `uv run tai codex setup-skills --force`; use `uv run tai codex setup-agents` to create a managed repository `AGENTS.md` and `uv run tai codex status --json` for diagnostics.

## Security & Configuration Tips

Configuration precedence is CLI flags, `TAI_*` environment variables, project `.tai.toml`, then user config at `~/.config/tai/config.toml`. Store secrets through the CLI/keychain flow; never commit credentials or local `.venv` artifacts.
