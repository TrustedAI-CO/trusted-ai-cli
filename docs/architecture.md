---
id: architecture
type: architecture
parent: null
children: [0001-markdown-docs, SPEC-dashboard-render, SPEC-dashboard-serve, 0002-dashboard-web-stack, SPEC-docs-query, SPEC-gates-view, SPEC-gates-action, SPEC-dashboard-ui]
related: [prd]
derived: true
---

> ⚠️ Derived doc — maintained live by an agent as code changes; may still lag. Source of truth is `docs/specs/` + `docs/prd.md`. Regenerate, don't hand-edit as canon.

# Architecture — tai CLI

C4 Context + Container. Code level is read from source, not drawn here.

## 1. Context

```mermaid
C4Context
    title System Context — tai CLI
    Person(dev, "TrustedAI developer", "Runs tai in the terminal")
    System(tai, "tai CLI", "Unified team developer CLI")
    System_Ext(google, "Google OAuth", "Identity (PKCE, id_token)")
    System_Ext(hub, "Hub API", "Workspace: projects, pages, tasks, files")
    System_Ext(gh, "GitHub Releases", "Self-update wheel distribution")

    Rel(dev, tai, "Runs commands", "shell")
    Rel(tai, google, "Authenticates", "OAuth PKCE")
    Rel(tai, hub, "Reads/writes workspace", "HTTPS + id_token")
    Rel(tai, gh, "Checks/downloads updates", "HTTPS")
```

## 2. Container

```mermaid
C4Container
    title Container diagram — tai CLI
    Person(dev, "Developer")
    System_Boundary(c1, "tai CLI") {
        Container(entry, "Entry / Typer app", "Python / Typer", "main.py assembles command groups")
        Container(cmds, "Command groups", "Python", "one module per group under tai/commands/")
        Container(core, "Core library", "Python", "auth, config, http, keystore, updater, errors")
        Container(data, "Bundled data", "files", "skills, templates, brand assets")
    }
    Rel(dev, entry, "Invokes", "tai <group> <cmd>")
    Rel(entry, cmds, "Dispatches to")
    Rel(cmds, core, "Uses")
    Rel(cmds, data, "Reads bundled assets")
```

## 4. Container → code mapping

| Element | Code | Notes |
|---------|------|-------|
| Entry / Typer app | [`tai/main.py`](../tai/main.py) | entry point `tai.main:cli` |
| Command groups | [`tai/commands/`](../tai/commands) | one module per group |
| Core library | [`tai/core/`](../tai/core) | auth, config, http, keystore, updater, errors |
| Bundled data | [`tai/data/`](../tai/data) | skills, templates, brand assets |
| Hooks | [`tai/hooks/`](../tai/hooks) | Claude Code hooks |
| Plugins | [`tai/plugins/`](../tai/plugins) | entry-point plugin discovery |

## 5. Key decisions
- [0001-markdown-docs](decisions/0001-markdown-docs.md) — markdown document-driven framework (supersedes the legacy HTML docs).
