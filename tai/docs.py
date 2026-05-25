"""LLM-friendly usage documentation for the tai CLI."""

DOCS = """\
# tai — TrustedAI Internal CLI

tai is a cross-tool orchestrator for TrustedAI. It provides AI tools, API access,
secret management, and hub-based project workflows.

## Setup

```bash
tai login              # authenticate with Google (opens browser)
```

## Global Options

These must come BEFORE the subcommand:

| Flag | Description |
|------|-------------|
| `--profile, -p` | Config profile to use (dev/staging/prod). Env: TAI_PROFILE |
| `--verbose, -v` | Verbose/debug output |
| `--json` | Global JSON output (or use --json on each subcommand directly) |
| `--version` | Show version and exit |
| `--docs` | Print this documentation and exit |

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | General error |
| 2 | Usage error (bad arguments) or non-interactive context |
| 3 | Resource not found (API 404) |
| 4 | Permission denied (API 403) |
| 5 | Conflict / ambiguous ID (API 409) |

## Commands

### Authentication

```
tai login              # sign in with Google (opens browser)
tai logout             # revoke credentials
tai whoami             # show currently logged-in account
tai whoami --json      # → {"email": "...", "profile": "..."}
```

### Config

```
tai config list                    # show all config values for current profile
tai config get <key>               # get a single value
tai config set <key> <value>       # set a value
tai config list-profiles           # list available profiles
tai config switch-profile <name>   # switch active profile
```

### Secrets

Secrets are stored in the system keychain, scoped to the active profile.

```
tai secret list                    # list all secret names
tai secret get <name>              # get secret value
tai secret set <name> <value>      # store a secret
tai secret delete <name>           # delete (prompts confirmation; -f to skip)
tai secret rotate <name>           # update an existing secret value
tai secret exec -- <cmd> [args]    # run a command with secrets injected as env vars
```

### Claude Code

```
tai claude login                   # authenticate Claude Code with Anthropic
tai claude logout                  # sign out Claude Code
tai claude status                  # show Claude Code auth status
tai claude setup-skills            # install tai skills into ~/.claude/skills
tai claude setup-hooks             # install tai hooks into ~/.claude/settings.json
tai claude setup-hooks --list      # preview available hooks without installing
tai claude setup-hooks --remove    # remove tai-managed hooks
tai claude setup-hooks --json      # JSON output (for scripting)
```


### Codex

```
tai codex status                   # show Codex binary, skills, and AGENTS.md status
tai codex status --json            # machine-readable Codex setup status
tai codex setup-skills --force     # install tai skills into ~/.codex/skills
tai codex setup-agents             # create a tai-managed AGENTS.md in this repo
tai codex setup-agents --force     # replace an unmanaged AGENTS.md intentionally
```

### AI / API

```
tai ai chat "<prompt>"             # one-shot chat with Claude
tai ai complete "<prompt>"         # text completion
tai ai models                      # list available models

tai api call <path>                # call the TrustedAI API
tai api call <path> -X POST -d '{"key": "value"}'
tai api endpoints                  # list all API endpoints
```

### Sales

Manage sales pipelines on Hnavi (発注ナビ) and Aimitsu (アイミツ) platforms.
Requires `playwright` extra: `pip install 'trusted-ai-cli[sales]'`

```
tai sales status                   # show summary of both platforms
tai sales login                    # test login to both platforms

# Hnavi (発注ナビ)
tai sales hnavi                    # show hnavi summary
tai sales hnavi jobs               # list all available jobs
tai sales hnavi jobs -c AI         # filter by category (AI, システム, ホームページ, etc.)
tai sales hnavi jobs --saas        # include SaaS tab jobs
tai sales hnavi jobs <id>          # show job details
tai sales hnavi entry <id>         # submit entry for job (interactive)
tai sales hnavi entry <id> -y      # submit entry (skip confirmation)
tai sales hnavi active             # list active negotiations
tai sales hnavi active <id>        # show negotiation details + messages
tai sales hnavi send <id> "msg"    # send message to negotiation
tai sales hnavi send <id> "msg" --file path  # with attachment

# Aimitsu (アイミツ)
tai sales aimitsu                  # show aimitsu summary
tai sales aimitsu list             # list projects in negotiation
tai sales aimitsu show <no>        # show project details
tai sales aimitsu send <no> "msg"  # send message to project
```

Environment variables for credentials:
- `HNAVI_EMAIL`, `HNAVI_PASSWORD`
- `AIMITSU_EMAIL`, `AIMITSU_PASSWORD`

Options:
- `--visible` — show browser window (default: headless)
- `--json` — output as JSON

## Configuration File

Location: `~/.config/tai/config.toml` (or `$TAI_CONFIG_PATH`)

```toml
current_profile = "default"

[profiles.default]
api_base_url = "https://api.trusted-ai.co"
oauth_client_id = ""
company_domain = "trusted-ai.co"
```

"""
