#!/usr/bin/env python3
"""Generate a beat-timed composition from a measured narration take.

Usage: python3 templates/composition-generator.py <project-dir> [--vertical]

Reads <project>/assets/voice/timings.json, or <project>/vo/timings.json.
Writes <project>/index.html: one beat per paragraph, each beat placed on the measured
start of that paragraph, with the take as one audio element. The text of every caption
comes from your script, so nothing here is specific to any one video.

Motifs are drawn on, one per beat, cycling through four shapes. Bring your own font:
the CSS asks for assets/fonts/IBMPlexMono-Regular.ttf and falls back to the system
monospace when the file is absent.

Then: npm run check, then npm run render.
"""
import json, pathlib, sys

argv = sys.argv[1:]
flags = {a for a in argv if a.startswith("--")}
positional = [a for a in argv if not a.startswith("--")]
P = pathlib.Path(positional[0] if positional else ".").expanduser().resolve()
VERTICAL = "--vertical" in flags

CANDIDATES = [P / "assets/voice/timings.json", P / "vo/timings.json", P / "timings.json"]
tpath = next((p for p in CANDIDATES if p.exists()), None)
if tpath is None:
    sys.exit(f"No timings.json under {P}. Expected assets/voice/timings.json or vo/timings.json.\n"
             "Run tools/tts.py first.")
T = json.loads(tpath.read_text())
if "starts" not in T:
    sys.exit(f"{tpath} has no 'starts'. Regenerate the take with tools/tts.py.")
STARTS = [float(s) for s in T["starts"]]
TOTAL = float(T["total"])
TEXT = T.get("paragraphs") or T.get("sentences") or []
if len(TEXT) != len(STARTS):
    sys.exit(f"{tpath} has {len(STARTS)} starts and {len(TEXT)} paragraphs. They must match.")

wav = tpath.parent / "vo.wav"
if not wav.exists():
    sys.exit(f"No vo.wav next to {tpath}.")
try:
    wav_rel = str(wav.relative_to(P))
except ValueError:
    wav_rel = wav.name
    print(f"note: the audio sits outside the project. Copy {wav} into {P} and re-run, "
          f"or keep it at ./{wav.name}.")

TAIL = 1.2
END = round(TOTAL + TAIL, 2)
N = len(STARTS)
W, H = (1080, 1920) if VERTICAL else (1920, 1080)

# The font is optional. Without the file the composition asks for a generic monospace
# family and makes no request: the runtime treats a 404 on an asset as a hard error, and
# it rejects named system families that have no @font-face declaration.
FONT_FILE = P / "assets/fonts/IBMPlexMono-Regular.ttf"
if FONT_FILE.exists():
    FONT_CSS = ("@font-face { font-family:'IBMPlexMono'; "
                "src:url('assets/fonts/IBMPlexMono-Regular.ttf'); }\n")
    MONO = "'IBMPlexMono',monospace"
    print("font: assets/fonts/IBMPlexMono-Regular.ttf")
else:
    FONT_CSS = "/* no font file in assets/fonts: the generic monospace family is used */\n"
    MONO = "monospace"
    print("font: none in assets/fonts, using the generic monospace family. "
          "Drop IBMPlexMono-Regular.ttf there for the reference look.")

# ---------- geometry ----------
if VERTICAL:
    CX, CY = 540, 760
    CAP = ".cap { left:90px; width:900px; bottom:430px; font-size:46px; line-height:1.3; }"
    NUM = ".counter { right:90px; top:210px; }"
    TINY = ".tiny { left:90px; top:200px; }"
else:
    CX, CY = 960, 430
    CAP = ".cap { left:140px; width:1240px; bottom:110px; font-size:34px; line-height:1.4; }"
    NUM = ".counter { right:150px; bottom:120px; }"
    TINY = ".tiny { right:140px; top:96px; }"

