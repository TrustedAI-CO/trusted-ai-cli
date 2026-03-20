# tai — TrustedAI CLI

Internal CLI for TrustedAI company tools and APIs. Links git repos to Notion projects, manages secrets, orchestrates tasks and meetings, and ships with 19 bundled Claude Code skills for plan reviews, QA, design audit, and shipping workflows.

## Install

Requires Python 3.11+.

```bash
uv tool install "trusted-ai-cli @ git+https://github.com/TrustedAI-CO/trusted-ai-cli.git"
```

Or with pip:

```bash
pip install "trusted-ai-cli @ git+https://github.com/TrustedAI-CO/trusted-ai-cli.git"
```

For local development, see [Development](#development) below.

## Quick start

```bash
# Authenticate with Google OAuth
tai login

# Link your repo to a Notion project
tai link

# View project status
tai project status

# List your tasks
tai tasks

# Chat with AI (coming soon)
# tai ai chat "summarize this week's tasks"
```

## Commands

| Command | What it does |
|---------|-------------|
| `tai login` / `logout` / `whoami` | Google OAuth authentication |
| `tai claude login` / `logout` / `status` | Claude Code authentication |
| `tai claude setup-skills` | Install bundled Claude Code skills |
| `tai claude setup-hooks` | Install Claude Code hooks for quality gates and session management |
| `tai link` / `unlink` / `open` | Link repos to Notion projects |
| `tai project new` / `status` | Create or inspect projects |
| `tai tasks` / `add` / `done` | Manage Notion tasks |
| `tai meetings` / `add` | Manage Notion meetings |
| `tai ai chat` / `complete` / `models` | AI chat and completions *(coming soon)* |
| `tai api call` / `list` | Call company API endpoints *(coming soon)* |
| `tai config get` / `set` / `list` | Profile-based configuration |
| `tai secret set` / `get` / `rotate` / `exec` | Secret management with system keychain *(coming soon)* |
| `tai docs` | LLM-friendly usage reference |

Every command supports `--json` for machine-readable output.

## Claude Code Skills

19 bundled skills installed via `tai claude setup-skills`:

| Skill | Speed | What it does |
|-------|-------|-------------|
| `/plan-biz` | Full | CEO-mode plan review with 4 expansion modes |
| `/plan-biz-light` | Fast | Premise challenge + dream state + top 3 risks |
| `/plan-eng` | Full | Architecture, data flow, edge cases, test plan |
| `/plan-eng-light` | Fast | Scope challenge + architecture diagram + top concerns |
| `/plan-design` | Full | Designer's eye review, rates each dimension 0-10 |
| `/review` | Full | Pre-landing PR review with auto-fixing |
| `/review-light` | Fast | CRITICAL-only single-pass (SQL, races, LLM trust) |
| `/ship` | Full | Merge, test, review, version bump, changelog, PR |
| `/qa` | Full | Systematic QA testing + bug fixing |
| `/qa-only` | Full | QA testing, report only (no fixes) |
| `/design-consultation` | Full | Design system proposal with research |
| `/design-review` | Full | Visual QA for spacing, hierarchy, AI slop |
| `/document-release` | Full | Post-ship documentation update |
| `/retro` | Full | Weekly engineering retrospective |
| `/content-writer` | Full | Interactive content writing with voice profiles and AI-slop detection |
| `/market-research` | Full | Competitive analysis, market sizing, idea validation |
| `/tech-research` | Full | Library comparison, architecture decisions, deep dives, troubleshooting |
| `/project` | Fast | Project management: link, status, tasks, meetings, open tools |
| `/smart-compact` | Full | Strategic context compaction guide |

"Light" variants trade thoroughness for speed — use them when you need quick feedback.

## Claude Code Hooks

Installed via `tai claude setup-hooks`. Adds quality gates, session management, and developer experience hooks:

- **quality-gate** — Runs ruff (Python) or biome/prettier (JS) after file edits
- **cost-tracker** — Tracks token and cost metrics per session
- **session-start/end** — Loads and persists session context
- **doc-file-warning** — Warns about non-standard documentation files
- **suggest-compact** — Suggests `/compact` at ~50 tool calls
- **tmux-reminder** — Suggests tmux for long-running commands
- **git-push-reminder** — Review changes before pushing

## Configuration

Config lives at `~/.config/tai/config.toml` (XDG-compliant). Supports multiple profiles:

```bash
tai config list              # Show all settings
tai config set ai_model gpt-4o
tai config list-profiles     # Show available profiles
tai config switch staging    # Switch active profile
```

**Precedence:** CLI flags > env vars (`TAI_*`) > project config (`.tai.toml`) > user config.

## Secrets

Three-layer fallback: system keychain > encrypted file > environment variables.

```bash
tai secret set MY_API_KEY
tai secret get MY_API_KEY
tai secret exec -- my-command   # Injects secrets as env vars
tai secret rotate MY_API_KEY    # Generate and store a new value
```

## Plugins

Third-party CLI extensions register via entry points:

```toml
# In your plugin's pyproject.toml
[project.entry-points."tai.plugins"]
my-plugin = "tai_myplugin.commands:app"
```

## Development

```bash
git clone https://github.com/TrustedAI-CO/trusted-ai-cli.git
cd trusted-ai-cli
uv sync --all-extras
pytest                        # Runs with 80% coverage requirement
```

See [ARCHITECTURE.md](ARCHITECTURE.md) for internals and [CONTRIBUTING.md](CONTRIBUTING.md) for the development workflow.

## License

Internal — TrustedAI Co.
