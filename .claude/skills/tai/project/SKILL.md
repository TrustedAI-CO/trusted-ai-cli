---
name: project
version: 1.0.0
description: |
  [TAI] Project management: link repos to Notion, view status, manage tasks
  and meetings, open linked tools. Use when working with tai project workflows.
allowed-tools:
  - Bash
  - Read
---

# tai Project Management

Guides you through managing TrustedAI projects from the CLI. Projects live in
Notion and are linked to git repos via a `.tai.toml` manifest.

## Preamble — Check Prerequisites

Before running any project command, verify auth and link status:

```bash
# 1. Check authentication
tai whoami 2>&1 || echo "NOT_AUTHENTICATED"

# 2. Check project link
tai project status --json 2>&1 || echo "NOT_LINKED"
```

- If **NOT_AUTHENTICATED**: tell the user to run `tai login` in an interactive
  terminal first. This opens a browser for Google OAuth — it cannot run inside
  a Claude Code session.
- If **NOT_LINKED** (and step 1 passed): guide the user to run `tai link` in an
  interactive terminal to pick a Notion project, or use `tai project new` if they
  need to create one. Note: if step 1 failed, a step 2 failure is likely an auth
  issue, not a missing link.

## Command Reference

### Linking a Repo to a Project

Linking creates `.tai.toml` at the repo root with the Notion page ID.

| Command | What it does | Interactive? |
|---|---|---|
| `tai link` | Pick a project from the list and link this repo | Yes (TTY required) |
| `tai unlink` | Remove `.tai.toml` from the repo | No |
| `tai project new` | Create a new Notion project and link this repo | Yes (prompts for name, description, category) |

**Important:** `tai link` and `tai project new` require an interactive terminal.
They cannot run inside a Claude Code Bash tool. Tell the user to run them in
their own terminal.

### Viewing Project Status

```bash
tai project status            # human-readable table
tai project status --json     # machine-readable JSON
```

Output fields: Name, Notion URL, Status, Phase, GitHub, Drive, GChat.

JSON shape:
```json
{
  "name": "Project Name",
  "notion_page_id": "32-char-hex",
  "notion_url": "https://notion.so/...",
  "status": "Active",
  "phase": "In Progress",
  "github_repo": "https://github.com/...",
  "drive_folder": "https://drive.google.com/...",
  "gchat_space": "https://chat.google.com/...",
  "client": "Client Name"
}
```

### Opening Linked Tools

```bash
tai open github     # open GitHub repo in browser
tai open notion     # open Notion project page
tai open drive      # open Google Drive folder
tai open chat       # open Google Chat space
```

### Managing Tasks

Tasks are Notion database entries linked to the project.

```bash
# List tasks
tai tasks                        # table view
tai tasks --json                 # JSON array
tai tasks -q                     # one name per line (pipe-friendly)
tai tasks -a                     # across all projects
tai tasks -n 10                  # limit results
tai tasks -f "deploy"            # filter by name (case-insensitive)

# Create a task
tai tasks add                    # prompts for name (interactive)
tai tasks add --json             # JSON output

# Mark done
tai tasks done <short_id>        # by ID prefix — matches all tasks including Done
tai tasks done                   # interactive picker — shows open tasks only (TTY)
```

Task JSON shape:
```json
{
  "task_id": "32-char-hex",
  "short_id": "8-char-prefix",
  "name": "Write tests",
  "status": "In progress",
  "description": null,
  "due_date": null,
  "assignee": null
}
```

### Managing Meetings

Meetings are Notion entries scoped to the project (last 6 months).

```bash
# List meetings
tai meetings                     # interactive picker → opens in Notion (TTY)
tai meetings --json              # JSON array
tai meetings -q                  # one title per line
tai meetings -a                  # across all projects
tai meetings -n 5                # limit results
tai meetings -f "sprint"         # filter by title

# Create a meeting
tai meetings add                 # prompts for title, date, type (interactive)
tai meetings add --json          # JSON output
```

Meeting JSON shape:
```json
{
  "meeting_id": "32-char-hex",
  "short_id": "8-char-prefix",
  "title": "Sprint Planning",
  "date": "2026-03-20",
  "meeting_type": ["Project meeting"],
  "lead": null,
  "notion_url": "https://notion.so/..."
}
```

Meeting types: Colab, Sale meeting, External meeting, Project meeting, Review,
Team meeting.

## Non-Interactive Usage (Inside Claude Code)

Claude Code's Bash tool is **not** an interactive TTY. Commands that require
prompts (`tai link`, `tai project new`, `tai tasks add`, `tai meetings add`)
will fail. For these, tell the user to run the command in their terminal.

Commands that work inside Claude Code without interaction:

```bash
tai project status --json        # check project bindings
tai tasks --json                 # list all tasks as JSON
tai tasks -q                     # task names for quick reference
tai tasks -f "keyword" --json    # filtered task search
tai tasks done <short_id> --json # mark task done by ID
tai meetings --json              # list meetings
tai open github                  # opens browser on the user's machine
```

### Recommended Patterns for Agents

```bash
# Get open tasks only
tai tasks --json | jq '[.[] | select(.status != "Done")]'

# Get the next task to work on
tai tasks --json | jq '[.[] | select(.status != "Done")][0]'

# Check which tools are linked
tai project status --json | jq '{github: .github_repo, notion: .notion_url}'

# Get most recent meeting
tai meetings --json | jq '.[0]'
```

## Workflow Guide

### Starting Work on a Project

1. Check if the repo is linked: `tai project status --json`
2. If not linked, tell the user to run `tai link` in their terminal
3. Review open tasks: `tai tasks --json`
4. Pick a task and start working on it

### During Development

- Use `tai tasks --json` to check task status and find work items
- Use `tai open github` to quickly open the repo in the browser
- Use `tai open notion` to reference project documentation

### Completing Work

- Mark tasks done: `tai tasks done <short_id>`
- Check remaining work: `tai tasks -f "keyword" --json`

## Configuration

### Project Manifest (`.tai.toml`)

Located at the repo root. Created by `tai link` or `tai project new`.

```toml
[project]
notion_page = "2ef55eff03158039b95cf6e8ff60d632"
```

This file should be committed to the repo so all team members share the link.

### CLI Config

Location: `~/.config/tai/config.toml` (or `$TAI_CONFIG_PATH`).

```toml
current_profile = "default"

[profiles.default]
api_base_url = "https://api.trusted-ai.co"
```

Use `tai setup` for interactive configuration, or `tai config set <key> <value>`
for non-interactive changes.
