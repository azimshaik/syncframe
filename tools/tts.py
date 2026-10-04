#!/usr/bin/env python3
"""Continuous narration takes for either explainer, so neither piece has inserted silence.

Usage: python3 tts_continuous2.py <script-name> <voice> <out-dir> [style]
   script-name: storage | move
"""
import base64
import json
import pathlib
import re
import subprocess
import sys
import urllib.request
import wave

env = {}
for line in (pathlib.Path(".env")).read_text(errors="ignore").splitlines():
    m = re.match(r"\s*([A-Z0-9_]+)\s*=\s*(.*)", line)
    if m:
        env[m.group(1)] = m.group(2).strip().strip('"').strip("'")
KEY = env["GEMINI_API_KEY"]
MODEL = "gemini-2.5-flash-preview-tts"

STYLES = {
    "brisk": ("Read this like someone who knows the answer and is a little impatient with the problem. "
              "Direct, warm, quick, no filler. Land the key words and keep it moving. Do not drawl the "
              "ends of sentences and do not pause for effect between sentences. Read it as one "
              "continuous thought."),
    "engaged": ("Read this the way you would explain something genuinely useful to a colleague standing "
                "next to you. Relaxed but interested, confident, natural rise and fall, important words "
                "landing a little harder. Read it as one continuous thought, not as separate lines."),
}

SCRIPTS = {
    "storage": [
        "You filled a storage unit and closed the door.",
        "Six months later, the one thing you need is an hour away, behind a wall of boxes.",
        "So photograph each box as it goes in, and it lists what is inside.",
        "Then search before you leave: it names the box, so you open one, not twelve.",
        "If that unit ever floods, the claim ready list is already built.",
        "the product. Know what is in every box.",
    ],
    "move": [
        "You packed a hundred boxes, and the labels say kitchen, bedroom, garage.",
        "Six months later you need one thing, and no label tells you where it is.",
        "So photograph the box, and it lists what is inside, filed to that box.",
        "Then search for the item: every match names the box it is in.",
        "When something breaks, the claim ready list is already built.",
        "the product. Know what is in every box.",
    ],
}

name = sys.argv[1]
voice = sys.argv[2] if len(sys.argv) > 2 else "Charon"
out = pathlib.Path(sys.argv[3]).expanduser()
style_name = sys.argv[4] if len(sys.argv) > 4 else "brisk"
sentences = SCRIPTS[name]
script = " ".join(sentences)
out.mkdir(parents=True, exist_ok=True)

body = {"contents": [{"parts": [{"text": f"{STYLES[style_name]}\n\n{script}"}]}],
        "generationConfig": {"responseModalities": ["AUDIO"],
                             "speechConfig": {"voiceConfig": {"prebuiltVoiceConfig": {"voiceName": voice}}}}}
req = urllib.request.Request(
    f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent?key={KEY}",
    data=json.dumps(body).encode(), headers={"Content-Type": "application/json"})
with urllib.request.urlopen(req, timeout=300) as r:
    res = json.loads(r.read().decode())
part = res["candidates"][0]["content"]["parts"][0]
raw = base64.b64decode(part["inlineData"]["data"])
wav = out / "vo.wav"
if raw[:4] == b"RIFF":
    wav.write_bytes(raw)
else:
    with wave.open(str(wav), "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(24000); w.writeframes(raw)

d = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0",
                          str(wav)], capture_output=True, text=True).stdout.strip())
print(f"{name}: {d:.2f}s, {len(script.split())} words -> {len(script.split()) / (d / 60):.0f} wpm, voice {voice}, style {style_name}")
(out / "timings.json").write_text(json.dumps({"voice": voice, "style": style_name, "total": round(d, 2),
                                              "sentences": sentences}, indent=1))
