# How the explainer videos are made

The practical process, start to finish: the working method, the commands, and the mistakes that cost time.

Written 2026-10-03, from the first explainers and the knowledge graph pieces. The worked example in the README
is the knowledge graph cut, and its script ships in `examples/`.

---

## The whole idea in one paragraph

Record **one continuous narration take**. Measure where each sentence starts inside that take. Build a single
HTML page on a seekable timeline where every beat is placed **on those boundaries**, so the visuals land on
the words. Render it with a headless browser. Then run checks **on the rendered file**, not on the project,
because the project can be right while the file is wrong.

Nine stages, in order:

```
[1] DATA     source real data        ->  series.json            (only if the piece makes a claim)
[2] VOICE    one continuous take     ->  assets/voice/vo.wav
[3] TIMING   measure sentence starts ->  assets/voice/timings.json
[4] COMPOSE  build the page         ->  index.html              (beats placed on the timings)
[5] MIX      carve music under voice ->  (skip entirely if the cut is music-free)
[6] QA       lint + overlap + contrast
[7] RENDER   headless browser        ->  1920x1080, 30fps, h264 + AAC
[8] VERIFY   checks on the rendered file
[9] DELIVER  thumbnail, upload, read back from the API
```

---

## Stage by stage, with the actual commands

### [2] Voice

One take, never per-line clips. Six clips with 2.2 second gaps read as a slide deck and cost 11 seconds of
dead air in a 36 second piece. This was measured, not guessed.

Two engines, chosen by what the video is for:

- **A cloned presenter voice**, for that person's own channel: ElevenLabs `eleven_v3` with the clone's id in
  `EL_VOICE_ID` from the environment. `tools/tts.py --engine elevenlabs` drives it, and it writes the same
  `timings.json`, so nothing downstream changes. Check the monthly character quota **before** planning a
  re-record; it is 40,000 on the entry plan and one explainer uses a few thousand. `--check-quota` reads the
  quota without spending any of it, and `--dry-run` prints exactly what would be sent. An over-quota account
  answers with **401**, which is the same answer as a bad key.
- **A product voice**, for product pieces: Gemini TTS `gemini-2.5-flash-preview-tts`, one continuous read.

The direction line matters more than the voice. The "sleepy and uninterested" note came from a direction that
literally said "no emphasis, no excitement". The version that fixed it says: warm, quick, interested, pitch
moving, slow on the important words, not flat, not salesy. Do not ask a newer Gemini model for a direction it
will read aloud.

### [3] Timing, and the two traps

Measure the take. Never trust the pace you asked for: the same text, same settings, same voice returned
**137, 160 and 171 words per minute** on three consecutive calls. So:

```bash
# duration and pace
ffprobe -v error -show_entries format=duration -of csv=p=0 vo.wav
# every pause, to snap sentence starts onto real speech
ffmpeg -hide_banner -i vo.wav -af silencedetect=noise=-32dB:d=0.12 -f null - 2>&1 | grep silence_end
```

Then: estimated start = word position, **snapped** to the nearest detected pause within 0.7s. That is good
enough for placing beats, and it is not good enough for cutting audio.

**Trap one: the estimates drift.** Word-proportional timings assume even pacing and this voice does not have
it. In one piece the file said a line started at 135.5s when the audio had it at 138s. Cutting on an estimate
took out half of the previous sentence and left the wrong line in the audio.

**Trap two: the fix is to measure, not estimate.** Before any cut or splice, transcribe the region with
timestamps, read where the line actually starts, and snap that to the nearest pause. The splice that finally
worked used anchors read off the audio (138.0s and 144.0s) instead of estimates (135.5s and 142.6s). Two
wasted renders came from skipping this.

Pace correction, when the take comes in slow:

```bash
ffmpeg -i vo.wav -filter:a atempo=1.095 -ac 1 -ar 44100 vo-fast.wav
```

A tempo change scales every time in the take by a constant, so **multiply every beat boundary by the same
factor**. Do not re-measure. Target 185 to 190 words per minute.

### [4] Compose

One HTML file, GSAP on a paused timeline, beats as elements with `data-start` and `data-duration`. The
narration is one `<audio>` element in the page, so the render carries the voice.

Framework contract, which its own linter enforces:

- the root needs `data-composition-id`, `data-width`, `data-height`
- register one paused timeline on `window.__timelines` under that same id
- **no `querySelector` with a template literal**; the bundler's CSS parser crashes on it. Collect element
  references into variables at build time and animate those.
- every timed visual element gets `class="clip"`

Visual rules that have earned their place:

- **one idea per beat**, one number moving if a number is the point
- **opacity layering**: focus at 1.0, context at 0.4, structure at 0.15. The dimmed state is what makes the
  bright state mean something
- monospace throughout; proportional fonts kern badly in this renderer
- deliberate holds. Pauses are not dead air when they are doing work
- draw shapes on rather than cutting to them: animate `stroke-dashoffset` from the path length to zero
- teases and holds land better than a flat explanation, when the piece has a payoff to hold back

### [6] QA before rendering

```bash
npm run check     # lint, layout overlap, motion, WCAG contrast
```

Fix errors, read the warnings. A contrast warning during a fade-in is usually harmless; the same warning on a
static element is not.

### [7] Render

```bash
npm run render    # 1920x1080, 30fps, h264 + AAC
```

A vector-only piece renders in about two and a half minutes. Pieces using real footage take 15 to 25 minutes.

### [8] Verify, on the finished file

