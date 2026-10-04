# Agent instructions

This repository turns a written script into a rendered explainer video. If someone asks you to make a video
from a topic or a draft, this is the whole job.

## The four commands

```bash
bash tools/doctor.sh                                              # prerequisites, installs nothing
export GEMINI_API_KEY=...                                         # the one thing the user brings
python3 tools/tts.py <script.txt> <piece>/assets/voice            # one continuous take, boundaries measured
python3 templates/composition-generator.py <piece> [--vertical]   # one beat per paragraph
cd <piece> && npm run check && npm run render
python3 tools/verify.py <piece>/renders/*.mp4 <word-count>        # check the file, not the project
```

## What you write

- `<piece>/script.txt`: **one paragraph per beat, plain text.** The paragraph count sets the beat count. Keep
  paragraphs short: a paragraph becomes one caption line.
- Do not hand-write timings. `tools/tts.py` measures them from the take and writes `timings.json`, and the
  generator places every beat from that file. Re-record the voice and the beats move with it.

## Rules that are not optional

- **One continuous take.** Never per-line clips. Per-line clips with gaps read as a slide deck.
- **Measure the take, never trust the pace.** The same script comes back at different speeds between calls.
  Compare `wpm` against the target, then use `tools/retime.py <vo-dir> <seconds>` if it is off.
- **Check the finished file.** `npm run check` validates the project; `tools/verify.py` reads the mp4. A project
  can pass its own check and the file still be wrong.
- **Never publish without a person approving it.** Upload unlisted, then read the video back from the API.

Write all prose, commit messages and replies to the standard in `STYLE.md`. Use the ASD-STE100 rules there:
short sentences, active voice, one term per thing, and keep the uncertainty.
