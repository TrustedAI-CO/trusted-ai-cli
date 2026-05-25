---
name: vastai-quick-gpu
version: 1.0.0
description: |
  [TAI] Provision a cheapest-match GPU box on vast.ai, sync the user's repo,
  install Claude Code / Codex / tai, and write an SSH config block so VS Code
  Remote-SSH "just works". Use when asked to "spin up a GPU", "give me a
  vastai box", "I need an H100 for an hour", or "sync my repo to a GPU server".
  For teardown, use `vastai-quick-gpu-clean`.
allowed-tools:
  - AskUserQuestion
  - Bash
  - Read
---

# vast.ai quick-GPU

You are setting up a temporary GPU dev box on vast.ai for the user. The
underlying CLI is `tai vastai up`. **All logic lives there** — your job is
to gather inputs, confirm, run it, and summarise the result.

## Step 1 — Preflight

Before anything else, verify:

```bash
command -v vastai
vastai show user --raw | head -c 200
```

If `vastai` is missing, tell the user: `pipx install vastai`. If `show
user` fails, tell them to run `vastai set api-key <KEY>` (key from
https://cloud.vast.ai/account/).

## Step 2 — Gather inputs (single AskUserQuestion turn)

Ask once, four questions:

1. **GPU model** — e.g. `RTX_5090`, `RTX_4090`, `H100`, `A100`. Spaces become underscores.
2. **Disk GB** — default 100. Ask if the user mentioned datasets / large checkpoints.
3. **Region** — `any` (default), `us`, `na`, `eu`, `asia`, or comma-separated country codes (`us,ca`).
4. **Repo paths** — absolute paths to sync. Multiple OK. If the user already named one, skip the question.
5. **Ignored files/dirs to also sync** — list paths inside the repo that are gitignored but the user actually needs (e.g. `data`, `.env`, `models`). Default: none.

Also pick an **alias** (default `quick-gpu`; `tai vastai up` auto-suffixes if taken).

If the user wants `.env`/`*.key`/`credentials.json` synced, warn once: "this puts secrets on a rented box — they'll be removed by `vastai-quick-gpu-clean`."

## Step 3 — Provision

Run with the gathered args. `--json` so you can parse the result:

```bash
tai vastai up \
  --gpu RTX_5090 \
  --disk 512 \
  --region us \
  --alias quick-gpu \
  --repo /Users/jack/Documents/Dev/some-repo \
  --include-ignored data \
  --include-ignored .env \
  --yes \
  --json
```

The `--yes` skips the price-confirmation prompt — only pass it after
**you** have shown the user the cheapest match and they've agreed. To get
the price preview without committing, run `vastai search offers` directly
and show the top hit; or omit `--yes` and let the user confirm in their
own terminal (preferred when running interactively).

## Step 4 — Tell the user how to connect

Parse the JSON output and surface the two ready-to-run lines:

- `ssh <ssh_alias>` for terminal access
- `code --remote ssh-remote+<ssh_alias> /root` for VS Code

Plus the instance id and hourly price so they know what's running.

## Common failure modes

- **No offers matched** — loosen disk/region/GPU. Tell the user the exact
  filter that returned zero results.
- **SSH never came up** — `vastai show instance <id>` to check status. May
  need to destroy and try a different host.
- **`git clone` over forwarded agent fails** — the user's local SSH agent
  might not have their GitHub key loaded. Tell them to run `ssh-add` and
  re-run with the same alias (the `tai vastai up` flow is idempotent on
  the SSH config side; instance creation is not, so prefer fixing the
  agent first).

## What gets installed on the box

`tai vastai up` runs a remote bootstrap script that installs:

- `uv` (Astral's Python toolchain)
- `trusted-ai-cli` via `uv tool install`
- `@anthropic-ai/claude-code` and `@openai/codex` via npm
- All `tai-*` skills for Claude Code and Codex (`tai claude/codex setup-skills`)

It also copies `~/.claude/.credentials.json` and `~/.codex/auth.json` (if
present locally) so the user can run `claude` and `codex` on the box
without a fresh OAuth dance. Tell the user this happened.

---
**Self-Improvement Rule:** If you run into a blocker, find a solution — then update this skill file so future runs don't hit the same issue.
