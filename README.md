# Explainers by narration timing

A method for making short explainer videos where the visuals land on the words, plus the parts of the
toolchain worth reusing. Written from building several of these, including the mistakes, because the mistakes
are the useful part.

## The idea

Record **one continuous narration take**. Measure where each sentence actually starts inside it. Build a
single HTML page on a seekable timeline where every beat is placed on those boundaries. Render it with a
headless browser. Then run the checks on the **rendered file**, not on the project, because a project can pass
and the file still be wrong.

No editor timeline, no keyframes by hand. The narration is the timing source, and re-recording the voice means
re-running a generator and re-rendering, not re-cutting.

## What is in here

| Path | What it is |
|---|---|
| `docs/HOW-THE-EXPLAINERS-ARE-MADE.md` | The whole method: nine stages with commands, the narration and timing rules, the visual rules, the verify gate, thumbnails, upload, and a symptom/cause/fix table of every mistake that cost time |
| `docs/HOW-A-PIECE-IS-BUILT.md` | The sequence for one piece: what you supply, what each stage produces, and the two gates that loop back. Mermaid, so it renders on GitHub |
| `tools/tts.py` | One continuous narration take from a script, with the sentence boundaries measured by snapping word positions to the pauses the speaker actually took |
| `tools/retime.py` | Correct a take to a target pace and rescale every boundary with it |
| `tools/verify.py` | Check the finished file: pace, dead air, and whether the lines survived the mix |
| `templates/composition-generator.py` | A beat-timed composition generator: a dark canvas, drawn-on shapes, an opacity ladder, and the framework contract already satisfied |
| `STYLE.md` | The writing style for docs, replies and narration scripts: the ASD-STE100 rules, the word limits, the approved verb forms, the dictionary substitutions, and the caption and pacing rules |
| `AGENTS.md` | Tells coding agents in this repository to follow `STYLE.md` |

## Worked example: the knowledge graph piece

Two cuts from one set of beats. The horizontal cut runs 3:08, the vertical cut runs 1:30, and both carry the
same narration plan.

- Horizontal: <https://youtu.be/xZbfV6jDHZ0>
- Vertical, 9:16: <https://youtu.be/yj1ANPtfq5o>

What that build measured, stage by stage:

| Stage | What the numbers were |
|---|---|
| Script | 593 words, one paragraph per beat, ten beats |
| One continuous take | 185.5 seconds, 192 words a minute, no per-line clips |
| Boundaries | ten beat starts, snapped to the pauses the voice took |
| Composition | one generated HTML file per cut: GSAP on a paused timeline, an SVG graph, and the voice as one audio element. 1920x1080, one idea per beat |
| Renderer | HyperFrames 0.8.117: `npx hyperframes check` first, then `npx hyperframes render`. 5,613 frames at 30 fps, hardware GPU |
| Verify, on the file | -15.0 LUFS, and nine sampled frames checked by eye |
| Deliver | uploaded unlisted, then read back from the API |

That build ran a project-local take tool and a timing filler, not the scripts in `tools/` by name. The steps
are the same ones this repository describes: one continuous take with boundaries snapped to real pauses, a
composition driven by those boundaries, and a check on the rendered file (loudness, and sampled frames). The
scripts here are the reusable form of those steps.

Three lessons from that build became rules:

1. **Roll more than one take.** The same 593-word script came back at 196 seconds (183 words a minute), 177
   seconds (201 words a minute) and 185.5 seconds (192 words a minute) across three calls. Keep the
   best-paced take instead of accepting the first one.
2. **Swap captions at one instant.** Two captions with a crossfade in the same slot print through each other
   and read as garbage. Swap them with a single set, which is what the 3Blue1Brown cuts do anyway.
3. **Check what the naive baseline reads.** An early measurement of the same tool reported a 92x token
   saving, by comparing the graph against reading the matched files for every question. That baseline claimed
   more tokens than the whole corpus holds, so it was wrong. The tool's own benchmark gives 5.4x on
   `psf/requests`: 78,600 tokens to read the corpus against 14,547 for an average query. The video and this
   repository use the second number, with the caveat spoken on screen.

## Requirements

- Python 3.10+, `ffmpeg` and `ffprobe`
- Node 20+ and a headless-browser renderer for the composition. The template targets
  [HyperFrames](https://hyperframes.heygen.com) (`npx hyperframes`), an HTML/GSAP video renderer; the
  composition pattern is portable to any renderer that can seek a timeline and capture frames.
- A TTS provider that returns **one continuous take**. Two are in use here: a cloned presenter voice for that
  person's own channel, and Gemini TTS (`gemini-2.5-flash-preview-tts`) for a product voice, which is what
  the knowledge graph cuts used.

## Quick start

```bash
# 1. a script, one paragraph per beat
$EDITOR script.txt

# 2. one continuous take, plus measured boundaries
GEMINI_API_KEY=... python3 tools/tts.py script.txt vo/

# 3. correct the pace if it came in slow or fast
python3 tools/retime.py vo/ 188

# 4. generate the composition from the boundaries
python3 templates/composition-generator.py ./my-project
cd my-project && npm run check && npm run render

# 5. verify the rendered file, not the project
python3 tools/verify.py out.mp4 194 "the first line" "the last line"
```

## The two numbers worth knowing before you start

- **Do not trust the pace you asked for.** The same text, same settings, same voice came back at 137, 160 and
  171 words a minute across three consecutive calls. Measure the take, then correct it.
- **Do not cut audio on estimated timings.** Word-proportional estimates drift by seconds. Before cutting or
  splicing, transcribe with timestamps and snap to real pauses; cutting on an estimate clipped a sentence and
  left the wrong take in the file, twice.

## What this is not

It is not a video editor, a template pack, or a product. There are no assets in here: no music, no fonts, no
footage, no voice models, and no credentials. Bring your own.

## Writing style

Docs, commit messages, issue replies and narration scripts follow `STYLE.md`. Short sentences, active voice,
one term per thing, and the hedges kept.

## Licence

MIT, see `LICENSE`. The method is the point, so use it, fork it and change the beats.
