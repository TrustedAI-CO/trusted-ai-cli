---
id: prd
type: prd
parent: null
children: []
related: []
status: draft
---

# tai CLI — Product Intent

> **Owner: HUMAN.** Product intent (L0). Agents may quote, never rewrite. Seeded from
> the legacy `docs.old/intent.html` on migration to the markdown framework.

## Problem
TrustedAI team members juggle multiple tools, APIs, and manual processes —
authentication, document generation, secret management, AI workflows each need
separate setup and context switching.

## Who it's for
The TrustedAI team (internal developer tool).

## Goal & success metric
A single CLI that centralizes the team's daily workflows.
- All team members use `tai` for daily workflows.
- Zero manual secret handling — everything goes through the keystore.
- Claude Code skills installable with one command.

## Scope
**In:** Google OAuth auth, profile-based config, secret management
(keychain/file/env), Typst PDF generation, Claude Code skill/hook management, Hub
workspace API, AI-assisted workflows, a plugin architecture for extensibility.
**Out:** non-team / public distribution; replacing existing product surfaces.

## How it works (rough)
A Typer-based CLI (`tai <group> <command>`) over a shared core (auth, config, http,
keystore, updater). Command groups live one-per-file under `tai/commands/`; bundled
data (skills, templates, brand assets) ships in `tai/data/`.

## Open questions / risks
- Migrated from HTML docs (`docs.old/`) to the markdown document-driven framework.
