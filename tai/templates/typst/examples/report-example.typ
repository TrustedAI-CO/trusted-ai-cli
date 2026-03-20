// Example: TrustedAI Full Report
#import "../report.typ": *
#import "../theme.typ": blockquote, tag, highlight-text

#show: full-report.with(
  title: "Quarterly Security Audit",
  subtitle: "Infrastructure & Application Review",
  author: "TrustedAI Engineering",
  organization: "TrustedAI Co., Ltd.",
  date: "March 19, 2026",
  version: "1.0",
)

= Executive Summary

Our quarterly audit covered #highlight-text[42 services] across production
and staging environments. Key metrics:

- *Critical findings:* 3 (all resolved)
- *High findings:* 7 (5 resolved, 2 in progress)
- *Compliance score:* 94% #tag("PASSING", color: rgb("16a34a"))

#blockquote[
  _"The team's response time improved 40% compared to Q4 2025,
  with average remediation under 48 hours."_
]

= Methodology

== Scope

The audit covered the following areas:

+ Authentication and authorization flows
+ Data encryption at rest and in transit
+ Network segmentation and firewall rules
+ Dependency vulnerability scanning
+ Access control and privilege escalation

== Tools Used

We used a combination of automated scanning and manual review:

```bash
# Example: dependency audit
tai secret scan --scope production
trivy image --severity HIGH,CRITICAL app:latest
```

= Findings

== Critical: Exposed API Keys in Logs

#tag("CRITICAL") #tag("RESOLVED", color: rgb("16a34a"))

Application logs contained unredacted API keys in request headers.
Immediate remediation applied via log sanitization middleware.

== High: Outdated TLS Configuration

#tag("HIGH") #tag("IN PROGRESS", color: rgb("d97706"))

Several internal services still negotiate TLS 1.1 connections.
Migration to TLS 1.3 is scheduled for completion by end of Q2.

= Recommendations

+ Implement automated secret scanning in CI pipeline
+ Enforce TLS 1.3 minimum across all internal services
+ Add quarterly access review for privileged accounts
+ Deploy runtime application self-protection (RASP)

= Appendix

Detailed scan results and evidence are available in the
internal security dashboard.
