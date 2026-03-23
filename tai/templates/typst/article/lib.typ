// TrustedAI Article — lib.typ
// Entry point for `tai pdf compile --template article`.
// Exposes `template(body, ..)` for the markdown wrapper.

#import "../theme.typ": *
#import "../article.typ": article as _article

#let template(
  body,
  company-name: "TrustedAI",
  title: none,
  subtitle: none,
  author: none,
  organization: none,
  date: datetime.today().display("[month repr:long] [day], [year]"),
  version: none,
  show-logo: true,
) = {
  _article(
    title: if title != none { title } else { company-name },
    subtitle: subtitle,
    author: if author != none { author } else { "" },
    organization: organization,
    date: date,
    version: version,
    show-logo: show-logo,
    body,
  )
}
