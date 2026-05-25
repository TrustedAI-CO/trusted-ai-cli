---
name: hub
version: 1.0.0
description: |
  [TAI] Workspace hub manager. Search, create, and update projects, pages, tasks,
  files, meetings, email, and calendar via `tai hub` CLI. Use when asked to "check
  tasks", "create a page", "search the workspace", "list projects", "upload a file",
  "link a meeting", "check my calendar", "search email", or any workspace management.
allowed-tools:
  - Bash
  - Read
  - AskUserQuestion
---

## Hub Workspace Manager

You manage the TrustedAI Hub workspace through the `tai hub` CLI. Always use
`--json` when you need to parse output programmatically. Use plain output when
showing results to the user.

## Prerequisites

User must be logged in: `tai login`. If you get "Not authenticated" or "Hub session
expired", tell the user to run `tai login`.

## Command Reference

### Global

```bash
tai hub search <query>              # search pages, tasks, projects
tai hub projects                    # list all projects (shows ID, name, status)
tai hub summary                     # workspace overview with task counts
```

### Pages (default: wiki, --private for private, -p for project)

```bash
tai hub page                        # list wiki pages
tai hub page --private              # list private pages
tai hub page -p <id-prefix>         # list project pages
tai hub page get <uuid>             # read page content
tai hub page create <title>         # create in wiki (default)
tai hub page create <title> -p <id> # create in project
tai hub page create <title> --private  # create in private space
tai hub page update <uuid> <content>   # update page content
tai hub page rename <uuid> <new-title> # rename page
```

### Tasks (project-scoped, use -p)

```bash
tai hub task -p <id-prefix>                    # list tasks
tai hub task -p <id> --status todo             # filter by status
tai hub task create <title> -p <id>            # create task
tai hub task create <title> -p <id> --priority high --due 2026-06-01
tai hub task update <#number-or-uuid> -p <id> --status done
tai hub task update <#number-or-uuid> -p <id> --title "New title"
```

Task status values: `todo`, `in-progress`, `review`, `done`
Priority values: `low`, `medium`, `high`
Reference tasks by `#number` (e.g. `#42`) or full UUID.

### Members & Milestones

```bash
tai hub members -p <id-prefix>      # list project members (shows user IDs)
tai hub milestones -p <id-prefix>   # list milestones with progress
tai hub deliverables <#num-or-uuid> -p <id>  # task deliverables
tai hub comment task <#num-or-uuid> "message" -p <id>  # add comment to task
tai hub comment page <uuid> "message"                   # add comment to page
```

### Files (Google Drive, project-scoped)

```bash
tai hub file -p <id-prefix>                    # list files in root folder
tai hub file -p <id> --folder <folder-id>      # browse subfolder
tai hub file search <query> -p <id>            # search by name
tai hub file upload <local-path> -p <id>       # upload file
tai hub file upload <path> -p <id> --folder <folder-id>  # upload to subfolder
tai hub file download <file-id> -p <id>        # download to cwd
tai hub file download <file-id> -p <id> -o /path/to/save
tai hub file delete <file-id> -p <id>          # delete file
```

### Meetings (link calendar events to projects)

```bash
tai hub meeting -p <id-prefix>                 # list linked meetings
tai hub meeting link <event-id> -p <id>        # link calendar event (auto-fetches details)
tai hub meeting unlink <meeting-uuid>          # unlink meeting
```

To get event IDs, use `tai hub cal --json` first.

### Email (Gmail)

```bash
tai hub email                                  # list recent threads
tai hub email -q "from:client subject:contract"  # search with Gmail syntax
tai hub email read <thread-id>                 # read full thread
tai hub email drafts                           # list drafts
tai hub email compose <to> <subject> <body>    # create draft (not sent)
tai hub email compose <to> <subject> <body> --cc <cc>
tai hub email send <to> <subject> <body>       # send email
tai hub email reply-context <message-id>       # get reply headers
tai hub email reply-context <message-id> --all # reply-all context
```

### Calendar

```bash
tai hub cal                                    # next 7 days
tai hub cal --from 2026-06-01T00:00:00Z --to 2026-06-07T00:00:00Z
tai hub cal create <title> <start-iso> <end-iso>
tai hub cal create <title> <start> <end> --desc "Notes" --location "Office"
tai hub cal create <title> <start> <end> --all-day --tz Asia/Tokyo
tai hub cal update <event-id> --title "New title" --start <iso>
tai hub cal rsvp <event-id> accepted           # or: declined, tentative
```

## --project / -p Flag

`-p` accepts a project **ID or UUID prefix** (not name). Use `tai hub projects` first
to see IDs, then copy the prefix.

```bash
# Get project IDs
tai hub projects
# Output:
#   Name                  Status      Repos
#   OCR Technical Draw    active          0    ← ID: a816cfcd-...

# Use prefix
tai hub task -p a816c
```

If `-p` is omitted and you're in an interactive terminal, a picker appears.
In non-interactive mode (scripts, agents), `-p` is required.

## JSON Output

All commands support `--json` for machine-readable output. Use this when you need
to parse results programmatically:

```bash
# Get project ID programmatically
PROJECT_ID=$(tai hub projects --json | jq -r '.[0].id')

# Get task IDs
tai hub task -p $PROJECT_ID --json | jq '.[].id'

# Get calendar event IDs for meeting linking
EVENT_ID=$(tai hub cal --json | jq -r '.[0].id')
tai hub meeting link $EVENT_ID -p $PROJECT_ID
```

## Common Workflows

### Create a task and assign it
```bash
# 1. Find the project
tai hub projects --json | jq '.[] | select(.status=="active")'
# 2. List members to get user IDs
tai hub members -p <project-id> --json
# 3. Create task (assignees via API only, not CLI flags yet)
tai hub task create "Implement feature X" -p <project-id> --priority high --due 2026-06-15
```

### Search → Read → Reply email
```bash
# 1. Search
tai hub email -q "from:client is:unread"
# 2. Read thread
tai hub email read <thread-id>
# 3. Get reply context
tai hub email reply-context <message-id>
# 4. Compose reply draft
tai hub email compose <to> "Re: Subject" "Response body"
```

### Link a meeting to a project
```bash
# 1. Find upcoming events
tai hub cal --json | jq '.[].id, .[].summary'
# 2. Link to project
tai hub meeting link <event-id> -p <project-id>
```

## Error Handling

| Error | Meaning | Action |
|-------|---------|--------|
| "Not authenticated" | No login | Run `tai login` |
| "Hub session expired" | Token expired | Run `tai login` |
| "Cannot reach Hub" | Hub server down | Check hub URL in config |
| "No project matching ID prefix" | Bad -p value | Run `tai hub projects` to see IDs |
| "Permission denied" | No access | Check project membership |
| "Rate limit exceeded" | Too many requests | Wait 60 seconds |
