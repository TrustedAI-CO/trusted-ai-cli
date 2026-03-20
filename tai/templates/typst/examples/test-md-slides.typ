// Simulates what `tai pdf compile test-slides.md --template slides` generates
#import "../slides/lib.typ": *

#let company-name = "TrustedAI"
#let company-icon = "/Users/dizzyvn/conductor/workspaces/trusted-ai-cli/vienna/tai/templates/typst/brand/icon.png"
#let company-logo = "/Users/dizzyvn/conductor/workspaces/trusted-ai-cli/vienna/tai/templates/typst/brand/logo.png"
#let company-banner = "/Users/dizzyvn/conductor/workspaces/trusted-ai-cli/vienna/tai/templates/typst/brand/banner.png"
#let _strip-frontmatter(s) = {
  let m = s.match(regex("(?s)\\A---\\s*\\n.+?\\n---\\s*\\n"))
  if m != none { s.slice(m.end) } else { s }
}

#render-slides(_strip-frontmatter(read("test-slides.md")), company-name: company-name, icon: company-icon, logo: company-logo, banner: company-banner, title: "TrustedAI CLI", subtitle: "Ship Safer Software, Faster", author: "Thien Nguyen", date: "March 2026", institution: "TrustedAI Co., Ltd.")
