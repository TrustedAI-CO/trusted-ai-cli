# Architecture

## Overview

```
┌─────────────────────────────────────────────────────┐
│                    tai CLI (Typer)                   │
│  main.py — entry point, plugin discovery, globals   │
├──────────┬──────────┬──────────┬──────────┬─────────┤
│ commands │ commands │ commands │ commands │ plugins │
│  auth    │  claude  │  tasks   │  ai      │ (entry  │
│  config  │  secret  │ meetings │  api     │  points)│
│  project │  setup   │          │          │         │
├──────────┴──────────┴──────────┴──────────┴─────────┤
│                    tai/core/                         │
│  context · config · auth · http · keystore          │
│  project · skills · errors · prompt                 │
├─────────────────────────────────────────────────────┤
│              External Services                      │
│  Google OAuth · Notion API · Company API · Claude   │
└─────────────────────────────────────────────────────┘
```

## Directory layout

```
tai/
├── main.py              # Typer app, global options, plugin loader
├── docs.py              # Embedded LLM-friendly reference (tai docs)
├── core/                # Shared library — no CLI concerns
│   ├── context.py       # AppContext dataclass (profile, verbose, json)
│   ├── config.py        # ProfileConfig + TaiConfig, TOML I/O
│   ├── auth.py          # Google OAuth 2.0 PKCE with domain restriction
│   ├── http.py          # Authenticated httpx client builder
│   ├── keystore.py      # 3-layer secret storage (keychain → file → env)
│   ├── project.py       # .tai.toml manifest (Notion page binding)
│   ├── skills.py        # Skill discovery, frontmatter parsing, install
│   ├── errors.py        # TaiError hierarchy + ExitCode constants
│   └── prompt.py        # TTY detection, fuzzy search picker
├── commands/            # One module per command group
│   ├── auth.py          # login, logout, whoami
│   ├── claude.py        # Claude auth, setup-skills, setup-hooks
│   ├── config.py        # get, set, list, profiles
│   ├── secret.py        # set, get, rotate, delete, exec
│   ├── project.py       # link, unlink, new, status, open
│   ├── tasks.py         # list, add, done (Notion)
│   ├── meetings.py      # list, add (Notion)
│   ├── ai.py            # chat, complete, models
│   ├── api.py           # call, list (raw API)
│   └── setup.py         # Interactive config wizard
├── hooks/               # Claude Code integration
│   ├── __init__.py      # Hook merge/remove logic for settings.json
│   ├── hooks.json       # Hook definitions (event → matcher → script)
│   ├── scripts/         # 12 Node.js hook scripts
│   └── lib/             # Shared JS utilities
└── plugins/             # Entry-point discovery
```

## Key design decisions

### AppContext flows through Typer

Every command receives `ctx: typer.Context`. The global callback stores an `AppContext` in `ctx.obj` with the active profile, verbosity, and JSON mode. Commands call `get_ctx(ctx)` to retrieve it.

### Config precedence

CLI flags > `TAI_*` env vars > `.tai.toml` (project) > `~/.config/tai/config.toml` (user). The `ProfileConfig` model uses Pydantic Settings to layer these sources.

### Authentication

Google OAuth 2.0 with PKCE. Tokens are stored in the system keychain via `keyring`. On 401, `get_access_token()` auto-refreshes. Domain restriction is enforced at token exchange and at `current_email()`.

### Secret storage (3-layer fallback)

1. **System keychain** (macOS Keychain, GNOME Keyring, Windows Credential Locker) — preferred
2. **Encrypted file** — fallback when keychain is unavailable
3. **Environment variables** — last resort, CI-friendly

### Skills system

Skills are directories containing a `SKILL.md` with YAML frontmatter (name, version, description, allowed-tools). `tai claude setup-skills` copies each skill to `~/.claude/skills/tai-<name>/` so Claude Code discovers them as personal skills.

### Hooks system

Hooks are Node.js scripts bundled in `tai/hooks/`. `tai claude setup-hooks` merges them into `~/.claude/settings.json`, preserving any custom hooks the user already has. All tai hooks are prefixed with `[tai]` for identification and safe removal.

### Error handling

All errors inherit from `TaiError(message, hint)`. The `handle_error()` function prints a user-friendly message with an optional hint and exits with the appropriate code. Exit codes: 0 (success), 1 (error), 2 (usage), 3 (not found), 4 (permission denied), 5 (conflict).

### Plugin architecture

Third-party packages register a Typer app via `[project.entry-points."tai.plugins"]`. On startup, `main.py` iterates over discovered entry points and adds each as a command group.

## Data flow: linking a project

```
tai link
  │
  ├─ auth.get_access_token()     # Refresh if expired
  ├─ http.build_client(ctx)      # httpx with bearer token
  ├─ GET /api/notion/pages       # Fetch available pages
  ├─ prompt.search_select()      # Fuzzy picker (TTY) or plain list
  ├─ project.save_manifest()     # Write .tai.toml with notion_page_id
  └─ console.print("Linked!")
```

## Testing

Tests mirror the source structure: `tests/test_*.py` for core modules, `tests/commands/test_*_cmd.py` for commands. Coverage target: 80% (enforced by pytest-cov). External services are mocked with `respx` and `pytest-httpx`.
