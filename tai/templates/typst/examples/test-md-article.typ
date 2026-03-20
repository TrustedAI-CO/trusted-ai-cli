// Simulates what `tai pdf compile test-article.md --template article` generates
// with frontmatter: title, subtitle, author, date
#import "../article/lib.typ": *

#let company-name = "TrustedAI"
#let company-icon = "/Users/dizzyvn/conductor/workspaces/trusted-ai-cli/vienna/tai/templates/typst/brand/icon.png"
#let company-logo = "/Users/dizzyvn/conductor/workspaces/trusted-ai-cli/vienna/tai/templates/typst/brand/logo.png"
#let company-banner = "/Users/dizzyvn/conductor/workspaces/trusted-ai-cli/vienna/tai/templates/typst/brand/banner.png"
#let _strip-frontmatter(s) = {
  let m = s.match(regex("(?s)\\A---\\s*\\n.+?\\n---\\s*\\n"))
  if m != none { s.slice(m.end) } else { s }
}

#show: doc => template(doc, company-name: company-name, icon: company-icon, logo: company-logo, banner: company-banner, title: "Partnership Proposal", subtitle: "AI Safety Collaboration", author: "Thien Nguyen", date: "March 2026")

#{  import "@preview/cmarker:0.1.8"
   cmarker.render(_strip-frontmatter(read("test-article.md")), smart-punctuation: true)
}
