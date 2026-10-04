# Gemini CLI and Antigravity

Read `AGENTS.md` first. It carries the whole job: the four commands, the script format, and the rules that are
not optional. `STYLE.md` carries the writing standard for anything you write here.

Short version: the user brings a key and a script (one paragraph per beat). Run `tools/doctor.sh`, then
`tools/tts.py`, then `templates/composition-generator.py`, then `npm run check && npm run render`, then
`tools/verify.py` on the mp4. Never hand-write timings, never publish without a person approving it.
