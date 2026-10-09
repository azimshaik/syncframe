#!/usr/bin/env python3
"""One continuous narration take from a script, with each paragraph start measured.

Usage: python3 tools/tts.py <script.txt> <out-dir> [voice] [style] [--engine gemini|elevenlabs]
                                                                  [--dry-run] [--check-quota]

The script is one paragraph per beat. The take is a single read, never per-line clips.
Writes <out-dir>/vo.wav and <out-dir>/timings.json. The timings carry the measured
start of every paragraph, which is what the composition generator places beats on.

Engines:

  gemini      (default) gemini-2.5-flash-preview-tts. Key from GEMINI_API_KEY.
              Voices: any Gemini prebuilt voice, for example Charon, Kore, Puck, Fenrir.
  elevenlabs  eleven_v3 with a voice of your own, a clone included. Key from
              ELEVENLABS_API_KEY, voice id from EL_VOICE_ID, both from the environment
              or ./.env. This engine costs money and spends the account's character
              quota, so check it first with --check-quota.

Styles (gemini):  measured, engaged, brisk.
Styles (elevenlabs): the same three names, applied as voice settings, not spoken text.

--dry-run      Print what would be sent, mask the credentials, and send nothing.
--check-quota  Ask ElevenLabs how many characters are used and left. Spends nothing.

Keys never print. Errors pass through a redactor, so a failed request cannot leak one.
"""
import base64, json, os, pathlib, re, subprocess, sys, urllib.error, urllib.request, wave
from typing import NoReturn

USAGE = "python3 tools/tts.py <script.txt> <out-dir> [voice] [style] [--engine gemini|elevenlabs] [--dry-run] [--check-quota]"

FLAGS = {a for a in sys.argv[1:] if a.startswith("--")}
# A flag's value is not a positional argument. Without this, `--engine elevenlabs` would hand
# "elevenlabs" to the script as the voice.
VALUE_FLAGS = {"--engine"}
POS, _skip = [], False
for _a in sys.argv[1:]:
    if _skip:
        _skip = False
        continue
    if _a in VALUE_FLAGS:
        _skip = True
        continue
    if _a.startswith("--"):
        continue
    POS.append(_a)
DRY = "--dry-run" in FLAGS
CHECK = "--check-quota" in FLAGS
ENGINE = "gemini"
for i, a in enumerate(sys.argv):
    if a == "--engine" and i + 1 < len(sys.argv):
        ENGINE = sys.argv[i + 1].strip().lower()
    elif a.startswith("--engine="):
        ENGINE = a.split("=", 1)[1].strip().lower()
if ENGINE not in ("gemini", "elevenlabs"):
    sys.exit(f"Unknown engine: {ENGINE}. Use gemini or elevenlabs.")

GEMINI_MODEL = "gemini-2.5-flash-preview-tts"
ELEVEN_MODEL = "eleven_v3"
ELEVEN_URL = "https://api.elevenlabs.io"

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

# ElevenLabs takes settings rather than a spoken direction. These are starting points, and the
# pace of a clone drifts between calls, so roll more than one take and keep the best.
ELEVEN_VOICE_SETTINGS = {
    "measured": {"stability": 0.33, "similarity_boost": 0.75, "style": 0.50, "use_speaker_boost": True},
    "engaged":  {"stability": 0.30, "similarity_boost": 0.80, "style": 0.65, "use_speaker_boost": True},
    "brisk":    {"stability": 0.25, "similarity_boost": 0.80, "style": 0.75, "use_speaker_boost": True},
}


def load_env(names):
    """Read the named keys from the environment, then from ./.env. Values are never printed."""
    out = {}
    dotenv = pathlib.Path(".env")
    pairs = {}
    if dotenv.exists():
        for line in dotenv.read_text(errors="ignore").splitlines():
            m = re.match(r"\s*([A-Za-z0-9_]+)\s*=\s*(.*)", line)
            if m:
                pairs[m.group(1)] = m.group(2).strip().strip('"').strip("'")
    for n in names:
        v = os.environ.get(n) or pairs.get(n, "")
        if v:
            out[n] = v
    return out


