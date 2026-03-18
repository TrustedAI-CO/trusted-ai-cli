# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/), and this project adheres to [Semantic Versioning](https://semver.org/).

## [0.1.2] - 2026-03-19

### Added
- Content writer skill (`.claude/skills/tai/content-writer/`) — interactive guided content creation for blog posts, technical articles, release announcements, tutorials, case studies, and comparison posts
- Voice profile system — persistent writing style profiles at `~/.tai-skills/voice-profiles/` for consistent tone across content
- AI-slop detection quality gate — scans drafts for ~60 generic AI phrases across 9 categories and auto-rewrites them with specific language
- Codebase-aware technical writing — reads source files, tests, and docs to include accurate code examples
- Git-aware release announcements — generates release content from git log, CHANGELOG, and merged PRs
- 6 content templates: how-to guide, product announcement, case study, tutorial, comparison post, changelog entry
- Readability and factual grounding quality checks with structured reporting

## [0.1.1] - 2026-03-19

### Added
- `tai claude compact-status` command with `--json` support — shows session tool-call count, compaction history, and suggestions
- Strategic compact skill (`.claude/skills/tai/compact/SKILL.md`) — tai-workflow-aware compaction guide for Claude Code sessions
- Pre-compact resume notes — automatically saves git state and active tasks to `.context/compact-resume.md` before compaction
- Shared `getCounterFilePath()` utility in hooks lib to keep counter path convention in sync

### Changed
- `suggest-compact.js` refactored to use shared counter path helper instead of inline path construction

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
