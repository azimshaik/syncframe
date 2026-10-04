#!/usr/bin/env python3
"""Generate a beat-timed composition from a measured narration take.

Usage: python3 templates/composition-generator.py <project-dir> [--vertical] [--motifs a,b,c]

Reads <project>/assets/voice/timings.json, or <project>/vo/timings.json.
Writes <project>/index.html: one beat per paragraph, each beat placed on the measured
start of that paragraph, with the take as one audio element. Every caption comes from
your script, so nothing here is specific to any one video.

Motif packs (see --motifs). Content is read out of the paragraph, so a pack either has
what it needs or falls back to `basic`:

  basic     four drawn shapes, cycling: circle, bars, node ring, frame
  graph     a node for every paragraph, edges drawn on, this beat's node in green
  bars      two or three bars, sized from the numbers in the paragraph
  steps     the paragraph's sentences as a numbered list, revealed one at a time

Default: basic. Example: --motifs graph,steps,bars,basic

The font is optional. With assets/fonts/IBMPlexMono-Regular.ttf you get the reference
look; without it the composition asks for generic monospace and requests nothing.

Then: npm run check, then npm run render.
"""
import json, math, pathlib, re, sys

argv = sys.argv[1:]
flags = {a for a in argv if a.startswith("--")}
positional = [a for a in argv if not a.startswith("--")]
P = pathlib.Path(positional[0] if positional else ".").expanduser().resolve()
VERTICAL = "--vertical" in flags
MOTIFS = "basic"
for a in argv:
    if a.startswith("--motifs"):
        MOTIFS = a.split("=", 1)[1] if "=" in a else ""
        if not MOTIFS and "--motifs" in argv:
            MOTIFS = argv[argv.index("--motifs") + 1] if argv.index("--motifs") + 1 < len(argv) else "basic"
PACKS = [m.strip().lower() for m in MOTIFS.split(",") if m.strip()] or ["basic"]
UNKNOWN = [m for m in PACKS if m not in ("basic", "graph", "bars", "steps")]
if UNKNOWN:
    sys.exit(f"Unknown motif pack(s): {', '.join(UNKNOWN)}. Use basic, graph, bars or steps.")

