Read `AGENTS.md` at the repository root. It carries the whole job: the four commands, the script format (one
paragraph per beat), and the rules that are not optional.

Use `python3` on macOS and Linux, or `py -3` in Windows PowerShell. Use native shell syntax to set keys.

Order of work: run `tools/doctor.py`, then `tools/tts.py <script.txt> <piece>/assets/voice`, then
`templates/composition-generator.py <piece>`. Run `npm run check` before `npm run render`, then run
`tools/verify.py <piece>/renders/<file>.mp4 <word-count>`.

Never hand-write timings: `tools/tts.py` measures them and the generator reads them. Never publish without a
person approving it. Write prose to `STYLE.md`.
