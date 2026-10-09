# Agent instructions

This repository turns a written script into a rendered explainer video. If someone asks you to make a video
from a topic or a draft, this is the whole job.

## The commands

```bash
bash tools/doctor.sh                                              # prerequisites, installs nothing
export GEMINI_API_KEY=...                                         # the free key, for the default engine
python3 tools/tts.py <script.txt> <piece>/assets/voice            # one continuous take, boundaries measured
python3 templates/composition-generator.py <piece> --motifs graph,steps,bars,basic   # one beat per paragraph
cd <piece> && npm run check && npm run render
python3 tools/verify.py <piece>/renders/*.mp4 <word-count>        # check the file, not the project
```

Flags that change the output:

- `--vertical` on the generator: 1080x1920 instead of 1920x1080.
- `--theme bright` on the generator: the same layout on a light page. `dark` is the default.
- `--motifs a,b,c` on the generator: the packs, cycled across the beats. `basic` draws plain shapes,
  `graph` draws a node per paragraph, `bars` needs digits in the paragraph, `steps` needs two sentences.
  A pack with nothing to work from falls back to `basic` for that beat, and the tool prints what it used.
- `--engine elevenlabs` on the tts tool: a voice of your own, a clone included, instead of the Gemini
  stock voice. It reads `ELEVENLABS_API_KEY` and `EL_VOICE_ID` from the environment or `./.env`.
  `--check-quota` reports the character quota without spending any, and `--dry-run` prints what would be
  sent. **Never print, echo or commit a key**, and never write one into a script, a composition or a
  message. The tool masks what it prints; keep that property if you edit it.

## What you write

- `<piece>/script.txt`: **one paragraph per beat, plain text.** The paragraph count sets the beat count. Keep
  paragraphs short: the first sentence of a paragraph becomes the caption.
- Do not hand-write timings. `tools/tts.py` measures them from the take and writes `timings.json`, and the
  generator places every beat from that file. Re-record the voice and the beats move with it.
- If asked for a voice of your own, use the ElevenLabs engine and check the quota before a re-record.
  A 401 from ElevenLabs means a bad key or an exhausted quota, and one 3 minute piece costs about
  3,300 characters.

## Rules that are not optional

- **One continuous take.** Never per-line clips. Per-line clips with gaps read as a slide deck.
- **One caption line per beat.** The generator takes the first sentence of the paragraph for this. A caption
  of four or five lines reads as a subtitle dump and fails the narration rules in `STYLE.md`.
- **Measure the take, never trust the pace.** The same script comes back at different speeds between calls.
  Compare `wpm` against the target, then use `tools/retime.py <vo-dir> <seconds>` if it is off.
- **Check the finished file.** `npm run check` validates the project; `tools/verify.py` reads the mp4. A project
  can pass its own check and the file still be wrong.
- **Never publish without a person approving it.** Upload unlisted, then read the video back from the API.

Write all prose, commit messages and replies to the standard in `STYLE.md`. Use the ASD-STE100 rules there:
short sentences, active voice, one term per thing, and keep the uncertainty.
