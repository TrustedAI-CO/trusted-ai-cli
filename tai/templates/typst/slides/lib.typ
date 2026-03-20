// TrustedAI Slides — lib.typ
// Entry point for `tai pdf compile --template slides`.
// Supports markdown with `---` as slide separators.
// The first `# heading` in each section becomes the slide title.

#import "../theme.typ": *
#import "../slides.typ": *

// For backwards compat: simple single-slide template
#let template(
  body,
  company-name: "TrustedAI",
  logo: none,
  title: none,
  subtitle: none,
  author: none,
  date: datetime.today().display("[month repr:long] [day], [year]"),
  institution: none,
) = {
  let resolved-logo = if logo != none { logo } else { "brand/logo.png" }
  content-slide(
    title: if title != none { title } else { company-name },
    footer-text: company-name,
    logo: resolved-logo,
  )[
    #set text(font: font-body, size: 18pt, fill: color-text)
    #set par(leading: 0.7em)
    #set list(indent: 0.8em, marker: move(dy: 0.11cm, square(width: 0.4em, height: 0.4em, fill: color-primary)), spacing: 0.8em)
    #show link: it => underline(text(fill: tai-blue, it))
    #body
  ]
}

/// Render markdown string as multiple slides, split on `---`.
/// First `# heading` per section becomes the slide title.
#let render-slides(
  md-string,
  company-name: "TrustedAI",
  logo: none,
  title: none,
  subtitle: none,
  author: none,
  date: datetime.today().display("[month repr:long] [day], [year]"),
  institution: none,
) = {
  import "@preview/cmarker:0.1.8"

  let resolved-logo = if logo != none { logo } else { "brand/logo.png" }

  // Title slide from frontmatter params
  title-slide(
    title: if title != none { title } else { company-name },
    subtitle: subtitle,
    author: if author != none { author } else { "" },
    date: date,
    institution: institution,
  )

  // Split on --- (horizontal rule) as slide separator
  let sections = md-string.split(regex("\n---+\s*\n"))

  let slide-count = sections.len() + 1  // +1 for title slide
  let slide-num = 1

  for section in sections {
    let section = section.trim()
    if section == "" { continue }

    // Extract title from first # heading
    let slide-title = ""
    let slide-body = section

    let heading-match = section.match(regex("#\\s+(.+)"))
    if heading-match != none {
      slide-title = heading-match.captures.at(0)
      // Remove the heading from body so it's not rendered twice
      slide-body = section.slice(heading-match.end).trim()
    }

    slide-num = slide-num + 1

    content-slide(
      title: slide-title,
      footer-text: company-name,
      logo: resolved-logo,
      slide-number: slide-num,
      total-slides: slide-count,
    )[
      #set text(font: font-body, size: 18pt, fill: color-text)
      #set par(leading: 0.7em)
      #set list(indent: 0.8em, marker: move(dy: 0.11cm, square(width: 0.4em, height: 0.4em, fill: color-primary)), spacing: 0.8em)
      #set enum(indent: 0.8em, spacing: 0.8em)
      #show heading.where(level: 1): set text(size: 0pt)
      #show heading.where(level: 2): set text(font: font-title, size: 20pt, fill: color-primary, weight: "semibold")
      #show heading.where(level: 3): set text(font: font-title, size: 17pt, fill: color-primary, weight: "medium")
      #show heading: it => { it + v(0.3em) }
      #show link: it => underline(text(fill: tai-blue, it))
      #cmarker.render(slide-body, smart-punctuation: true)
    ]
  }
}
