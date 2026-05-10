---
name: vastai-quick-gpu-clean
version: 1.0.0
description: |
  [TAI] Tear down a vast.ai instance provisioned by `vastai-quick-gpu`.
  Destroys the instance, removes the SSH config block, deletes the
  generated SSH key, and removes the local state file. Use when asked
  to "shut down the GPU", "kill the vast box", "clean up vastai", or
  "stop billing".
allowed-tools:
  - AskUserQuestion
  - Bash
---

# vast.ai quick-GPU teardown

You are destroying a vast.ai instance the user previously provisioned via
`vastai-quick-gpu`. The underlying CLI is `tai vastai down`. **You should
confirm before destroying** — the box and everything on it disappears.

## Step 1 — List what exists

```bash
tai vastai list --json
```

If the list is empty, tell the user "nothing to clean up" and stop.

## Step 2 — Decide which alias(es)

If only one alias exists, target it.

If multiple exist, ask the user which one (or `--all`). Use AskUserQuestion
with the alias names as options.

## Step 3 — Confirm with the user

Show what will happen:

- Instance `<id>` will be **destroyed** (data lost permanently)
- SSH config block `vastai-<alias>` removed from `~/.ssh/config`
- SSH key `~/.ssh/vastai_<alias>_ed25519` deleted (unless `--keep-key`)
- Local state file deleted

Confirm before running. Don't pass `--yes` until the user explicitly
confirms.

## Step 4 — Tear down

```bash
tai vastai down <alias> --yes --json
# or
tai vastai down --all --yes --json
```

If anything on the server (uncommitted code, datasets) hasn't been
mirrored back, **stop the user** and offer to rsync it down first:

```bash
rsync -az vastai-<alias>:/root/<repo>/ /Users/jack/Documents/Dev/<repo>/backup-<date>/
```

## Step 5 — Confirm cleanup

Print the JSON output's `removed` array and tell the user billing has
stopped for those instance ids.
