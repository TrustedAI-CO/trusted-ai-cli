<!-- tai:codex-agents-template -->
# Repository Guidelines

## Project Structure & Module Organization

Use this file to give Codex repository-specific instructions. Keep source code, tests, generated assets, and documentation paths explicit. Update this section with the real layout, for example `src/` for implementation, `tests/` for pytest or unit tests, and `docs/` for reference material.

## Build, Test, and Development Commands

Document the exact commands contributors should run. Examples:

- `uv sync --all-extras` — install Python dependencies.
- `uv run pytest` — run tests with the project environment.
- `uv run tai codex setup-skills --force` — refresh bundled tai skills for Codex.

## Coding Style & Naming Conventions

Prefer small, typed functions and established project patterns. Follow the formatter and linter already used by this repository. Name tests after the behavior under test, such as `test_<feature>_<condition>`.

## Testing Guidelines

Add or update tests for every behavior change and bug fix. Mock network, credentials, and external services. Run focused tests first, then the full suite before opening a PR.

## Codex-Specific Instructions

Run `tai codex status` to inspect local Codex setup. Run `tai codex setup-skills --force` after upgrading `tai` to refresh personal skills under `~/.codex/skills`. Do not overwrite this file manually if it is managed by tai unless you intend to replace the generated guide.

## Commit & Pull Request Guidelines

Use Conventional Commits where possible, for example `feat: add codex setup command` or `fix: preserve custom AGENTS.md`. PRs should summarize the change, include test results, and call out any migration or setup impact.
