#!/usr/bin/env python3
"""Retime a project to a single continuous narration take.

Replaces the per-line audio clips with one clip, sets every beat window from the sentence boundaries
measured in the take, and regenerates the whole animation block with timings scaled to the new, faster
pace (short beats need shorter reveals and earlier count-ups).

Usage: python3 retime_continuous.py <project-dir>
Reads <project>/assets/voice/vo.wav and <project>/assets/voice/timings.json
"""
import json
import pathlib
import re
import subprocess
import sys

proj = pathlib.Path(sys.argv[1]).expanduser()
vd = proj / "assets/voice"
wav = vd / "vo.wav"
meta = json.loads((vd / "timings.json").read_text())
sentences = meta["sentences"]


def dur(p):
    return float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of",
                                 "csv=p=0", str(p)], capture_output=True, text=True).stdout.strip())


total = dur(wav)

# boundaries: word-proportional, snapped to a real pause in the take when one sits within 0.8s
sil = subprocess.run(["ffmpeg", "-hide_banner", "-i", str(wav), "-af",
                      "silencedetect=noise=-32dB:d=0.18", "-f", "null", "-"],
                     capture_output=True, text=True).stderr
pauses = [float(x) for x in re.findall(r"silence_end: ([\d.]+)", sil)]
words = [len(s.split()) for s in sentences]
cum, acc = [], 0
for w in words[:-1]:
    acc += w
    cum.append(total * acc / sum(words))
bounds = []
for b in cum:
    near = [p for p in pauses if abs(p - b) < 0.8]
    bounds.append(round(min(near, key=lambda p: abs(p - b)), 2) if near else round(b, 2))

seg = [0.0] + bounds + [round(total, 2)]
windows = [(seg[i], round(seg[i + 1] - seg[i], 2)) for i in range(len(seg) - 1)]
TAIL = 1.4
end = round(total + TAIL, 2)
# the closing card holds to the end of the piece, not to the end of the read
windows[-1] = (windows[-1][0], round(end - windows[-1][0], 2))
beats = [round(w[0] + (0.0 if i == 0 else -0.0), 2) for i, w in enumerate(windows)]

s = (proj / "index.html").read_text()

# 1. root duration
s = re.sub(r'(<div id="root" data-composition-id="main" data-start="0" data-duration=")[\d.]+(")',
           lambda m: m.group(1) + str(end) + m.group(2), s)

# 2. each beat window
for key, (st, du) in zip(["a1", "a2", "b", "c", "d", "e"], windows):
    s = re.sub(rf'(id="beat-{key}" data-start=")[\d.]+(" data-duration=")[\d.]+(")',
               lambda m, a=st, b=du: m.group(1) + str(a) + m.group(2) + str(b) + m.group(3), s)

# 3. plates, scrims and the phone inset follow their beats
for elem, idx in [("plate-a", 0), ("scrim-a", 0), ("plate-b", 1), ("scrim-b", 1), ("b-video", 2)]:
    st, du = windows[idx]
    s = re.sub(rf'(id="{elem}"[^>]*?data-start=")[\d.]+(" data-duration=")[\d.]+(")',
               lambda m: m.group(1) + str(st) + m.group(2) + str(du) + m.group(3), s, flags=re.S)

# 4. footer runs until the closing card
s = re.sub(r'(id="footer" data-start=")[\d.]+(" data-duration=")[\d.]+(")',
           lambda m: m.group(1) + "0.2" + m.group(2) + str(round(windows[5][0] - 0.3, 2)) + m.group(3), s)

# 5. one voice clip instead of six, and the bed length
s = re.sub(r'\s*<hf-audio-group id="voiceover" data-label="Voiceover"></hf-audio-group>(\s*<audio id="vo\d".*?</audio>){6}',
           f'\n      <hf-audio-group id="voiceover" data-label="Voiceover"></hf-audio-group>\n'
           f'      <audio id="vo" src="assets/voice/vo.wav" data-start="0" data-duration="{round(total, 2)}" '
           f'data-audio-group="voiceover"></audio>', s, flags=re.S)
s = re.sub(r'(<audio id="music"[^>]*?data-start="0" data-duration=")[\d.]+(")',
           lambda m: m.group(1) + str(end) + m.group(2), s, flags=re.S)

# 6. regenerate the animation block for the new pace
T = {"a1": windows[0][0], "a2": windows[1][0], "b": windows[2][0],
     "c": windows[3][0], "d": windows[4][0], "e": windows[5][0]}
