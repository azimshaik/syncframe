# Contributing

This repository is a method, plus the parts of a toolchain that carry it. Most contributions are small,
and each one is usually one of three things:

- A fix that makes a step repeatable.
- A motif that draws an idea the generator does not have yet.
- A mistake written down, so the next person does not repeat it.

## What is wanted

- **A fix with a reproduction.** The command you ran, what you expected, and what happened.
- **A motif pack.** A new drawn idea. The steps are below.
- **A correction to the method.** If a step in `docs/HOW-THE-EXPLAINERS-ARE-MADE.md` fails on your
  machine, that is a defect in the document, not in your setup.
- **A mistake.** The symptom, the cause and the fix. The end of `docs/HOW-THE-EXPLAINERS-ARE-MADE.md`
  is a table of exactly these, and it is the most useful page here.

## What is not wanted

- **A change to the output of the reference example.** `dark` is the default, and
  `examples/knowledge-graph-example.mp4` is what it produces. Add an option instead.
- **Hand-written timings.** The take measures them. See `AGENTS.md`.
- **Per-line voice clips.** One continuous take, always. A slide deck of clips is the defect this
  whole method exists to avoid.
- **A key, a voice id, or a personal voice file.** Never in a commit, a script or a message.

## Set up

```bash
git clone https://github.com/azimshaik/syncframe.git
cd syncframe
bash tools/doctor.sh        # what is missing. It installs nothing.
```

You need Python 3.10 or newer, `ffmpeg` and `ffprobe` on the path, and Node 20 or newer.

You need no key to read or change the tools. A take needs one:

- `GEMINI_API_KEY` for the default engine. The free tier is enough for a test piece.
- `ELEVENLABS_API_KEY` and `EL_VOICE_ID` for a voice of your own, a clone included.

Keep a key in the environment or in `./.env`. The repository ignores `.env`. The tools print only the
last four characters of a key, and they pass every error message through a redactor. Keep both
properties when you edit them.

## The loop

Work on a scratch piece. Nothing here needs a real subject, and a short script is faster:

```bash
npx --yes hyperframes@latest init /tmp/scratch-piece
cp examples/knowledge-graph-script.txt /tmp/scratch-piece/script.txt
python3 tools/tts.py /tmp/scratch-piece/script.txt /tmp/scratch-piece/assets/voice
python3 templates/composition-generator.py /tmp/scratch-piece --motifs graph,steps,bars,basic
cd /tmp/scratch-piece && npm run check && npm run render
```

Then read the file, not the project:

```bash
python3 tools/verify.py /tmp/scratch-piece/renders/*.mp4 593
```

The word count is the last argument, and it is the one in `wc -w` of the script. Three habits keep the
cycle short:

- **Run `npm run check` before every render.** It costs seconds. A render costs minutes.
- **Cut the script to two paragraphs while you work on a drawing.** Two beats show a motif.
- **Look at the frames.** Sample the moment a change happens, then look at it. The checker reads the
  markup, not the picture.

## Add a motif pack

A pack reads the text of one paragraph and returns the drawing for that beat. The steps:

1. **Write the pack function** beside the others in `templates/composition-generator.py`. It takes the
   paragraph text and the beat index, and it returns what the other packs return.
2. **Register the name** where the tool validates pack names, and add it to the usage text at the top of
   the file. The tool then reports it in the pack list.
3. **Give the pack a fallback.** A paragraph with nothing to work from falls back to `basic` for that
   beat. A build never fails on a paragraph.
4. **Keep every colour in `THEMES`.** A hardcoded hex value stays behind when the theme changes, and
   nobody sees it until the other theme is rendered. Both themes need a value for a new token.
5. **Print what the tool used**, so a fallback is visible in the output and not silent.
6. **Respect the caption rule.** The caption is the first sentence of the paragraph. A pack draws
   around it, never through it.

Then check the contrast and look at the picture:

```bash
python3 templates/composition-generator.py /tmp/scratch-piece --motifs yourpack
cd /tmp/scratch-piece && npm run check && npm run render
```

`npm run check` reports contrast, and both themes have to pass it. A pack that reads well in the code
can still be wrong on screen, so render two or three beats and look at them.

## Add a theme token

Pick the value against the background it sits on, then measure it. `npm run check` reports contrast,
and a text token has to pass WCAG AA in both themes. Keep `dark` the default, so an existing piece does
not change.

## A pull request

One change per pull request. Include:

- The exact commands you ran, and what they printed.
- The `npm run check` verdict, including the contrast count.
- **Frames, when the change is visual.** Two stills, or a short GIF, before and after. A reviewer cannot
  judge a drawing from a diff.
- The word count and the `tools/verify.py` output, when the narration changed.

Write the description and the commit messages in the style of `STYLE.md`: short sentences, active
voice, one term per thing, and the uncertainty kept. Do not use em dashes or smart quotes.

If you changed a tool, say what you measured before and after. "The caption is one line now" is not a
number. "The caption went from 166 to 40 characters" is.

## Credit

The MIT licence in `LICENSE` covers what you send. Send work you have the right to send.

Credit the source of anything you adapt. A prompt, a diagram or a piece of copy from another person
gets a name and a link. Put the credit in the file and in the pull request. Say "we use it" when you
use something. Say "we built it" only when you did.

## Ask a question

Open an issue with the command, what you expected, and what happened. Paste the output. A question with
the output attached is answerable in one reply, and the answer usually improves a document here.
