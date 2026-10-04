#!/usr/bin/env python3
"""Correct a take to a target length, and move every beat boundary with it.

Usage: python3 tools/retime.py <vo-dir> <target-seconds>

A tempo change scales every time in the take by one constant, so every boundary is
scaled by the same factor. Do not re-measure. The original take is kept as
vo-original.wav, and vo.wav is replaced by the corrected one.

Example: python3 tools/retime.py my-piece/vo 180
"""
import json, pathlib, shutil, subprocess, sys

if len(sys.argv) < 3:
    sys.exit((__doc__ or "").strip())

VD = pathlib.Path(sys.argv[1]).expanduser()
TARGET = float(sys.argv[2])
wav = VD / "vo.wav"
tpath = VD / "timings.json"
if not wav.exists() or not tpath.exists():
    sys.exit(f"No vo.wav or timings.json in {VD}. Run tools/tts.py first.")

T = json.loads(tpath.read_text())
dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0",
                            str(wav)], capture_output=True, text=True).stdout.strip())
factor = dur / TARGET
if abs(factor - 1.0) < 0.02:
    print(f"Nothing to do: the take is {dur:.2f}s against a target of {TARGET:.0f}s.")
    sys.exit(0)
if not 0.5 <= factor <= 2.0:
    sys.exit(f"A factor of {factor:.2f} is too far from 1.0. Atempo stays between 0.5 and 2.0.")

backup = VD / "vo-original.wav"
if not backup.exists():
    shutil.copy2(wav, backup)
out = VD / "vo-tmp.wav"
subprocess.run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-i", str(wav),
                "-af", f"atempo={factor:.4f}", str(out)], check=True)
out.replace(wav)

T["starts"] = [round(s / factor, 2) for s in T["starts"]]
T["total"] = round(dur / factor, 2)
T["retime_factor"] = round(factor, 4)
T["wpm"] = round(T.get("words", 0) / (T["total"] / 60)) if T.get("words") else T.get("wpm")
tpath.write_text(json.dumps(T, indent=1))
print(f"atempo {factor:.4f}: {dur:.2f}s -> {T['total']:.2f}s, {len(T['starts'])} boundaries scaled")
print(f"vo.wav replaced, the original kept at {backup.name}")
