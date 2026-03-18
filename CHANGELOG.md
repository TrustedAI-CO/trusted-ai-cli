# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/), and this project adheres to [Semantic Versioning](https://semver.org/).

## [0.1.0] - 2026-03-19

### Added
- Core CLI framework with 8 command groups: auth, claude, config, secret, project, tasks, meetings, ai/api
- Google OAuth 2.0 PKCE authentication with domain restriction and auto-refresh
- Profile-based configuration with TOML files and multi-source precedence
- Three-layer secret storage: system keychain, encrypted file, environment variables
- Notion integration for project linking, tasks, and meetings
- AI chat and completion commands with model selection
- Raw API client for company endpoints with OpenAPI spec listing
- `tai claude setup-skills` — installs 14 bundled Claude Code skills for plan reviews, QA, design audit, shipping, and retrospectives
- `tai claude setup-hooks` — installs Claude Code hooks for quality gates, session management, and developer experience
- Light skill variants (`plan-ceo-light`, `plan-eng-light`, `review-light`) for fast feedback when speed matters
- `tai docs` — LLM-friendly usage reference
- Plugin system via entry points for third-party extensions
- 80% test coverage requirement enforced by CI
