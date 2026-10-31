# Claude Code

Read `AGENTS.md` first. It carries the whole job: the four commands, the script format, and the rules that are
not optional. `STYLE.md` carries the writing standard for anything you write here.

Short version: the user brings a key and a script (one paragraph per beat). Use `python3` on macOS and Linux,
or `py -3` in Windows PowerShell. Run `tools/doctor.py`, then `tools/tts.py`, then
`templates/composition-generator.py`, then `npm run check` and `npm run render`, then `tools/verify.py` on
the mp4. Never hand-write timings, never publish without a person approving it.
