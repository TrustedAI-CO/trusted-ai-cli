# Template: Changelog Entry

Concise, user-facing release notes. The reader is scanning quickly — make every
line earn its place.

## Structure

### Version Header
Format: `## [X.Y.Z] - YYYY-MM-DD`

### Sections (use only what applies)
Order by user impact, highest first:

#### Added
New features and capabilities. Lead with what the user can now DO.
- **{Feature name}** — {what it does in one sentence}

#### Changed
Behavior changes in existing features. Highlight what's different.
- **{What changed}** — {old behavior} → {new behavior}

#### Fixed
Bug fixes. Describe the symptom the user saw, not the internal cause.
- Fix {symptom the user experienced} ({context if needed})

#### Removed
Features or capabilities that no longer exist. Include migration guidance.
- Removed {thing} — use {alternative} instead

#### For Contributors (optional)
Internal changes relevant to developers working on the project.
- {Change} — {why it matters for contributors}

## Writing Rules
- User-facing language: "You can now..." not "Refactored the internal..."
- One line per change. If you need more, the feature deserves its own announcement.
- Concrete over abstract: "Reduced CLI startup from 1.2s to 0.3s" not "Improved performance"
- Don't list every commit — group related changes into meaningful entries.
- Every entry should pass the "so what?" test. If the user wouldn't care, cut it.
- For git-aware mode: read the actual git log and PR descriptions, then translate
  each meaningful change into user-facing language.
