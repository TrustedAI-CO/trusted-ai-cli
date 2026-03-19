# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/), and this project adheres to [Semantic Versioning](https://semver.org/).

## [0.2.7] - 2026-03-19

### Changed
- Market-research skill v2.0: 10 Market Thinking Frameworks, interactive research checkpoints, 3-tier depth levels (quick/standard/deep), cross-research persistence, and automatic context detection
- Added external templates for competitor analysis, market sizing, idea validation, and investor-ready output format
- Added market-specific research quality checklist with depth, objectivity, and completeness checks
- Strengthened contrarian analysis with structured tables in every research mode

## [0.2.6] - 2026-03-19

### Changed
- Tech-research skill v2.0: added Research Prime Directives, Thinking Instincts, depth modes (Quick/Standard/Deep), multi-source triangulation protocol, adversarial red team section, interactive checkpoints, and completion summary dashboard
- Updated comparison-matrix, architecture-decision-record, and deep-dive-summary templates with red team sections, failure mode analysis, and source type labeling
- Strengthened research quality checklist with triangulation, adversarial depth, and depth indicator checks

## [0.2.5] - 2026-03-19

### Added
- `tai setup` interactive config wizard that prompts for every variable in the active profile, with Enter-to-skip for already-set values, sensitive field masking, and type coercion

## [0.2.4] - 2026-03-19

### Fixed
- `tai login` crash on macOS when keychain returns error -25244 (`PasswordSetError`). Keystore now catches all `KeyringError` subtypes and falls back to file storage gracefully.

## [0.2.3] - 2026-03-19

### Added
- Technical research skill (`/tech-research`) with 4 modes: library/tool comparison, architecture decision records, technology deep dives, and troubleshooting research
- Output templates for each mode: comparison matrix, ADR, deep-dive summary, and troubleshooting report
- Research quality checklist for sourcing standards, objectivity, and decision orientation
- Optional context7 MCP and chub CLI integration for authoritative documentation lookup
- Research log persistence (`~/.tai-skills/projects/$SLUG/research-log.jsonl`)

### Changed
- Updated README skill table to list all 18 bundled skills (was 14)

## [0.2.2] - 2026-03-19

### Added
- Visualization support for content-writer skill — Mermaid diagram guidance, visualization quality gate (Step 3D), briefing preference (Step 0E), and per-template visualization hints
- Visualization reference guide (`references/visualization-guide.md`) with diagram type decision matrix, quality checklist, and anti-patterns

## [0.2.1] - 2026-03-19

### Added
- Multilingual language policy for all 15 TAI skills — skills now respond in the user's conversational language (Japanese, Vietnamese, etc.) while keeping severity labels, verdict strings, and technical terms in English for consistency

## [0.2.0] - 2026-03-19

### Added
- `tai-market-research` Claude Code skill — startup market research with 3 specialized modes: competitive analysis (SWOT, competitive matrix, positioning gaps), market sizing (TAM/SAM/SOM with top-down + bottom-up), and idea validation (go/no-go assessment)
- Web search integration (WebSearch + WebFetch) for real-time market data
- Quality gate with source attribution, recency checks, and contrarian evidence requirements

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
- Strategic compact skill (`.claude/skills/tai/smart-compact/SKILL.md`) — tai-workflow-aware compaction guide for Claude Code sessions
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
