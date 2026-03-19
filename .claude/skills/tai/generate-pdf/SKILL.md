---
name: generate-pdf
version: 1.0.0
description: |
  [TAI] Generate branded PDF from Markdown using Typst templates. Writes .md content,
  then compiles to PDF via `tai pdf compile`. Agent-friendly document generation.
allowed-tools:
  - Read
  - Write
  - Edit
  - Bash
  - Grep
  - Glob
---

# /generate-pdf — Branded PDF Generation

Generate a professional, company-branded PDF document from Markdown content.

## How it works

1. Write content as a Markdown file
2. Compile to PDF using `tai pdf compile` with a company template
3. The template applies branding (logo, colors, headers, footers) automatically

## Prerequisites

- **Typst** must be installed: `brew install typst` (or `cargo install typst-cli`)
- **Templates** must be installed: `tai pdf setup-templates`

## Available templates

Check installed templates:
```bash
tai pdf setup-templates --list
```

Current templates:
- **proposal** — Client-facing proposal with executive summary, problem/solution, timeline, pricing
- **report** — Technical report with abstract, methodology, results, discussion, conclusion

## Usage

### Step 1: Write Markdown content

Create a `.md` file with the document content. Use standard Markdown:
- `# Heading 1` for main sections
- `## Heading 2` for subsections
- Regular paragraphs, lists, tables, code blocks all supported

### Step 2: Compile to PDF

```bash
# With a template (branded output):
tai pdf compile document.md --template proposal

# Without template (plain output):
tai pdf compile document.md

# Direct Typst file:
tai pdf compile document.typ

# Custom output path:
tai pdf compile document.md --template report --output final-report.pdf

# Debug mode (keeps intermediate .typ file):
tai pdf compile document.md --template proposal --debug
```

## Workflow for agents

When asked to create a document (proposal, report, etc.):

1. Create the markdown content file with appropriate sections
2. Run `tai pdf compile <file.md> --template <template-name>`
3. The PDF is generated in the same directory

## Template structure

Each template follows the Typst package format:
```
template-name/
  typst.toml          # Package manifest (name, version)
  lib.typ             # Styling function (layout, fonts, colors)
  template/
    main.typ           # Scaffold document for direct Typst editing
```

## Brand assets

Brand assets (logo, colors, company name) are installed alongside templates
at `~/.config/tai/brand/`. Templates automatically use these for consistent
branding across all document types.

## Troubleshooting

- **"Typst not found"** — Install Typst: `brew install typst`
- **"Template not found"** — Run `tai pdf setup-templates`
- **Compilation error** — Check the Typst stderr output in the error hint. Use `--debug` to inspect the intermediate `.typ` file.
- **First run slow** — Typst downloads the `cmarker` package on first use (requires internet).
