// TrustedAI Full Report — lib.typ
// Entry point for `tai pdf compile --template report`.
// Exposes `template(body, ..)` for the markdown wrapper.

#import "../theme.typ": *
#import "../report.typ": full-report as _full-report

#let template(
  body,
  company-name: "TrustedAI",
  title: none,
  subtitle: none,
  author: none,
  organization: none,
  date: datetime.today().display("[month repr:long] [day], [year]"),
  version: none,
) = {
  _full-report(
    title: if title != none { title } else { company-name + " Report" },
    subtitle: subtitle,
    author: if author != none { author } else { company-name },
    organization: organization,
    date: date,
    version: version,
    body,
  )
}