This gate is not optional, and it is what catches the errors the project cannot show you:

```bash
ffprobe -v error -select_streams v:0 -show_entries stream=width,height,r_frame_rate,nb_frames -of csv=p=0 out.mp4
ffmpeg -hide_banner -i out.mp4 -af ebur128=framelog=quiet -f null - 2>&1 | grep -E "I:|LRA:"
ffmpeg -hide_banner -i out.mp4 -af silencedetect=noise=-32dB:d=0.6 -f null - 2>&1 | grep -c silence_start
```

Then transcribe the video's own audio and check the lines are present, in order, and not repeated. Then look
at frames with your own eyes at three or four moments, including the ends of beats where collisions show up.

The transcription is also the honest judge of the read. It has called the same voice "energetic" and "flat" on
different pieces, so treat it as a signal about that take, not about the voice in general.

### [9] Deliver

- **Thumbnail from the film itself**, or from the presenter's own photo. Never a stock image. If the frame you want
  has the subject too small in a 1080p field, crop the artwork out at full resolution and recompose it at
  thumbnail scale, which is what the 3Blue1Brown thumbnail does.
- **Check the thumbnail by looking at it**, and specifically check that the words promise only what the video
  delivers. One thumbnail said "and how to build one" while the video did not build one; that had to be
  changed.
- **Upload unlisted** through the official API, then **read it back**: title, privacy, duration, tags,
  thumbnail sizes. Trust the read-back, not the upload command's own success message.
- Tags sometimes come back empty on the first write and stick on a second pass. Read back, retry once.
- YouTube cannot swap a file in place. Replacing an upload means delete and re-upload, and a new URL.

---

## Claims: the rule that has cost the most

**A sentence that describes how something works must come from something you actually ran.** A "how to set one
up" section in one video listed tree-sitter, networkx, kuzu, neo4j, Louvain, Leiden, PageRank, CodeQL and
Sourcegraph as though we had used them. We had not. We installed one tool and ran three commands. That section
was cut from the video, at the cost of 56 seconds of finished narration, and the tool's own name was corrected
from "ours" to the third-party project it actually is.

Two rules came out of it:

1. Name what you ran, and cut anything you did not.
2. Every number on screen comes from a capture, a parsed file, or a named primary source, and the source is
   named on screen. If you cannot source it, leave the number out rather than approximate it.

---

## The 3Blue1Brown variant

Requested as "a 3b1b style explainer". Manim is the honest tool for that, but it needs pycairo, and pycairo
ships no macOS wheel, so it has to be built, which needs a working C compiler. Without the command line
tools installed, meson reports no usable compiler. `xcode-select --install` fixes it (one click, ~1.5GB).

The look was reproduced on the same HTML/GSAP pipeline instead:

| Ingredient | Implementation |
|---|---|
| dark canvas | `#1C1C1C`, faint grid at 5 percent |
| palette | `#58C4DD` structure, `#83C167` resolved, `#FFFF00` the open question |
| type | monospace throughout, one key line per beat, never full subtitles |
| drawn on | `stroke-dashoffset` from path length to zero |
| depth of focus | sealed contents at 0.15, context at 0.3, focus at 1.0 |
| pacing | long beats, deliberate holds, no music |

Result: 1 minute 13, vector-only, rendered in 2.5 minutes rather than an hour.

---

## The mistakes, as a table

| Symptom | Cause | Fix |
|---|---|---|
| Read sounds sleepy or flat | the direction said "no emphasis" | warm, quick, pitch moving, slow on key words |
| Dead air, piece feels like slides | per-line clips with inserted gaps | one continuous take |
| Beats land after the words | trusting the requested pace | measure the take, correct with atempo, rescale all boundaries |
| A cut removes half a sentence, or repeats a clause | cutting on estimated timings | transcribe with timestamps, anchor on real pauses |
| Render fails its own lint | missing composition id, template-literal selector | set the data attributes, animate element references |
| Boxes read as houses | body outline drawn without the lid line | add the lid path |
| Thumbnail unreadable in a feed | using a raw 1080p frame with a small subject | crop the artwork at full resolution, recompose at 1280x720 |
| Thumbnail promises content that is not in the film | wrote the card before the cut was final | re-check the card against the finished file |
| Tags empty after upload | API write did not stick | read back, retry once |
| A false claim ships | describing tools that were never run | every sentence from something actually executed, or it is cut |

---

## Starting a new one

```bash
npx --yes hyperframes@latest init <piece>               # scaffold, pins a CLI version
# write plan.md first: what misconception it corrects, what the aha is, the beat list
# write <piece>/script.txt: one paragraph per beat
python3 tools/tts.py <piece>/script.txt <piece>/assets/voice
python3 templates/composition-generator.py <piece>      # add --vertical for the 9:16 cut
cd <piece> && npm run check && npm run render
python3 tools/verify.py <piece>/renders/*.mp4 <word-count>
# then the thumbnail, then the upload and the read-back
```

Project layout:

```
<piece>/
  plan.md                 narrative plan, written before any code
  README.md               what the piece is, the beats, the caveats
  <project>/index.html    the composition
  <project>/assets/       voice, footage, fonts
  out/                    the deliverable, the thumbnail, the web encode
```

Reusable scripts live in `tools/`: `tts.py` (one take, plus boundaries measured against real pauses),
`retime.py` (pace correction, every boundary rescaled), and `verify.py` (the check on the finished file, not
on the project). The composition generator is `templates/composition-generator.py`.
