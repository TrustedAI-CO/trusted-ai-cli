# AI-Slop Patterns

Phrases and patterns that signal generic, low-effort AI writing. When detected in a draft,
these should be flagged and rewritten with specific, concrete language.

## Categories

### Filler Openers
These phrases add zero information. Cut them entirely or replace with the actual point.

- "In today's fast-paced world"
- "In the ever-evolving landscape of"
- "In this article, we will explore"
- "In this blog post, we'll look at"
- "Let's dive in"
- "Let's dive deep into"
- "Without further ado"
- "As we all know"
- "It goes without saying"
- "It's no secret that"
- "It's worth noting that"
- "It's important to note that"
- "It's important to understand that"
- "Needless to say"

### Vague Intensifiers
These make claims feel big without evidence. Replace with specific numbers or examples.

- "incredibly powerful"
- "extremely useful"
- "very important"
- "truly remarkable"
- "absolutely essential"
- "game-changing"
- "groundbreaking"
- "cutting-edge"
- "state-of-the-art"
- "next-level"
- "world-class"
- "best-in-class"
- "industry-leading"

### Corporate Buzzwords
Replace with plain language that says what you actually mean.

- "leverage" → use
- "utilize" → use
- "optimize" → improve / speed up / reduce
- "streamline" → simplify
- "synergy" → working together
- "paradigm shift" → change
- "holistic approach" → considering everything
- "actionable insights" → useful findings
- "move the needle" → make a difference
- "low-hanging fruit" → easy wins
- "at the end of the day" → ultimately
- "circle back" → follow up
- "deep dive" → detailed look
- "drill down" → examine closely

### Unsupported Superlatives
Claims of extremes without evidence. Either add proof or soften to a factual claim.

- "the best way to"
- "the only solution that"
- "the most powerful"
- "the fastest"
- "the easiest"
- "the simplest"
- "the ultimate guide to"
- "everything you need to know"

### Over-Hedging
These undermine your own claims. Either commit to the statement or cut it.

- "It might be worth considering"
- "One could argue that"
- "It's possible that"
- "Perhaps it could be said"
- "This may or may not"
- "To some extent"
- "In some cases"
- "It depends on the situation"

### Hollow Conclusions
These restate the introduction without adding value. Replace with a specific call to action.

- "In conclusion"
- "To sum up"
- "In summary"
- "All in all"
- "At the end of the day"
- "As we've seen"
- "To wrap things up"

### AI-Specific Tells
Phrases that specifically signal AI-generated content.

- "Ah," (sentence opener — conversational filler)
- "Great question!"
- "That's a great point"
- "I hope this helps"
- "Happy to help"
- "Feel free to"
- "Don't hesitate to"
- "I'd be happy to"
- "Here's the thing:"
- Starting 3+ consecutive paragraphs with "The" or "This"

### Empty Transitions
Replace with transitions that actually connect ideas.

- "Furthermore"
- "Moreover"
- "Additionally"
- "In addition to this"
- "On the other hand" (when there's no actual contrast)
- "Having said that"
- "With that being said"
- "That said" (overused)
- "Interestingly"
- "Interestingly enough"

### Robotic Structure Signals
Patterns that reveal templated writing. Vary your structure.

- Numbered lists where bullets would work
- Every section starting with the same sentence pattern
- "There are N key things to consider:" followed by exactly N headers
- "First... Second... Third... Finally..." as the sole structural device
- Repeating the section title in the first sentence of every section

## Usage

When scanning a draft:
1. Check every sentence against these patterns
2. Flag exact matches AND close variants (e.g., "In our rapidly changing world" matches "In today's fast-paced world")
3. For each flag, provide a specific rewrite using concrete details from the content
4. Count flags per total sentences to compute slop score
5. Also check `~/.tai-skills/custom-slop-patterns.md` for user-defined additions
