// TrustedAI Article — lib.typ
// Entry point for `tai pdf compile --template article`.
// Exposes `template(body, ..)` for the markdown wrapper.

#import "../theme.typ": *
#import "../letter.typ": article as _article

#let template(
  body,
  company-name: "TrustedAI",
  icon: none,
  logo: none,
  banner: none,
  title: none,
  subtitle: none,
  author: none,
  date: datetime.today().display("[month repr:long] [day], [year]"),
) = {
  _article(
    title: if title != none { title } else { company-name },
    subtitle: subtitle,
    author: if author != none { author } else { "" },
    date: date,
    icon: icon,
    body,
  )
}