def mask(value):
    """Show that a credential is set without showing it."""
    if not value:
        return "not set"
    if len(value) <= 8:
        return "set (too short to mask safely: check this value)"
    return f"set, ends ...{value[-4:]}"


def redact(text, secrets):
    for s in secrets:
        if s and len(s) > 6:
            text = text.replace(s, "***REDACTED***")
    return text


SECRETS = []


def fail(message: str) -> NoReturn:
    sys.exit(redact(message, SECRETS))


if CHECK:
    # The subscription endpoint belongs to ElevenLabs, so this reads the ElevenLabs key whether or
    # not an engine was named, and it needs no script. Read only: it spends no characters.
    env = load_env(["ELEVENLABS_API_KEY"])
    KEY = env.get("ELEVENLABS_API_KEY", "")
    SECRETS.append(KEY)
    if not KEY:
        fail("No ELEVENLABS_API_KEY, so the quota cannot be read. Set it, or put it in ./.env.")
    req = urllib.request.Request(f"{ELEVEN_URL}/v1/user/subscription", headers={"xi-api-key": KEY})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            sub = json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        body_txt = redact(e.read().decode()[:200], SECRETS)
        if e.code == 401:
            fail("ElevenLabs refused the key (401). That is either a bad key or an exhausted quota.\n"
                 f"Response: {body_txt}")
        fail(f"The quota request failed: {e.code} {body_txt}")
    used, limit = sub.get("character_count"), sub.get("character_limit")
    tier = sub.get("tier", "?")
    left = f", {limit - used} left" if isinstance(used, int) and isinstance(limit, int) else ""
    print(f"ElevenLabs: {tier}, {used} characters used of {limit}{left}")
    sys.exit(0)

if not POS or len(POS) < 2:
    sys.exit(USAGE)
SCRIPT = pathlib.Path(POS[0]).expanduser()
OUT = pathlib.Path(POS[1]).expanduser()
STYLE = POS[3] if len(POS) > 3 else "measured"
if STYLE not in STYLES:
    sys.exit(f"Unknown style: {STYLE}. Use one of: {', '.join(STYLES)}.")

if ENGINE == "gemini":
    VOICE = POS[2] if len(POS) > 2 else "Charon"
    env = load_env(["GEMINI_API_KEY"])
    KEY = env.get("GEMINI_API_KEY", "")
    SECRETS.append(KEY)
    if not KEY and not DRY:
        fail("No key. Set GEMINI_API_KEY, or put it in ./.env. Run tools/doctor.sh to check.")
else:
    env = load_env(["ELEVENLABS_API_KEY", "EL_VOICE_ID", "VOICE_ID"])
    KEY = env.get("ELEVENLABS_API_KEY", "")
    VOICE = POS[2] if len(POS) > 2 else env.get("EL_VOICE_ID") or env.get("VOICE_ID") or ""
    SECRETS.append(KEY)
    if not KEY and not DRY:
        fail("No key. Set ELEVENLABS_API_KEY, or put it in ./.env. Run tools/doctor.sh to check.")
    if not VOICE and not DRY:
        fail("No voice id. Set EL_VOICE_ID, or put it in ./.env, or pass it as the third argument.\n"
             "The id is in the ElevenLabs voice library next to the voice you cloned.")

if not SCRIPT.exists():
    fail(f"No script at {SCRIPT}. The script is one paragraph per beat, plain text.")
PARAGRAPHS = [p.strip() for p in SCRIPT.read_text().splitlines() if p.strip()]
if len(PARAGRAPHS) < 2:
    fail(f"{SCRIPT} has {len(PARAGRAPHS)} paragraph(s). The script needs at least two, one per beat.")
script = " ".join(PARAGRAPHS)

