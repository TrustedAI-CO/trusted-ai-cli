// Example: TrustedAI Article
#import "../article.typ": *
#import "../theme.typ": blockquote, tag, highlight-text

#show: article.with(
  title: "Partnership Proposal",
  subtitle: "AI Safety Collaboration",
  author: "Thien Nguyen",
  date: "March 19, 2026",
)

= Background

TrustedAI has been building developer tools that integrate safety checks
directly into the software development lifecycle. We believe combining
our practical engineering experience with research expertise could
accelerate adoption of safety practices across the industry.

= Proposed Collaboration

We propose collaboration in three areas:

+ *Evaluation frameworks* — standardized benchmarks for measuring
  model safety across common deployment scenarios.

+ *Developer tooling* — CLI and IDE integrations that surface safety
  metrics during the development process, not just in post-deployment
  audits.

+ *Open datasets* — curated datasets for red-team testing that can be
  shared across the research community.

#blockquote[
  _"Our goal is to make safety checks as natural as running tests —
  integrated into every developer's workflow, not bolted on after the fact."_
]

= Expected Outcomes

- Shared evaluation framework published as open-source #tag("Q3 2026")
- Joint research paper on developer-facing safety tooling #tag("Q4 2026")
- Community benchmark dataset with 10k+ test cases #tag("2027")

= Next Steps

We would welcome the opportunity to discuss this proposal further.
Our team is available for a call at your convenience. Reach out at
#highlight-text[dev\@trusted-ai.co].
