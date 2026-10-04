# Writing style

The docs in this repo follow a plain technical style, guided by
[ASD-STE100](https://www.asd-ste100.org/) (Simplified Technical English). The prompt below is the whole
rule set. Paste it into whatever assistant you write with.

```text
Use ASD-STE100 as a guide for your responses. Write short sentences, use active voice, and keep terminology
consistent. Relax the vocabulary rules when they make explanations awkward. Preserve technical precision and
uncertainty.
```

## How we apply it

- **One idea per sentence.** Aim under 20 words. Split a sentence before you nest a clause.
- **Active voice.** "The generator writes the timings", not "the timings are written by the generator".
- **One term per thing, everywhere.** A *take* stays a take. It does not become a recording, and then a clip.
- **Keep the hedges that carry information.** "Came back at 137, 160 and 171 words a minute across three calls"
  is more useful than "pacing is unreliable". Numbers and uncertainty stay in the sentence.
- **Relax the vocabulary rules before you write an awkward sentence.** The guide serves the reader. If a
  permitted word makes a sentence clumsy, use the clearer word.
- **Say what you did not verify.** If a claim comes from one machine, one repository, or one run, write that
  down next to the claim.

## Where it applies

Docs, commit messages, issue and pull-request replies, and the narration scripts that this method turns into
video. The last one matters most: a script written in this style is easier to voice, and the measured
boundaries land on cleaner sentence ends.
