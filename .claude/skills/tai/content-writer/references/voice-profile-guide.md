# Voice Profile Guide

A voice profile captures a brand's or author's writing style so content stays consistent
across pieces and sessions. Profiles are stored in `~/.tai-skills/voice-profiles/`.

## Profile Format

```markdown
---
name: {profile-name}
created: {YYYY-MM-DD}
source: {what this was extracted from — e.g., "3 blog posts from acme.com/blog"}
---

# Voice Profile: {Name}

## Tone
{One sentence describing the overall tone: casual, authoritative, playful, etc.}

## Sentence Style
- Average length: {short / medium / long} ({N}-{N} words)
- Structure preference: {simple / compound / varied}
- Rhythm: {punchy and staccato / flowing and connected / mixed}

## Vocabulary
- Level: {casual / conversational / technical / academic}
- Jargon policy: {use freely / explain on first use / avoid}
- Contractions: {yes / no / sometimes}

## Perspective
- Person: {first singular (I) / first plural (we) / second (you) / third}
- Formality: {informal / semi-formal / formal}

## Signature Patterns
{2-5 distinctive patterns that make this voice recognizable. Examples:}
- Opens posts with a provocative question
- Uses analogies from cooking/sports/music to explain technical concepts
- Ends sections with a one-sentence paragraph for emphasis
- Favors em-dashes over parentheses
- Occasionally addresses the reader directly: "Here's the deal."

## Anti-Patterns
{Things this voice specifically avoids:}
- Never uses "leverage" or "utilize"
- Avoids numbered lists — prefers prose with subheadings
- Never opens with "In this article"
- Avoids passive voice except in technical specifications

## Example Snippets
{2-3 short excerpts that exemplify this voice at its best. Real quotes from source material.}

> "{Example 1}"

> "{Example 2}"
```

## Creating a Voice Profile

### From existing content (recommended)

1. Ask the user for 2-3 pieces of content that represent their ideal voice
2. Read each piece carefully
3. Analyze for the dimensions listed above
4. Write the profile to `~/.tai-skills/voice-profiles/{name}.md`
5. Show the profile to the user for approval before saving

### From description

1. Ask the user to describe their desired voice in plain language
2. Ask for 2-3 writers or publications they admire
3. Synthesize a profile from the description
4. Show the profile to the user for approval

### From scratch during writing

1. Write the first draft in a neutral tone
2. Ask the user to mark 2-3 sentences they love and 2-3 they don't
3. Infer the voice from the preference signal
4. Offer to save as a profile for future use

## Using a Voice Profile

When a voice profile is loaded:
- Match the tone, sentence style, and vocabulary exactly
- Follow the signature patterns — these are what make the voice distinctive
- Avoid the anti-patterns — these are dealbreakers
- Read the example snippets before drafting to internalize the rhythm
- The profile is a guide, not a cage — adapt to the content type while maintaining
  the core voice characteristics
