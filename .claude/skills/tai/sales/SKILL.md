---
name: sales
version: 1.0.0
description: |
  [TAI] Sales pipeline management for Hnavi (発注ナビ) and Aimitsu (アイミツ).
  View jobs, track negotiations, send messages, and submit entries on Japanese
  B2B lead platforms. Use when asked to "check sales leads", "view jobs",
  "send a message to a client", or "manage negotiations".
allowed-tools:
  - Bash
  - Read
---

# tai Sales Pipeline

Manage sales leads and negotiations on Japanese B2B platforms:

- **Hnavi (発注ナビ)** — Development/IT outsourcing lead platform
- **Aimitsu (アイミツ)** — PRONI supplier matching service

## Prerequisites

### 1. Install Playwright

The sales command uses browser automation. Install the optional dependency:

```bash
pip install 'trusted-ai-cli[sales]'
playwright install chromium
```

### 2. Set Credentials

Set environment variables for each platform:

```bash
# Hnavi credentials
export HNAVI_EMAIL="your-email@example.com"
export HNAVI_PASSWORD="your-password"

# Aimitsu credentials
export AIMITSU_EMAIL="your-email@example.com"
export AIMITSU_PASSWORD="your-password"
```

## Command Reference

### Top-Level Commands

```bash
tai sales status          # Summary of both platforms (jobs, negotiations, projects)
tai sales status --json   # JSON output

tai sales login           # Test login to both platforms
tai sales login --visible # Show browser window for debugging
```

### Hnavi Commands

#### List/View Jobs

```bash
tai sales hnavi                          # Show summary (job + negotiation counts)
tai sales hnavi jobs                     # List all available jobs
tai sales hnavi jobs --json              # JSON output
tai sales hnavi jobs --category AI       # Filter by category (AI, システム, ホームページ, etc.)
tai sales hnavi jobs --saas              # Include SaaS tab jobs
tai sales hnavi jobs <job_id>            # Show job details (URL ID or display No.)
tai sales hnavi jobs 202604030016        # Example: show job by display number
```

Job fields: id, title, budget, deadline, tags, url.

Detail fields: no, status, deadline, category, title, max_companies, company_size,
company_location, has_website, entry_conditions, inquiry_content, hearing_content.

#### Active Negotiations

```bash
tai sales hnavi active                   # List active negotiations
tai sales hnavi active --json            # JSON output
tai sales hnavi active <neg_id>          # Show negotiation details + messages
```

Negotiation fields: id, title, company, status, last_message_date, url.

#### Send Messages

```bash
tai sales hnavi send <neg_id> "message"          # Send message
tai sales hnavi send <neg_id> "message" -f file  # Attach a file
tai sales hnavi send <neg_id> "message" --visible # Show browser
```

#### Submit Entry (Interactive)

```bash
tai sales hnavi entry <job_id>           # Interactive entry submission
tai sales hnavi entry <job_id> --visible # Show browser
tai sales hnavi entry <job_id> --yes     # Skip confirmation prompt
```

**Note:** The entry command requires an interactive TTY. It prompts for:

1. Answers to entry requirement questions
2. Self-introduction text
3. Team member selection
4. Confirmation before submission

### Aimitsu Commands

#### List Projects

```bash
tai sales aimitsu                        # Show summary (project count)
tai sales aimitsu list                   # List projects in negotiation
tai sales aimitsu list --json            # JSON output
```

Project fields: no, title, customer, status, url.

#### View Project Details

```bash
tai sales aimitsu show <project_no>      # Show project details + messages
tai sales aimitsu show <project_no> --json
```

Detail fields: no, url, customer, request_date, inquiry_no, title, background,
details, system_details, required_features, target_users, current_issues,
budget, budget_certainty, delivery, schedule, meeting_method, contact_hours,
preferred_times, messages.

#### Send Messages

```bash
tai sales aimitsu send <project_no> "message"
tai sales aimitsu send <project_no> "message" -f file
tai sales aimitsu send <project_no> "message" --visible
```

## Non-Interactive Usage (Inside Claude Code)

