# Writing style

Docs, replies and narration scripts in this repository use ASD-STE100 (Simplified Technical English) as a
guide. Paste this into the assistant you write with:

```text
Use ASD-STE100 as a guide for your responses. Write short sentences, use active voice, and keep terminology
consistent. Relax the vocabulary rules when they make explanations awkward. Preserve technical precision and
uncertainty.
```

## What the guide is

ASD-STE100 is a controlled-language standard. Work started in 1979, for aircraft maintenance. The current
specification is free at [asd-ste100.org](https://www.asd-ste100.org/). It has two parts:

- **Part 1, writing rules.** Nine sections: words, noun clusters, verbs, sentences, procedures, descriptive
  writing, safety instructions, punctuation and word counts, and writing practices.
- **Part 2, dictionary.** About 900 approved words. Each approved word has one meaning and one part of speech.
  Each unapproved word comes with an approved alternative.

The standard was written for maintenance procedures. We use it as a guide for prose, documentation and video
narration. That is why the relax clause in the prompt above matters.

## The limits

| Item | Limit |
|---|---|
| Procedural sentence | 20 words |
| Descriptive sentence | 25 words |
| Descriptive paragraph | 6 sentences, one topic |
| Noun cluster | 3 words |
| Instructions in one sentence | 1 |

Two practices from Part 1 that bite in practice:

- **Use the same word for the same thing every time.** A *take* does not become a recording later.
- **Do not put a comma before *and* or *or* in a series.**
- **Use the active voice in procedures.** "The generator writes the timings", not "the timings are written".
- **Use a vertical list when the text is complex.**

## Verbs

Use these forms: command form (`Close the valve`), simple present, simple past, simple future, infinitive, and
the past participle as an adjective (`the closed valve`).

Do not use these forms: the progressive (`is closing`), the perfect (`has closed`), or the passive in a
procedure (`must be closed`). Use the `-ing` form only as a technical noun, such as "landing gear".

## The dictionary, in practice

One word, one meaning, one part of speech. When a word is not approved, use its alternative:

| Not approved | Use instead |
|---|---|
| commence | START |
| ensure | MAKE SURE |
| prior to | BEFORE |
| replenish | FILL |
| utilize | USE |
| approximately | ABOUT |
| in order to | TO |
| close (adjective, meaning near) | NEAR |
| test (verb) | TEST (approved) |

Approved words appear in capitals in the standard. `close` is a verb only. It never means "near". These
examples come from the ASD-STE100 overview sheet; the dictionary in the specification is the authority.

## The narration rules (the 3b1b rule)

The 3Blue1Brown-style cut follows the method in `docs/HOW-THE-EXPLAINERS-ARE-MADE.md`. The rules that apply to
text and to the beats that carry it:

| Ingredient | Rule |
|---|---|
| captions | one key line per beat, never full subtitles |
| caption swaps | swap at one instant. Never crossfade two captions in the same slot |
| sentence length | short enough to draw, and short enough to read in one look |
| pacing | long beats, deliberate holds, no music |
| claims | every number on screen comes from a capture, a parsed file, or a named source, and the source is named on screen |

The STE limits and the caption rule agree. A 20-word sentence is about one caption line. That is not a
coincidence. Both keep one idea in front of the reader at a time.

## The two themes

The composition ships two palettes. Both use the same layout, the same grid and the same shapes. Only the
tokens change. The generator holds them in one place (`THEMES`) and writes them into the generated HTML as CSS
variables, so one change to a token changes every beat.

| Token | `dark` (default) | `bright` | What it paints |
|---|---|---|---|
| `bg` | `#1C1C1C` | `#FAFAF7` | the page |
| `ink` | `#ECECEC` | `#16181D` | captions and bar labels |
| `dim` | `#888888` | `#5C5C5C` | the counter, node labels, the corner label |
| `grid` | `#ECECEC` at 5% | `#16181D` at 6% | the background grid |
| `blue` | `#58C4DD` | `#1E7FA6` | the drawn shapes |
| `green` | `#83C167` | `#2F7D32` | this beat's node, the first bar |
| `yellow` | `#FFFF00` | `#A97B00` | the accent line |
| `muted` | `#3C3C3C` | `#BDBDB4` | the bars that are not the point |

The accents are darker in `bright` on purpose. `#58C4DD` and `#FFFF00` read well on a dark page and wash out
on a white one. Keep that rule when you add a token: pick the value against the background, then measure it.
`npm run check` reports contrast, and the bright theme passes all 25 text checks against WCAG AA.

## Where the rules bend

- **Relax the vocabulary before you write an awkward sentence.** When the approved word makes the sentence
  clumsy, use the clearer word. The guide serves the reader.
- **Keep technical precision.** Names from a specification, an API or a command line stay exactly as the tool
  spells them, even when the dictionary would prefer a simpler word.
- **Keep the uncertainty.** "Three calls came back at 137, 160 and 171 words a minute" is better than "pacing
  is unreliable", and better than a number that hides the spread. Write what you measured, and write what you
  did not verify next to the claim.

## Sources

- ASD-STE100, Simplified Technical English, free from [asd-ste100.org](https://www.asd-ste100.org/).
- `docs/HOW-THE-EXPLAINERS-ARE-MADE.md` in this repository: the narration, timing and visual rules, and the
  mistakes that cost the most time.
