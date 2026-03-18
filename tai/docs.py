"""LLM-friendly usage documentation for the tai CLI."""

DOCS = """\
# tai — TrustedAI Internal CLI

tai is a cross-tool orchestrator for TrustedAI. It links git repositories to Notion
projects and provides structured access to tasks, meetings, and tool integrations.
All data is fetched from the TrustedAI API server, which proxies to Notion, GitHub,
and Google Workspace.

## Setup

```bash
tai login              # authenticate with Google (opens browser)
tai link               # link this repo to a Notion project (interactive picker)
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

### Project Linking

Requires a `.tai.toml` in the repo root (created by `tai link`).

```
tai link               # interactive: pick Notion project → writes .tai.toml
tai unlink             # remove .tai.toml
tai project new        # create a new Notion project and link this repo
tai project status     # show all tool bindings (Notion, GitHub, Drive, GChat)
tai project status --json
```

```
tai open github        # open linked GitHub repo in browser
tai open notion        # open linked Notion project page
tai open drive         # open linked Google Drive folder
tai open chat          # open linked Google Chat space
```

### Tasks

List and manage Notion tasks for the current project.

```
tai tasks                          # show task table (requires linked project)
tai tasks --json                   # → [{task_id, short_id, name, status, due_date, assignee}]
tai tasks -q                       # one task name per line (pipe-friendly)
tai tasks -a                       # all projects
tai tasks -n 10                    # limit to 10 results
tai tasks -f "deploy"              # filter by name (case-insensitive)
tai tasks -a -f "bug" --json       # combine flags

tai tasks add                      # prompt for name → create task
tai tasks add --json               # → {task_id, short_id, name, status}

tai tasks done <short_id>          # mark task as Done by ID prefix
tai tasks done                     # interactive picker (TTY only)
tai tasks done --json              # → {task_id, short_id, name, status: "Done"}
```

Task object shape:
```json
{
  "task_id": "aabbccdd11223344aabbccdd11223344",
  "short_id": "aabbccdd",
  "name": "Write tests",
  "status": "In progress",
  "description": null,
  "due_date": null,
  "assignee": null
}
```

### Meetings

List and manage Notion meetings. Only meetings from the last 6 months are returned.

```
tai meetings                       # interactive picker → opens Notion page (TTY)
                                   # non-TTY: prints plain list to stdout
tai meetings --json                # → [{meeting_id, short_id, title, date, notion_url}]
tai meetings -q                    # one meeting title per line
tai meetings -a                    # all projects
tai meetings -n 5                  # limit results
tai meetings -f "sprint"           # filter by title

tai meetings add                   # prompt for title, date, type → create meeting
tai meetings add --json            # → {meeting_id, short_id, title, date, notion_url}
```

Meeting object shape:
```json
{
  "meeting_id": "aabbccdd11223344aabbccdd11223344",
  "short_id": "aabbccdd",
  "title": "Sprint Planning",
  "date": "2026-03-20",
  "meeting_type": ["Project meeting"],
  "lead": null,
  "notion_url": "https://notion.so/aabbccdd11223344aabbccdd11223344"
}
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
tai claude setup-hooks             # install tai hooks into ~/.claude/settings.json
tai claude setup-hooks --list      # preview available hooks without installing
tai claude setup-hooks --remove    # remove tai-managed hooks
tai claude setup-hooks --json      # JSON output (for scripting)
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

## Non-Interactive Usage (Agents & CI)

tai detects whether stdin is a TTY. In non-interactive contexts:

- `tai tasks` — prints table as usual (no picker)
- `tai meetings` — prints plain list instead of launching picker
- `tai tasks done` (no ID) — exits with code 2; pass `<short_id>` explicitly
- `tai link` — exits with code 2; must be run in a real terminal

Recommended patterns for AI agents:

```bash
# Get all open tasks as JSON
tai tasks --json | jq '[.[] | select(.status != "Done")]'

# Get task names only
tai tasks -q

# Mark a specific task done
tai tasks done a1b2c3d4 --json

# List recent meetings
tai meetings --json | jq '.[0]'

# Check project bindings
tai project status --json
```

## Configuration File

Location: `~/.config/tai/config.toml` (or `$TAI_CONFIG_PATH`)

```toml
current_profile = "default"

[profiles.default]
api_base_url = "https://api.trusted-ai.co"
oauth_client_id = ""
company_domain = "trusted-ai.co"
```

## Project Manifest

Each linked repo has `.tai.toml` at the repo root:

```toml
[project]
notion_page = "2ef55eff03158039b95cf6e8ff60d632"
```
"""