block = f'''      const tl = gsap.timeline({{ paused: true }});
      const T = {{ a1: {T['a1']}, a2: {T['a2']}, b: {T['b']}, c: {T['c']}, d: {T['d']}, e: {T['e']} }};
      const money = (v) => "$" + Math.round(v).toLocaleString("en-US");
      const count = (sel, to, at, dur, fmt) => {{
        const el = document.querySelector(sel); const o = {{ v: 0 }};
        tl.to(o, {{ v: to, duration: dur, ease: "power1.out",
                   onUpdate: () => {{ el.textContent = (fmt || Math.round)(o.v); }} }}, at);
      }};
      const reveal = (sel, at, dur) => {{
        tl.fromTo(sel, {{ clipPath: "inset(0% 0% 100% 0%)" }},
                       {{ clipPath: "inset(0% 0% 0% 0%)", duration: dur, ease: "power2.inOut" }}, at);
      }};
      const inUp = (sel, at, dy) => {{
        tl.fromTo(sel, {{ opacity: 0, y: (dy === undefined ? 18 : dy) }},
                       {{ opacity: 1, y: 0, duration: .42 }}, at);
      }};

      // footage keeps moving under the words
      tl.fromTo("#plate-a", {{ scale: 1.0 }}, {{ scale: 1.06, duration: {windows[0][1]}, ease: "none" }}, {windows[0][0]});
      tl.fromTo("#plate-b", {{ scale: 1.06 }}, {{ scale: 1.0, duration: {windows[1][1]}, ease: "none" }}, {windows[1][0]});

      // A1
      inUp("#a1-eye", T.a1 + .05, 12);
      tl.fromTo("#a1-rule", {{ scaleX: 0 }}, {{ scaleX: 1, duration: .4, transformOrigin: "0 50%" }}, T.a1 + .12);
      inUp("#a1-h", T.a1 + .18, 24);
      tl.to("#beat-a1", {{ opacity: 0, duration: .35 }}, T.a2 - .4);

      // A2
      inUp("#a2-eye", T.a2 + .05, 12);
      tl.fromTo("#a2-rule", {{ scaleX: 0 }}, {{ scaleX: 1, duration: .4, transformOrigin: "0 50%" }}, T.a2 + .12);
      inUp("#a2-h", T.a2 + .18, 24);

      // B
      tl.fromTo("#beat-b", {{ opacity: 0 }}, {{ opacity: 1, duration: .35 }}, T.b);
      tl.fromTo("#b-card", {{ x: 44, opacity: 0 }}, {{ x: 0, opacity: 1, duration: .5, ease: "power2.out" }}, T.b + .1);
      reveal("#b-card", T.b + .1, 1.05);
      tl.fromTo("#b-pip", {{ y: 22, opacity: 0 }}, {{ y: 0, opacity: 1, duration: .5, ease: "power2.out" }}, T.b + .05);
      inUp("#b-eye", T.b + .12, 12);
      tl.fromTo("#b-rule", {{ scaleX: 0 }}, {{ scaleX: 1, duration: .4, transformOrigin: "0 50%" }}, T.b + .18);
      inUp("#b-h", T.b + .22, 20);
      inUp("#b-h + .stats", T.b + .5, 12);
      count("#b-n1", 4, T.b + .55, .5);
      count("#b-n2", 666, T.b + .65, .7, money);

      // C
      tl.fromTo("#beat-c", {{ opacity: 0 }}, {{ opacity: 1, duration: .35 }}, T.c);
      tl.fromTo("#c-card", {{ x: 44, opacity: 0 }}, {{ x: 0, opacity: 1, duration: .5, ease: "power2.out" }}, T.c + .1);
      reveal("#c-card", T.c + .1, 1.0);
      inUp("#c-eye", T.c + .12, 12);
      tl.fromTo("#c-rule", {{ scaleX: 0 }}, {{ scaleX: 1, duration: .4, transformOrigin: "0 50%" }}, T.c + .18);
      inUp("#c-h", T.c + .22, 20);
      inUp("#c-h + .stats", T.c + .55, 12);
      count("#c-n", 2, T.c + .6, .45);
      tl.fromTo("#c-chips .chip", {{ opacity: 0, y: 10 }}, {{ opacity: 1, y: 0, duration: .34, stagger: .3 }}, T.c + 1.0);

      // D
      tl.fromTo("#beat-d", {{ opacity: 0 }}, {{ opacity: 1, duration: .35 }}, T.d);
      tl.fromTo("#d-card", {{ x: 44, opacity: 0 }}, {{ x: 0, opacity: 1, duration: .5, ease: "power2.out" }}, T.d + .1);
      reveal("#d-card", T.d + .1, 1.0);
      inUp("#d-eye", T.d + .12, 12);
      tl.fromTo("#d-rule", {{ scaleX: 0 }}, {{ scaleX: 1, duration: .4, transformOrigin: "0 50%" }}, T.d + .18);
      inUp("#d-h", T.d + .22, 20);
      inUp("#d-h + .stats", T.d + .5, 12);
      count("#d-n1", 165, T.d + .55, .6);
      count("#d-n2", 8410, T.d + .65, .8, money);
      count("#d-n3", 6, T.d + .75, .5);

      // E
      tl.fromTo("#beat-e", {{ opacity: 0 }}, {{ opacity: 1, duration: .5 }}, T.e);
      inUp("#e-mark", T.e + .15, 18);
      inUp("#e-line", T.e + .5, 14);
      tl.fromTo("#e-fine", {{ opacity: 0 }}, {{ opacity: 1, duration: .5 }}, T.e + 1.1);
      tl.to("#footer", {{ opacity: 0, duration: .3 }}, T.e - .2);
      tl.to({{}}, {{ duration: .1 }}, {round(end - 0.1, 2)});

      window.__timelines = window.__timelines || {{}};
      window.__timelines["main"] = tl;
      tl.seek(0);
'''
s = re.sub(r"      const tl = gsap\.timeline.*?tl\.seek\(0\);\n", block, s, flags=re.S)
(proj / "index.html").write_text(s)

print(json.dumps({"take": round(total, 2), "boundaries": bounds, "windows": windows, "total": end}, indent=1))