if DRY:
    chars = len(script)
    print(f"engine:    {ENGINE}")
    if ENGINE == "gemini":
        print(f"model:     {GEMINI_MODEL}\nvoice:     {VOICE}\nstyle:     {STYLE} (sent as a spoken direction)")
        print(f"key:       {mask(KEY)}")
        print(f"endpoint:  POST https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent"
              "\n           (the key travels as a query parameter, so it is never printed here)")
    else:
        print(f"model:     {ELEVEN_MODEL}\nvoice id:  {mask(VOICE)}\nsettings:  {ELEVEN_VOICE_SETTINGS[STYLE]}")
        print(f"key:       {mask(KEY)}")
        print(f"endpoint:  POST {ELEVEN_URL}/v1/text-to-speech/<voice-id>?output_format=pcm_24000"
              "\n           (the key travels in the xi-api-key header, so it is never printed here)")
    print(f"script:    {len(PARAGRAPHS)} paragraphs, {len(script.split())} words, {chars} characters")
    print(f"out:       {OUT}/vo.wav and {OUT}/timings.json")
    print(f"cost:      Gemini free tier, or {chars} characters of the ElevenLabs quota")
    print("dry run: nothing was sent.")
    sys.exit(0)

OUT.mkdir(parents=True, exist_ok=True)

if ENGINE == "gemini":
    body = {"contents": [{"parts": [{"text": f"{STYLES[STYLE]}\n\n{script}"}]}],
            "generationConfig": {"responseModalities": ["AUDIO"],
                                 "speechConfig": {"voiceConfig": {"prebuiltVoiceConfig": {"voiceName": VOICE}}}}}
    req = urllib.request.Request(
        f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent?key={KEY}",
        data=json.dumps(body).encode(), headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=600) as r:
            res = json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        fail(f"The TTS request failed: {e.code} {e.read().decode()[:300]}")
    except urllib.error.URLError as e:
        fail(f"The TTS request failed: {e.reason}")
    raw = base64.b64decode(res["candidates"][0]["content"]["parts"][0]["inlineData"]["data"])
    if raw[:4] == b"RIFF":
        (OUT / "vo.wav").write_bytes(raw)
    else:
        with wave.open(str(OUT / "vo.wav"), "wb") as w:
            w.setnchannels(1); w.setsampwidth(2); w.setframerate(24000); w.writeframes(raw)
else:
    # One request, one read. The direction is never spoken here: eleven_v3 takes settings, not a
    # spoken instruction, and a direction in the text would be read out loud.
    body = {"text": script, "model_id": ELEVEN_MODEL, "voice_settings": ELEVEN_VOICE_SETTINGS[STYLE]}
    req = urllib.request.Request(
        f"{ELEVEN_URL}/v1/text-to-speech/{VOICE}?output_format=pcm_24000",
        data=json.dumps(body).encode(),
        headers={"Content-Type": "application/json", "xi-api-key": KEY, "Accept": "audio/*"})
    try:
        with urllib.request.urlopen(req, timeout=600) as r:
            pcm = r.read()
    except urllib.error.HTTPError as e:
        body_txt = redact(e.read().decode()[:300], SECRETS)
        if e.code == 401:
            fail("ElevenLabs refused the request (401). A bad key and an exhausted quota look the same.\n"
                 f"Run --check-quota to tell them apart.\nResponse: {body_txt}")
        fail(f"The TTS request failed: {e.code} {body_txt}")
    except urllib.error.URLError as e:
        fail(f"The TTS request failed: {e.reason}")
    if not pcm:
        fail("The TTS request returned no audio.")
    with wave.open(str(OUT / "vo.wav"), "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(24000); w.writeframes(pcm)

wav = OUT / "vo.wav"


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

model = GEMINI_MODEL if ENGINE == "gemini" else ELEVEN_MODEL
(OUT / "timings.json").write_text(json.dumps(
    {"engine": ENGINE, "voice": VOICE, "model": model, "style": STYLE, "total": round(dur, 2),
     "wpm": round(words / (dur / 60)), "words": words,
     "paragraphs": PARAGRAPHS, "sentences": PARAGRAPHS, "starts": starts,
     "pauses_detected": len(pauses),
     "boundary_method": "paragraph word position snapped to the nearest detected pause"}, indent=1))
print(f"{ENGINE}/{VOICE}/{STYLE}: {dur:.2f}s, {words} words, {words / (dur / 60):.0f} wpm, "
      f"{len(pauses)} pauses, {len(starts)} paragraph starts")
print(f"wrote {wav}")
print(f"wrote {OUT / 'timings.json'}")
print("starts:", starts)
print("Pace varies between takes of the same script. If this one feels fast or slow, roll another take,")
print(f"or correct it: python3 tools/retime.py {OUT} <target-seconds>")