Claude Code's Bash tool is **not** an interactive TTY. Commands that require
prompts will fail. The entry command specifically requires interaction.

Commands that work inside Claude Code:

```bash
# Status checks
tai sales status --json

# Hnavi
tai sales hnavi jobs --json
tai sales hnavi jobs <job_id> --json
tai sales hnavi active --json
tai sales hnavi active <neg_id> --json

# Aimitsu
tai sales aimitsu list --json
tai sales aimitsu show <project_no> --json
```

For `tai sales hnavi entry`, tell the user to run it in their terminal.

## Workflow Examples

### Daily Pipeline Check

```bash
# Get overview
tai sales status --json

# Check new Hnavi jobs
tai sales hnavi jobs --json

# Review specific job
tai sales hnavi jobs 15995 --json
```

### Filter Jobs by Category

```bash
# AI/ML projects
tai sales hnavi jobs --category AI --json

# System development
tai sales hnavi jobs --category システム --json

# Website projects
tai sales hnavi jobs --category ホームページ --json
```

### Follow Up on Negotiations

```bash
# List active negotiations
tai sales hnavi active --json

# Read messages in a negotiation
tai sales hnavi active 12345 --json

# Send a follow-up (if approved by user)
tai sales hnavi send 12345 "ご連絡ありがとうございます。..."
```

### Aimitsu Project Management

```bash
# List projects
tai sales aimitsu list --json

# Get project details
tai sales aimitsu show 67890 --json

# Reply to customer
tai sales aimitsu send 67890 "お問い合わせありがとうございます。..."
```

## JSON Output Shapes

### Hnavi Job List

```json
[
  {
    "id": "202604030016",
    "title": "AIチャットボット開発",
    "budget": null,
    "deadline": "2026年4月6日 17:00",
    "tags": ["AI"],
    "url": "https://developer.hnavi.co.jp/jobs/15995"
  }
]
```

### Hnavi Job Details

```json
{
  "url_id": "15995",
  "url": "https://developer.hnavi.co.jp/jobs/15995",
  "no": "202604030016",
  "status": "募集中",
  "deadline": "2026年4月6日 17:00",
  "category": "AI",
  "title": "AIチャットボット開発",
  "max_companies": "10社",
  "company_size": "50〜100名",
  "company_location": "東京都",
  "has_website": "有り",
  "entry_conditions": ["条件1", "条件2"],
  "inquiry_content": "問い合わせ内容...",
  "hearing_content": "ヒアリング内容..."
}
```

### Aimitsu Project List

```json
[
  {
    "no": "12345",
    "title": "ECサイト構築",
    "customer": "株式会社〇〇 山田様",
    "status": "商談中",
    "url": "https://imitsu.jp/mypage/supplier/competitions/12345"
  }
]
```

### Aimitsu Project Details

```json
{
  "no": "12345",
  "url": "https://imitsu.jp/mypage/supplier/competitions/12345",
  "customer": "山田様",
  "request_date": "2026年4月1日",
  "inquiry_no": "98765",
  "title": "ECサイト構築",
  "background": "既存サイトのリニューアル...",
  "budget": "500万円〜1000万円",
  "delivery": "2026年6月末",
  "meeting_method": "オンライン",
  "messages": [
    {
      "sender": "株式会社〇〇 山田太郎",
      "content": "お世話になっております...",
      "date": "2026年4月2日 14:30"
    }
  ]
}
```

## Troubleshooting

### Login Failed

```
Error: Hnavi login failed. Check credentials.
```

Verify environment variables are set correctly:

```bash
echo $HNAVI_EMAIL
echo $AIMITSU_EMAIL
```

### Playwright Not Installed

```
Error: Playwright is not installed.
Install with: pip install 'trusted-ai-cli[sales]' && playwright install chromium
```

Run the suggested installation command.

### Entry Button Not Found

```
Error: Entry button not found. Job may be closed or already entered.
```

The job may have reached its company limit or you've already submitted an entry.

### Debugging with Visible Browser

Add `--visible` to any command to watch the browser automation:

```bash
tai sales hnavi jobs --visible
tai sales aimitsu show 12345 --visible
```