CANDIDATES = [P / "assets/voice/timings.json", P / "vo/timings.json", P / "timings.json"]
tpath = next((p for p in CANDIDATES if p.exists()), None)
if tpath is None:
    sys.exit(f"No timings.json under {P}. Expected assets/voice/timings.json or vo/timings.json. "
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
    print(f"note: the audio sits outside the project. Copy {wav} into {P} and re-run.")

TAIL = 1.2
END = round(TOTAL + TAIL, 2)
N = len(STARTS)
W, H = (1080, 1920) if VERTICAL else (1920, 1080)

FONT_FILE = P / "assets/fonts/IBMPlexMono-Regular.ttf"
if FONT_FILE.exists():
    FONT_CSS = ("@font-face { font-family:'IBMPlexMono'; "
                "src:url('assets/fonts/IBMPlexMono-Regular.ttf'); }\n")
    MONO = "'IBMPlexMono',monospace"
    print("font: assets/fonts/IBMPlexMono-Regular.ttf")
else:
    FONT_CSS = "/* no font file in assets/fonts: the generic monospace family is used */\n"
    MONO = "monospace"
    print("font: none in assets/fonts, using generic monospace. Drop IBMPlexMono-Regular.ttf there "
          "for the reference look.")

# ---------- geometry ----------
# The caption owns the bottom of the frame. Everything else stays above MOTIF_BOTTOM, so a
# five line caption cannot land on a diagram. Captions are also capped to CAP_CHARS.
if VERTICAL:
    CX, CY = 540, 780
    MOTIF_TOP, MOTIF_BOTTOM = 380, 1180
    RMAX_X, RMAX_Y = 400, 400
    CAP_CHARS = 156
    CAP = ".cap { left:90px; width:900px; bottom:430px; font-size:46px; line-height:1.3; }"
    NUM = ".counter { right:90px; top:210px; }"
    TINY = ".tiny { left:90px; top:200px; }"
else:
    CX, CY = 960, 455
    MOTIF_TOP, MOTIF_BOTTOM = 170, 740
    RMAX_X, RMAX_Y = 620, 285
    CAP_CHARS = 236
    CAP = ".cap { left:140px; width:1240px; bottom:110px; font-size:34px; line-height:1.4; }"
    NUM = ".counter { right:150px; bottom:120px; }"
    TINY = ".tiny { right:140px; top:96px; }"


def caption_text(text):
    """One caption, capped so it cannot grow into the diagram above it."""
    t = " ".join(text.split())
    if len(t) <= CAP_CHARS:
        return t
    return t[:CAP_CHARS].rsplit(" ", 1)[0] + "\u2026"

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
      .cap { position:absolute; font-family:__MONO__; color:var(--ink); letter-spacing:.01em; }
      .counter { position:absolute; font-family:__MONO__; font-size:26px; color:var(--dim);
                 letter-spacing:.14em; }
      .tiny { position:absolute; font-family:__MONO__; font-size:20px; color:var(--dim);
              letter-spacing:.18em; text-transform:uppercase; }
      svg { display:block; }
      .stroke { fill:none; stroke-width:4; stroke-linejoin:round; }
      .dot { fill:none; stroke-width:4; }
      .nlabel { position:absolute; font-family:__MONO__; font-size:19px; color:var(--dim); }
      .bar { position:absolute; border-radius:3px; }
      .barlabel { position:absolute; font-family:__MONO__; font-size:28px; color:var(--ink); }
      .row { position:absolute; font-family:__MONO__; font-size:38px; color:var(--ink); }
      .row .n { color:var(--blue); }
      .panel { position:absolute; background:#151515; border:3px solid #333333; border-radius:8px; }
""".replace("__W__", str(W)).replace("__H__", str(H)).replace("__MONO__", MONO) + CAP + NUM + TINY + "\n"


def first_words(text, n=3, limit=18):
    words = re.sub(r"[\u2018\u2019\u201c\u201d'\"]", "", text).split()
    out = " ".join(words[:n])
    return out if len(out) <= limit else out[:limit - 1] + "\u2026"


def sentences_in(text, limit=5):
    parts = [s.strip() for s in re.split(r"(?<=[.!?])\s+", text) if s.strip()]
    return parts[:limit]


def numbers_in(text, limit=3):
    """Numbers the reader can see: digits only, with separators and an optional suffix."""
    found = []
    for m in re.finditer(r"(\d[\d,]*(?:\.\d+)?)\s*(%|x|\u00d7|percent)?", text):
        raw = m.group(1).replace(",", "")
        try:
            val = float(raw)
        except ValueError:
            continue
        prefix = text[:m.start()].rstrip()
        label = " ".join(prefix.split()[-3:])
        suffix = m.group(2) or ""
        shown = m.group(1) + ("" if suffix in ("percent",) else suffix)
        found.append({"value": val, "shown": shown + ("%" if suffix == "percent" else ""),
                      "label": label, "suffix": suffix})
        if len(found) >= limit:
            break
    return found


def svg_open():
    return f'<svg width="{W}" height="{H}" style="position:absolute; left:0; top:0;">'


# ---------- motif packs: each returns (extra_html, svg, js) ----------
def pack_basic(i, text):
    k = i % 4
    pre = f"b{i}"
    if k == 0:
        r = 210 if not VERTICAL else 250
        svg = (svg_open() + f'<circle class="stroke" id="{pre}s1" stroke="#58C4DD" cx="{CX}" cy="{CY}" r="{r}"/>'
               + f'<circle class="stroke" id="{pre}s2" stroke="#83C167" cx="{CX}" cy="{CY}" r="{int(r * 0.34)}"/>'
               + '</svg>')
        js = [(f"#{pre}s1", "dash", 0.30, 1.4), (f"#{pre}s2", "dash", 1.30, 0.9)]
    elif k == 1:
        bw, gap = 84, 26
        total = 6 * bw + 5 * gap
        x0 = CX - total // 2
        rects = "".join(f'<rect class="dot" id="{pre}s{j+1}" stroke="#58C4DD" x="{x0 + j * (bw + gap)}" '
                        f'y="{CY - 40 + (j % 3) * 30}" width="{bw}" height="{120 - (j % 3) * 24}" rx="4"/>'
                        for j in range(6))
        svg = svg_open() + rects + '</svg>'
        js = [(f"#{pre}s{j+1}", "fade", 0.30 + j * 0.16, 0.5) for j in range(6)]
    elif k == 2:
        n, r = 6, (230 if not VERTICAL else 260)
        pts = [(CX + r * math.cos(2 * math.pi * j / n - 1.57), CY + r * math.sin(2 * math.pi * j / n - 1.57))
               for j in range(n)]
        lines = "".join(f'<line class="stroke" id="{pre}l{j+1}" stroke="#58C4DD" x1="{CX}" y1="{CY}" '
                        f'x2="{x:.1f}" y2="{y:.1f}"/>' for j, (x, y) in enumerate(pts))
        dots = (f'<circle class="dot" id="{pre}s0" stroke="#83C167" cx="{CX}" cy="{CY}" r="42"/>'
                + "".join(f'<circle class="dot" id="{pre}s{j+1}" stroke="#58C4DD" cx="{x:.1f}" cy="{y:.1f}" r="26"/>'
                          for j, (x, y) in enumerate(pts)))
        svg = svg_open() + lines + dots + '</svg>'
        js = [(f"#{pre}l{j+1}", "dash", 0.30 + j * 0.10, 0.4) for j in range(n)]
        js += [(f"#{pre}s0", "dash", 0.30, 1.0)]
        js += [(f"#{pre}s{j+1}", "dash", 0.80 + j * 0.10, 0.5) for j in range(n)]
    else:
        bw, bh = ((760, 520) if not VERTICAL else (820, 620))
        x0, y0 = CX - bw // 2, CY - bh // 2
        lid = y0 + int(bh * 0.30)
        svg = (svg_open() + f'<path class="stroke" id="{pre}s1" stroke="#58C4DD" '
               f'd="M{x0} {y0} L{x0 + bw} {y0} L{x0 + bw} {y0 + bh} L{x0} {y0 + bh} Z"/>'
               + f'<path class="stroke" id="{pre}s2" stroke="#FFFF00" d="M{x0} {lid} L{x0 + bw} {lid}"/>'
               + '</svg>')
        js = [(f"#{pre}s1", "dash", 0.30, 1.4), (f"#{pre}s2", "dash", 1.40, 0.7)]
    return "", svg, js


def pack_graph(i, text):
    """One node per paragraph, sequential edges, this beat's node resolved in green."""
    if N < 3:
        return None
    pre = f"b{i}"
    rx = min(RMAX_X - 80, 120 + N * 30) if not VERTICAL else min(RMAX_X - 60, 110 + N * 26)
    ry = min(RMAX_Y - 90, 90 + N * 16) if not VERTICAL else min(RMAX_Y - 120, 130 + N * 32)
    rx, ry = max(rx, 90), max(ry, 70)
    pts = [(CX + rx * math.cos(2 * math.pi * j / N - 1.57), CY + ry * math.sin(2 * math.pi * j / N - 1.57))
           for j in range(N)]
    edges = [(j, j + 1) for j in range(N - 1)] + [(j, j + 2) for j in range(0, N - 2, 3)]
    lines = "".join(f'<line class="stroke" id="{pre}l{k+1}" stroke="#58C4DD" x1="{pts[a][0]:.1f}" '
                    f'y1="{pts[a][1]:.1f}" x2="{pts[b][0]:.1f}" y2="{pts[b][1]:.1f}"/>'
                    for k, (a, b) in enumerate(edges))
    dots = "".join(f'<circle class="dot" id="{pre}s{j+1}" '
                   f'stroke="{"#83C167" if j == i else "#58C4DD"}" cx="{pts[j][0]:.1f}" cy="{pts[j][1]:.1f}" '
                   f'r="{34 if j == i else 24}"/>' for j in range(N))
    # Labels go outward along each node's radius, so neighbours diverge instead of stacking.
    # Above eight nodes the ring is too dense to label, so it stays clean.
    labels, label_js = "", []
    if N <= 8:
        for j in range(N):
            dx, dy = pts[j][0] - CX, pts[j][1] - CY
            d = math.hypot(dx, dy) or 1
            lx, ly = pts[j][0] + dx / d * 44, pts[j][1] + dy / d * 16
            align = "translateX(-100%)" if dx < 0 else "none"
            labels += (f'<div class="nlabel" id="{pre}t{j+1}" style="left:{lx:.0f}px; top:{ly - 10:.0f}px; '
                       f'transform:{align}; opacity:0">{first_words(TEXT[j], 2, 14)}</div>')
            label_js.append((f"#{pre}t{j+1}", "fade", 0.95 + j * 0.08, 0.4))
    js = [(f"#{pre}l{k+1}", "dash", 0.30 + k * 0.06, 0.35) for k in range(len(edges))]
    js += [(f"#{pre}s{j+1}", "dash", 0.70 + j * 0.08, 0.5) for j in range(N)]
    js += label_js
    return labels, svg_open() + lines + dots + '</svg>', js


def pack_bars(i, text):
    """Two or three bars sized from the numbers in the paragraph."""
    nums = numbers_in(text)
    if len(nums) < 2:
        return None
    pre = f"b{i}"
    top = nums[:3]
    biggest = max(n["value"] for n in top) or 1
    maxw = (1080 if not VERTICAL else 780)
    bar_h = 46 if not VERTICAL else 60
    pitch = 132 if not VERTICAL else 165
    y0 = CY - (len(top) - 1) * pitch // 2 - bar_h // 2
    x0 = CX - maxw // 2
    bars, labels, js = [], [], []
    for j, n in enumerate(top):
        w = max(24, int(maxw * (n["value"] / biggest)))
        colour = "#83C167" if j == 0 else "#3C3C3C"
        bars.append(f'<div class="bar" id="{pre}b{j+1}" style="left:{x0}px; top:{y0 + j * pitch}px; '
                    f'width:{w}px; height:{bar_h}px; background:{colour}; opacity:0"></div>')
        label = (n["label"] + " " if n["label"] else "") + n["shown"]
        labels.append(f'<div class="barlabel" id="{pre}t{j+1}" style="left:{x0}px; '
                      f'top:{y0 + j * pitch - 44}px; opacity:0">{label[:46]}</div>')
        js.append((f"#{pre}b{j+1}", "scale", 0.30 + j * 0.45, 0.6))
        js.append((f"#{pre}t{j+1}", "fade", 0.40 + j * 0.45, 0.4))
    return "".join(bars + labels), "", js


def pack_steps(i, text):
    """The paragraph's sentences, as a numbered list revealed one at a time."""
    pitch = 86 if not VERTICAL else 116
    rows_max = max(2, min(5, (2 * RMAX_Y) // pitch + 1))
    parts = sentences_in(text, rows_max)
    if len(parts) < 2:
        return None
    pre = f"b{i}"
    y0 = CY - (len(parts) - 1) * pitch // 2
    x0 = CX - (560 if not VERTICAL else 430)
    rows, js = [], []
    for j, part in enumerate(parts):
        rows.append(f'<div class="row" id="{pre}r{j+1}" style="left:{x0}px; top:{y0 + j * pitch}px; '
                    f'opacity:0"><span class="n">{j + 1}</span>&nbsp;&nbsp;{part[:40]}</div>')
        js.append((f"#{pre}r{j+1}", "fade", 0.35 + j * 0.5, 0.45))
    return "".join(rows), "", js


PACK_FN = {"basic": pack_basic, "graph": pack_graph, "bars": pack_bars, "steps": pack_steps}

beats_html, beats_js, chosen = [], [], []
for i in range(N):
    start = STARTS[i]
    end = STARTS[i + 1] if i + 1 < N else END
    dur = round(end - start, 2)
    wanted = PACKS[i % len(PACKS)]
    if wanted == "basic":
        extra, svg, js = pack_basic(i, TEXT[i])
        used = "basic"
    else:
        got = PACK_FN[wanted](i, TEXT[i])
        if got is None:
            extra, svg, js = pack_basic(i, TEXT[i])
            used = "basic (fell back: this paragraph has nothing for " + wanted + ")"
        else:
            extra, svg, js = got
            used = wanted
    chosen.append(used)
    cap = caption_text(TEXT[i]).replace("<", "&lt;")
    beats_html.append(f"""
  <!-- beat {i + 1} of {N}, motif: {used} -->
  <div class="clip" id="beat-b{i}" data-start="{start:.2f}" data-duration="{dur:.2f}" data-track-index="{i + 1}">
    {svg}
    {extra}
    <div class="cap" id="b{i}cap" style="opacity:0">{cap}</div>
    <div class="counter" id="b{i}num" style="opacity:0">{i + 1} / {N}</div>
  </div>""")
    beats_js.append(f"    tl.fromTo('#beat-b{i}', {{ opacity: 0 }}, {{ opacity: 1, duration: .4 }}, {start:.2f});")
    for sel, kind, delay, d in js:
        at = round(start + delay, 2)
        if kind == "dash":
            beats_js.append(f"    tl.fromTo('{sel}', {{ strokeDashoffset: window.__len('{sel}') }}, "
                            f"{{ strokeDashoffset: 0, duration: {d}, ease: 'power1.inOut' }}, {at});")
        elif kind == "scale":
            beats_js.append(f"    tl.fromTo('{sel}', {{ opacity: 0, scaleX: .55, transformOrigin: '0% 50%' }}, "
                            f"{{ opacity: 1, scaleX: 1, duration: {d}, ease: 'power2.out' }}, {at});")
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
  // path lengths are read once, outside the tweens
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
print(f"motifs asked for: {PACKS}")
print(f"motifs used:      {chosen}")
print("next: cd", P, "&& npm run check && npm run render")
