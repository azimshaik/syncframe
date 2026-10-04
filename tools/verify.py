#!/usr/bin/env python3
"""Check the finished file, not the project.

Usage: python3 tools/verify.py <file.mp4> [word-count] ["phrase" ...]

Reports the contract (size, frame rate, frames, duration, audio stream), the loudness,
every silence of 0.6s or more, the pace if you give the word count, and whether each
phrase you name survived. The phrase check reads the audio back through Gemini, so it
needs GEMINI_API_KEY; without a key the rest still runs.
"""
import base64, json, os, pathlib, re, subprocess, sys, urllib.request

USAGE = (__doc__ or "").strip()
if len(sys.argv) < 2:
    sys.exit(USAGE)

path = pathlib.Path(sys.argv[1]).expanduser()
if not path.exists():
    sys.exit(f"No such file: {path}")
words = int(sys.argv[2]) if len(sys.argv) > 2 and sys.argv[2].isdigit() else None
phrases = [a for a in sys.argv[2 + (1 if words else 0):]]


def sh(cmd):
    return subprocess.run(cmd, capture_output=True, text=True)


v = sh(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
        "stream=width,height,r_frame_rate,nb_frames", "-of", "csv=p=0", str(path)]).stdout.strip()
a = sh(["ffprobe", "-v", "error", "-select_streams", "a:0", "-show_entries",
        "stream=codec_name,channels", "-of", "csv=p=0", str(path)]).stdout.strip()
dur = float(sh(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0",
                str(path)]).stdout.strip() or 0)

loud = sh(["ffmpeg", "-hide_banner", "-i", str(path), "-af", "ebur128=peak=true", "-f", "null", "-"]).stderr
integ = [l.strip() for l in loud.splitlines() if re.search(r"\bI:\s+-?\d", l)]
lra = [l.strip() for l in loud.splitlines() if "LRA:" in l]
peak = [l.strip() for l in loud.splitlines() if "Peak:" in l]

sil = sh(["ffmpeg", "-hide_banner", "-i", str(path), "-af", "silencedetect=noise=-38dB:d=0.6",
          "-f", "null", "-"]).stderr
pauses = [round(float(e) - float(s), 2) for s, e in
          zip(re.findall(r"silence_start: ([\d.]+)", sil), re.findall(r"silence_end: ([\d.]+)", sil))]
dead = round(sum(pauses), 2)

print(f"file       {path.name}  {path.stat().st_size} bytes")
print(f"video      {v}   audio {a or 'NONE'}")
print(f"duration   {dur:.2f}s")
print(f"loudness   {integ[-1] if integ else 'n/a'}   {lra[-1] if lra else ''}   {peak[-1] if peak else ''}")
if words:
    print(f"pace       {words / (dur / 60):.0f} wpm of finished runtime")
print(f"dead air   gaps over 0.6s: {pauses or 'none'}  ->  {dead}s of {dur:.1f}s")

key = os.environ.get("GEMINI_API_KEY", "")
if phrases and not key:
    print("phrases    skipped: set GEMINI_API_KEY to read the audio back")
elif phrases:
    mp3 = pathlib.Path("/tmp") / f"{path.stem}-check.mp3"
    sh(["ffmpeg", "-y", "-loglevel", "error", "-i", str(path), "-vn", "-ac", "1", "-ar", "16000",
        "-b:a", "64k", str(mp3)])
    body = {"contents": [{"parts": [
        {"text": "Transcribe the speech verbatim with [mm:ss] timestamps. Then say in one sentence whether "
                 "it sounds energetic or flat."},
        {"inline_data": {"mime_type": "audio/mp3", "data": base64.b64encode(mp3.read_bytes()).decode()}}]}],
        "generationConfig": {"temperature": 0.1, "maxOutputTokens": 1500}}
    req = urllib.request.Request(
        f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={key}",
        data=json.dumps(body).encode(), headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=300) as r:
            text = json.loads(r.read().decode())["candidates"][0]["content"]["parts"][0]["text"]
        missing = [p for p in phrases if p.lower() not in text.lower()]
        print(f"phrases    {len(phrases) - len(missing)}/{len(phrases)} present"
              f"{'  missing: ' + str(missing) if missing else ''}")
        print("transcript")
        for line in text.splitlines():
            if line.strip():
                print("  " + line.strip()[:110])
    except Exception as e:
        print(f"phrases    the read-back failed: {e}")