CSS = """
      :root { --bg:#1C1C1C; --blue:#58C4DD; --green:#83C167; --yellow:#FFFF00;
              --dim:#888888; --ink:#ECECEC; }
      html, body { margin:0; padding:0; background:var(--bg); }
      .stage { position:relative; width:__W__px; height:__H__px; background:var(--bg); overflow:hidden; }
      .grid { position:absolute; inset:0; opacity:.05;
        background-image: linear-gradient(#ECECEC 1px, transparent 1px),
                          linear-gradient(90deg, #ECECEC 1px, transparent 1px);
        background-size: 120px 120px; }
      .clip { position:absolute; inset:0; }
      .cap { position:absolute; font-family:__MONO__; color:var(--ink);
             letter-spacing:.01em; }
      .counter { position:absolute; font-family:__MONO__; font-size:26px;
                 color:var(--dim); letter-spacing:.14em; }
      .tiny { position:absolute; font-family:__MONO__; font-size:20px;
              color:var(--dim); letter-spacing:.18em; text-transform:uppercase; }
      svg { display:block; }
      .stroke { fill:none; stroke-width:4; stroke-linejoin:round; }
      .dot { fill:none; stroke-width:4; }
""".replace("__W__", str(W)).replace("__H__", str(H)).replace("__MONO__", MONO) + CAP + NUM + TINY + "\n"

# ---------- four motifs, cycling per beat ----------
def motif(i):
    """Return (svg, javascript) for beat i. Shapes are drawn on, never cut to."""
    k = i % 4
    pre = f"b{i}"
    if k == 0:  # a circle, drawn on
        r = 210 if not VERTICAL else 260
        svg = (f'<svg width="{W}" height="{H}" style="position:absolute; left:0; top:0;">'
               f'<circle class="stroke" id="{pre}s1" stroke="#58C4DD" cx="{CX}" cy="{CY}" r="{r}"/>'
               f'<circle class="stroke" id="{pre}s2" stroke="#83C167" cx="{CX}" cy="{CY}" r="{int(r*0.34)}"/>'
               f'</svg>')
        js = [(f"#{pre}s1", "dash", 0.30, 1.4), (f"#{pre}s2", "dash", 1.30, 0.9)]
    elif k == 1:  # six bars, appearing
        bw, gap = 84, 26
        total = 6 * bw + 5 * gap
        x0 = CX - total // 2
        rects = "".join(
            f'<rect class="dot" id="{pre}s{j+1}" stroke="#58C4DD" x="{x0 + j * (bw + gap)}" '
            f'y="{CY - 40 + (j % 3) * 30}" width="{bw}" height="{120 - (j % 3) * 24}" rx="4"/>'
            for j in range(6))
        svg = f'<svg width="{W}" height="{H}" style="position:absolute; left:0; top:0;">{rects}</svg>'
        js = [(f"#{pre}s{j+1}", "fade", 0.30 + j * 0.16, 0.5) for j in range(6)]
    elif k == 2:  # a node ring, with edges
        import math
        n, r = 6, 230 if not VERTICAL else 270
        pts = [(CX + r * math.cos(2 * math.pi * j / n - 1.57), CY + r * math.sin(2 * math.pi * j / n - 1.57))
               for j in range(n)]
        dots = f'<circle class="dot" id="{pre}s0" stroke="#83C167" cx="{CX}" cy="{CY}" r="42"/>'
        dots += "".join(f'<circle class="dot" id="{pre}s{j+1}" stroke="#58C4DD" cx="{x:.1f}" cy="{y:.1f}" r="26"/>'
                        for j, (x, y) in enumerate(pts))
        lines = "".join(f'<line class="stroke" id="{pre}l{j+1}" stroke="#58C4DD" x1="{CX}" y1="{CY}" '
                        f'x2="{x:.1f}" y2="{y:.1f}"/>' for j, (x, y) in enumerate(pts))
        svg = f'<svg width="{W}" height="{H}" style="position:absolute; left:0; top:0;">{lines}{dots}</svg>'
        js = [(f"#{pre}l{j+1}", "dash", 0.30 + j * 0.10, 0.4) for j in range(n)]
        js += [(f"#{pre}s0", "dash", 0.30, 1.0)]
        js += [(f"#{pre}s{j+1}", "dash", 0.80 + j * 0.10, 0.5) for j in range(n)]
    else:  # a frame, drawn on with its own lid
        bw, bh = (760, 520) if not VERTICAL else (820, 640)
        x0, y0 = CX - bw // 2, CY - bh // 2
        lid = y0 + int(bh * 0.30)
        svg = (f'<svg width="{W}" height="{H}" style="position:absolute; left:0; top:0;">'
               f'<path class="stroke" id="{pre}s1" stroke="#58C4DD" '
               f'd="M{x0} {y0} L{x0 + bw} {y0} L{x0 + bw} {y0 + bh} L{x0} {y0 + bh} Z"/>'
               f'<path class="stroke" id="{pre}s2" stroke="#FFFF00" d="M{x0} {lid} L{x0 + bw} {lid}"/>'
               f'</svg>')
        js = [(f"#{pre}s1", "dash", 0.30, 1.4), (f"#{pre}s2", "dash", 1.40, 0.7)]
    return svg, js


