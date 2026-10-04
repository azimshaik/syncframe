#!/usr/bin/env python3
"""One continuous narration take from a script, with each paragraph start measured.

Usage: python3 tools/tts.py <script.txt> <out-dir> [voice] [style]

The script is one paragraph per beat. The take is a single read, never per-line clips.
Writes <out-dir>/vo.wav and <out-dir>/timings.json. The timings carry the measured
start of every paragraph, which is what the composition generator places beats on.

The key comes from GEMINI_API_KEY in the environment, or from ./.env.
Voices: any Gemini prebuilt voice, for example Charon, Kore, Puck, Fenrir.
Styles: measured, engaged, brisk.
"""
import base64, json, os, pathlib, re, subprocess, sys, urllib.error, urllib.request, wave

USAGE = __doc__.strip() if __doc__ else "python3 tools/tts.py <script.txt> <out-dir> [voice] [style]"
if len(sys.argv) < 3:
    sys.exit(USAGE)

SCRIPT = pathlib.Path(sys.argv[1]).expanduser()
OUT = pathlib.Path(sys.argv[2]).expanduser()
VOICE = sys.argv[3] if len(sys.argv) > 3 else "Charon"
STYLE = sys.argv[4] if len(sys.argv) > 4 else "measured"
MODEL = "gemini-2.5-flash-preview-tts"

STYLES = {
    "measured": ("Read this the way a patient teacher works through one idea: calm, deliberate, unhurried, "
                 "confident. Clear articulation, a small fall at the end of each sentence, and let each idea "
                 "land before the next. Read it as one continuous narration, not as separate lines."),
    "engaged": ("Read this the way you would explain something genuinely useful to a colleague standing next "
                "to you. Relaxed but interested, confident, natural rise and fall, important words landing a "
                "little harder. Read it as one continuous thought, not as separate lines."),
    "brisk": ("Read this like someone who knows the answer and is a little impatient with the problem. Direct, "
              "warm, quick, no filler. Land the key words and keep it moving. Read it as one continuous "
              "thought."),
}

if not SCRIPT.exists():
    sys.exit(f"No script at {SCRIPT}. The script is one paragraph per beat, plain text.")

KEY = os.environ.get("GEMINI_API_KEY", "")
if not KEY:
    dotenv = pathlib.Path(".env")
    if dotenv.exists():
        for line in dotenv.read_text(errors="ignore").splitlines():
            m = re.match(r"\s*GEMINI_API_KEY\s*=\s*(.*)", line)
            if m:
                KEY = m.group(1).strip().strip('"').strip("'")
if not KEY:
    sys.exit("No key. Set GEMINI_API_KEY, or put it in ./.env. Run tools/doctor.sh to check.")

PARAGRAPHS = [p.strip() for p in SCRIPT.read_text().splitlines() if p.strip()]
if len(PARAGRAPHS) < 2:
    sys.exit(f"{SCRIPT} has {len(PARAGRAPHS)} paragraph(s). The script needs at least two, one per beat.")
script = " ".join(PARAGRAPHS)
OUT.mkdir(parents=True, exist_ok=True)

body = {"contents": [{"parts": [{"text": f"{STYLES[STYLE]}\n\n{script}"}]}],
        "generationConfig": {"responseModalities": ["AUDIO"],
                             "speechConfig": {"voiceConfig": {"prebuiltVoiceConfig": {"voiceName": VOICE}}}}}
req = urllib.request.Request(
    f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent?key={KEY}",
    data=json.dumps(body).encode(), headers={"Content-Type": "application/json"})
try:
    with urllib.request.urlopen(req, timeout=600) as r:
        res = json.loads(r.read().decode())
except urllib.error.HTTPError as e:
    sys.exit(f"The TTS request failed: {e.code} {e.read().decode()[:300]}")

part = res["candidates"][0]["content"]["parts"][0]
raw = base64.b64decode(part["inlineData"]["data"])
wav = OUT / "vo.wav"
if raw[:4] == b"RIFF":
    wav.write_bytes(raw)
else:
    with wave.open(str(wav), "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(24000); w.writeframes(raw)


def probe(p):
    return float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                                 "-of", "csv=p=0", str(p)], capture_output=True, text=True).stdout.strip())


dur = probe(wav)
words = len(script.split())

# Where each paragraph starts: its word position, snapped to the nearest pause the voice took.
sil = subprocess.run(["ffmpeg", "-hide_banner", "-i", str(wav), "-af",
                      "silencedetect=noise=-32dB:d=0.22", "-f", "null", "-"],
                     capture_output=True, text=True).stderr
pauses, cur = [], None
for line in sil.splitlines():
    m = re.search(r"silence_start: ([\d.]+)", line)
    if m:
        cur = float(m.group(1))
    m = re.search(r"silence_end: ([\d.]+)", line)
    if m and cur is not None:
        pauses.append((cur, float(m.group(1))))
        cur = None

cum, target = 0, []
for p in PARAGRAPHS:
    target.append(cum / words * dur)
    cum += len(p.split())

starts = [0.0]
for tp in target[1:]:
    cand = [q for q in pauses if abs((q[0] + q[1]) / 2 - tp) < 1.2]
    if cand:
        q = min(cand, key=lambda x: abs((x[0] + x[1]) / 2 - tp))
        starts.append(round((q[0] + q[1]) / 2, 2))
    else:
        starts.append(round(tp, 2))
starts = sorted(starts)

(OUT / "timings.json").write_text(json.dumps(
    {"voice": VOICE, "model": MODEL, "style": STYLE, "total": round(dur, 2),
     "wpm": round(words / (dur / 60)), "words": words,
     "paragraphs": PARAGRAPHS, "sentences": PARAGRAPHS, "starts": starts,
     "pauses_detected": len(pauses),
     "boundary_method": "paragraph word position snapped to the nearest detected pause"}, indent=1))
print(f"{VOICE}/{STYLE}: {dur:.2f}s, {words} words, {words / (dur / 60):.0f} wpm, "
      f"{len(pauses)} pauses, {len(starts)} paragraph starts")
print(f"wrote {wav}")
print(f"wrote {OUT / 'timings.json'}")
print("starts:", starts)
print("Pace varies between takes of the same script. If this one feels fast or slow, roll another take,")
print(f"or correct it: python3 tools/retime.py {OUT} <target-seconds>")
