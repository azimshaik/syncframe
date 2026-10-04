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
| `tools/tts.py` | One continuous narration take from a script, with the sentence boundaries measured by snapping word positions to the pauses the speaker actually took |
| `tools/retime.py` | Correct a take to a target pace and rescale every boundary with it |
| `tools/verify.py` | Check the finished file: pace, dead air, and whether the lines survived the mix |
| `templates/composition-generator.py` | A beat-timed composition generator: a dark canvas, drawn-on shapes, an opacity ladder, and the framework contract already satisfied |

## Requirements

- Python 3.10+, `ffmpeg` and `ffprobe`
- Node 20+ and a headless-browser renderer for the composition. The template targets
  [HyperFrames](https://hyperframes.heygen.com) (`npx hyperframes`), an HTML/GSAP video renderer; the
  composition pattern is portable to any renderer that can seek a timeline and capture frames.
- A TTS provider. The tools default to Gemini TTS, which has a usable free tier; any provider that returns
  one continuous take works.
- Optional: `xcode-select --install` if you want Manim for the diagram-led style. Manim needs a C compiler,
  because pycairo ships no macOS wheel.

## Quick start

```bash
# 1. a script, one sentence per line
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

## Licence

MIT, see `LICENSE`. The method is the point, so use it, fork it and change the beats.
