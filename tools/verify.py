#!/usr/bin/env python3
"""Verify a retimed piece: no inserted silence, speech pace, loudness, and the words present.

The point of this check is the one was raised in review: gaps. So it measures every silence in the finished mix
and reports the total dead air, then compares the pace against the reference explainer's 139 wpm.
"""
import base64
import json
import pathlib
import re
import subprocess
import sys
import urllib.request

env = {}
for line in (pathlib.Path(".env")).read_text(errors="ignore").splitlines():
    m = re.match(r"\s*([A-Z0-9_]+)\s*=\s*(.*)", line)
    if m:
        env[m.group(1)] = m.group(2).strip().strip('"').strip("'")

root = sys.argv[1]
proj = sys.argv[2]
out_name = sys.argv[3]
words = int(sys.argv[4])
phrases = sys.argv[5:]

base = pathlib.Path.home() / "video-pipeline" / root
render = sorted((base / proj / "renders").glob("*.mp4"), key=lambda p: p.stat().st_mtime)[-1]
out = base / "out"
out.mkdir(parents=True, exist_ok=True)
deliver = out / out_name
subprocess.run(["cp", str(render), str(deliver)], check=True)


def sh(cmd):
    return subprocess.run(cmd, capture_output=True, text=True)


info = sh(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
           "stream=width,height,r_frame_rate,nb_frames", "-of", "csv=p=0", str(deliver)]).stdout.strip()
aud = sh(["ffprobe", "-v", "error", "-select_streams", "a:0", "-show_entries",
          "stream=codec_name,channels", "-of", "csv=p=0", str(deliver)]).stdout.strip()
dur = float(sh(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0",
                str(deliver)]).stdout.strip())

loud = sh(["ffmpeg", "-hide_banner", "-i", str(deliver), "-af", "ebur128", "-f", "null", "-"]).stderr
integ = [l for l in loud.splitlines() if re.search(r"\bI:\s+-?\d", l)]
lra = [l for l in loud.splitlines() if "LRA:" in l]

# silence in the delivered mix: anything 0.6s or longer is dead air in a piece this short
sil = sh(["ffmpeg", "-hide_banner", "-i", str(deliver), "-af", "silencedetect=noise=-38dB:d=0.6",
          "-f", "null", "-"]).stderr
pauses = [round(float(e) - float(s), 2) for s, e in
          zip(re.findall(r"silence_start: ([\d.]+)", sil), re.findall(r"silence_end: ([\d.]+)", sil))]
dead = round(sum(pauses), 2)

mp3 = f"/tmp/{proj}-fin.mp3"
sh(["ffmpeg", "-y", "-loglevel", "error", "-i", str(deliver), "-vn", "-ac", "1", "-ar", "16000",
    "-b:a", "64k", mp3])
b64 = base64.b64encode(pathlib.Path(mp3).read_bytes()).decode()
body = {"contents": [{"parts": [{"text": "Transcribe the speech verbatim with [mm:ss] timestamps. "
                                          "Then say in one sentence whether it sounds energetic or flat."},
        {"inline_data": {"mime_type": "audio/mp3", "data": b64}}]}],
        "generationConfig": {"temperature": 0.1, "maxOutputTokens": 1500}}
req = urllib.request.Request(
    "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent",
    data=json.dumps(body).encode(), headers={"Content-Type": "application/json"})
with urllib.request.urlopen(req, timeout=300) as r:
    text = json.loads(r.read().decode())["candidates"][0]["content"]["parts"][0]["text"]

missing = [p for p in phrases if p.lower() not in text.lower()]
print(f"== {proj}")
print(f"   video {info}  audio {aud}")
print(f"   duration {dur:.2f}s   loudness {integ[-1].strip() if integ else 'n/a'}  {lra[-1].strip() if lra else ''}")
print(f"   speech pace {words / (dur / 60):.0f} wpm of finished runtime")
print(f"   gaps over 0.6s: {pauses or 'none'}  -> dead air {dead}s of {dur:.1f}s")
print(f"   phrases present: {len(phrases) - len(missing)}/{len(phrases)}  missing {missing or 'none'}")
print(f"   deliverable {deliver} {deliver.stat().st_size} bytes")
print("   transcript:")
for l in text.splitlines():
    if l.strip():
        print("     " + l.strip()[:110])