beats_html, beats_js = [], []
for i in range(N):
    start = STARTS[i]
    end = STARTS[i + 1] if i + 1 < N else END
    dur = round(end - start, 2)
    svg, js = motif(i)
    cap = TEXT[i].replace("<", "&lt;")
    beats_html.append(f"""
  <!-- beat {i + 1} of {N} -->
  <div class="clip" id="beat-b{i}" data-start="{start:.2f}" data-duration="{dur:.2f}" data-track-index="{i + 1}">
    {svg}
    <div class="cap" id="b{i}cap" style="opacity:0">{cap}</div>
    <div class="counter" id="b{i}num" style="opacity:0">{i + 1} / {N}</div>
  </div>""")
    beats_js.append(f"    tl.fromTo('#beat-b{i}', {{ opacity: 0 }}, {{ opacity: 1, duration: .4 }}, {start:.2f});")
    for sel, kind, delay, d in js:
        at = round(start + delay, 2)
        if kind == "dash":
            beats_js.append(f"    tl.fromTo('{sel}', {{ strokeDashoffset: (window.__len('{sel}')) }}, "
                            f"{{ strokeDashoffset: 0, duration: {d}, ease: 'power1.inOut' }}, {at});")
        else:
            beats_js.append(f"    tl.fromTo('{sel}', {{ opacity: 0 }}, {{ opacity: 1, duration: {d} }}, {at});")
    beats_js.append(f"    tl.fromTo('#b{i}cap', {{ opacity: 0, y: 14 }}, {{ opacity: 1, y: 0, duration: .6 }}, "
                    f"{round(start + 0.2, 2)});")
    beats_js.append(f"    tl.fromTo('#b{i}num', {{ opacity: 0 }}, {{ opacity: 1, duration: .5 }}, "
                    f"{round(start + 0.3, 2)});")

HTML = f"""<!doctype html>
<html><head><meta charset="utf-8">
<title>{P.name}</title>
<style>
{FONT_CSS}{CSS}</style></head>
<body>
<div class="stage" id="stage" data-composition-id="main" data-width="{W}" data-height="{H}">
  <div class="grid"></div>
  <div class="tiny">one take, beats on the words</div>
{''.join(beats_html)}

  <audio id="vo" src="{wav_rel}" data-start="0" data-duration="{TOTAL:.2f}" data-volume="1"></audio>
</div>

<script src="https://cdn.jsdelivr.net/npm/gsap@3.12.5/dist/gsap.min.js"></script>
<script>
  const END = {END};
  const tl = gsap.timeline({{ paused: true }});
  // path lengths are read once, not inside a tween selector
  window.__len = (sel) => {{
    const el = document.querySelector(sel);
    const len = el.getTotalLength();
    el.setAttribute('stroke-dasharray', len);
    return len;
  }};
{chr(10).join(beats_js)}
  tl.to({{}}, {{ duration: .1 }}, END - 0.1);
  window.__timelines = window.__timelines || {{}};
  window.__timelines.main = tl;
</script>
</body></html>
"""

(P / "index.html").write_text(HTML)
print(f"wrote {P / 'index.html'}")
print(f"{N} beats, {W}x{H}, voice {TOTAL:.2f}s, end {END:.2f}s, audio {wav_rel}")
print(f"beats: {[round(STARTS[i], 2) for i in range(N)]}")
print("next: cd", P, "&& npm run check && npm run render")
