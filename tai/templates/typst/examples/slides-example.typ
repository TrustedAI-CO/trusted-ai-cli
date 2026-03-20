// Example: TrustedAI Slides
#import "../slides.typ": *
#import "../theme.typ": tag

// ── Title slide ──────────────────────────────

#title-slide(
  title: "TrustedAI CLI",
  subtitle: "Ship Safer Software, Faster",
  author: "Thien Nguyen",
  institution: "TrustedAI Co., Ltd.",
  date: "March 2026",
)

// ── Section: Problem ─────────────────────────

#section-slide("The Problem")

#content-slide(
  title: "AI Safety Is an Afterthought",
  footer-text: "TrustedAI",
  slide-number: 2,
  total-slides: 8,
)[
  Most teams bolt on safety checks *after* deployment:

  - Security audits happen quarterly, not continuously
  - Model evaluations run in isolation from dev workflow
  - Safety documentation is manual and quickly outdated

  #callout(title: "The cost", color: rgb("dc2626"))[
    67% of AI incidents in 2025 could have been caught
    with automated pre-deployment checks.
  ]
]

// ── Section: Solution ────────────────────────

#section-slide("Our Solution")

#two-col-slide(
  title: "Integrated Safety Tooling",
  footer-text: "TrustedAI",
  slide-number: 4,
  total-slides: 8,
)[
  *Developer experience first:*

  - One command: `tai review`
  - Runs in CI/CD pipelines
  - Catches issues before merge
  - Zero-config for common frameworks

  #tag("Open Source")
  #tag("CLI-first")
][
  ```bash
  # Install
  pip install tai-cli

  # Link to your project
  tai project link

  # Run safety review
  tai review --scope all

  # Ship with confidence
  tai ship
  ```
]

// ── Standout ─────────────────────────────────

#standout-slide[
  "Move fast and *don't* break things."
]

// ── Section: Roadmap ─────────────────────────

#content-slide(
  title: "2026 Roadmap",
  footer-text: "TrustedAI",
  slide-number: 6,
  total-slides: 8,
)[
  #grid(
    columns: (1fr, 1fr),
    gutter: 1.5cm,
    [
      === Q1 — Foundation
      - CLI core & auth #tag("Done", color: rgb("16a34a"))
      - Notion integration #tag("Done", color: rgb("16a34a"))
      - Claude Code skills #tag("Done", color: rgb("16a34a"))
    ],
    [
      === Q2 — Scale
      - AI chat completions #tag("In Progress", color: rgb("d97706"))
      - Team dashboards
      - Plugin marketplace
    ],
  )
]

#content-slide(
  title: "Thank You",
  footer-text: "TrustedAI",
  slide-number: 8,
  total-slides: 8,
)[
  #align(center + horizon)[
    #text(size: 28pt, weight: "bold", fill: color-primary)[
      Let's build safer AI together.
    ]
    #v(1em)
    #text(size: 16pt, fill: color-text-muted)[
      thien\@trustedai.co · github.com/TrustedAI-CO
    ]
  ]
]
