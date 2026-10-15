#!/usr/bin/env python3
"""Generate a beat-timed composition from a measured narration take.

Usage: python3 templates/composition-generator.py <project-dir> [--vertical] [--motifs a,b,c] [--theme dark|bright]

Reads <project>/assets/voice/timings.json, or <project>/vo/timings.json.
Writes <project>/index.html: one beat per paragraph, each beat placed on the measured
start of that paragraph, with the take as one audio element. The caption for a beat is the
first sentence of that paragraph, so it stays one line, as the narration rules require.
Every caption comes from your script, so nothing here is specific to any one video.

Motif packs (see --motifs). Content is read out of the paragraph, so a pack either has
what it needs or falls back to `basic`:

  basic     four drawn shapes, cycling: circle, bars, node ring, frame
  graph     a node for every paragraph, edges drawn on, this beat's node in green
  bars      two or three bars, sized from the numbers in the paragraph
  steps     the paragraph's sentences as a numbered list, revealed one at a time

Motion packs, where the movement carries the idea rather than the shape:

  orbit     shells of satellites travelling around a centre, one of them highlighted
  race      two pulses running the same distance, one finishing far sooner
  hop       a pulse travelling node to node along a chain, links lighting as it passes
  grid      an antenna array rippling, with the beam angle tilting as the ripple passes

Default: basic. Example: --motifs graph,steps,bars,basic

Theme (see --theme). `dark` is the default reference look. `bright` puts the same layout on
paper: dark ink and deeper accents, so nothing gets lost on a white background. Use it for
documents, slide decks and light-themed sites. Example: --theme bright

Per-beat motifs (see --beats). `--motifs` cycles its packs across the beats. When a beat needs a
specific motif, name them in order instead:

  --beats orbit,race,orbit,grid,hop,hop,hop,grid,bars,steps,orbit

Beats past the end of the list fall back to `--motifs`. This is how a piece whose beats each have
their own idea stays readable, instead of one motif repeating on a cycle.

The font is optional. With assets/fonts/IBMPlexMono-Regular.ttf you get the reference
look; without it the composition asks for generic monospace and requests nothing.

Then: npm run check, then npm run render.
"""
import json, math, pathlib, re, sys

# Two themes, one layout. The tokens cover the page, the grid and every drawn shape, so the
# palette lives in one place. Bright is paper: dark ink and deeper accents, so contrast
# still holds on a white background.
THEMES = {
    "dark":   {"bg": "#1C1C1C", "ink": "#ECECEC", "dim": "#888888", "grid": "#ECECEC",
               "grid_opacity": ".05", "blue": "#58C4DD", "green": "#83C167",
               "yellow": "#FFFF00", "muted": "#3C3C3C", "rule": "#2E2E2E", "panel_bg": "#151515",
               "panel_bd": "#333333"},
    "bright": {"bg": "#FAFAF7", "ink": "#16181D", "dim": "#5C5C5C", "grid": "#16181D",
               "grid_opacity": ".06", "blue": "#1E7FA6", "green": "#2F7D32",
               "yellow": "#A97B00", "muted": "#BDBDB4", "rule": "#E2E2DC", "panel_bg": "#EFEFEA",
               "panel_bd": "#C9C9C2"},
}

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
MOTION_PACKS = ("orbit", "race", "hop", "grid", "scale")
ALL_PACKS = ("basic", "graph", "bars", "steps") + MOTION_PACKS
PACKS = [m.strip().lower() for m in MOTIFS.split(",") if m.strip()] or ["basic"]
UNKNOWN = [m for m in PACKS if m not in ALL_PACKS]
if UNKNOWN:
    sys.exit(f"Unknown motif pack(s): {', '.join(UNKNOWN)}. Use {', '.join(ALL_PACKS)}.")

# --beats assigns a pack to one beat, in order. Beats past the end fall back to --motifs.
BEATS = []
for _i, _a in enumerate(argv):
    if _a == "--beats" and _i + 1 < len(argv):
        BEATS = [m.strip().lower() for m in argv[_i + 1].split(",") if m.strip()]
    elif _a.startswith("--beats="):
        BEATS = [m.strip().lower() for m in _a.split("=", 1)[1].split(",") if m.strip()]
_BAD = [m for m in BEATS if m not in ALL_PACKS]
if _BAD:
    sys.exit(f"Unknown pack in --beats: {', '.join(_BAD)}. Use {', '.join(ALL_PACKS)}.")

THEME = "dark"
for _i, _a in enumerate(argv):
    if _a == "--theme" and _i + 1 < len(argv):
        THEME = argv[_i + 1]
    elif _a.startswith("--theme="):
        THEME = _a.split("=", 1)[1]
THEME = THEME.strip().lower()
if THEME not in THEMES:
    sys.exit(f"Unknown theme: {THEME}. Use dark or bright.")
C = THEMES[THEME]

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
    """One key line per beat, read out of the paragraph.

    The reference cuts use one line per beat. A whole paragraph runs to four or five lines and
    reads as a subtitle dump, so the caption is the first sentence of the paragraph. A very
    short first sentence takes the next sentence with it, so the line does not look clipped.
    The cap stays as a guard: a single long sentence still cannot grow into the diagram.
    """
    t = " ".join(text.split())
    parts = [s.strip() for s in re.split(r"(?<=[.!?])\s+", t) if s.strip()]
    cap = parts[0] if parts else t
    if len(cap) < 40 and len(parts) > 1:
        cap = (cap + " " + parts[1]).strip()
    if len(cap) <= CAP_CHARS:
        return cap
    return cap[:CAP_CHARS].rsplit(" ", 1)[0] + "\u2026"


def clip_words(text, limit):
    """Cut on a clause boundary where one exists, otherwise on a word, and say that you cut.

    A row that stops mid-clause reads as unfinished; stopping after a comma reads as a summary.
    """
    if len(text) <= limit:
        return text
    head = text[:limit]
    for sep in (", ", "; ", ": "):
        i = head.rfind(sep)
        if i >= int(limit * 0.55):
            return head[:i + 1]
    return head.rsplit(" ", 1)[0] + "\u2026"

CSS = """
      :root { --bg:__BG__; --blue:__BLUE__; --green:__GREEN__; --yellow:__YELLOW__;
              --dim:__DIM__; --ink:__INK__; --muted:__MUTED__; --rule:__RULE__; }
      html, body { margin:0; padding:0; background:var(--bg); }
      .stage { position:relative; width:__W__px; height:__H__px; background:var(--bg); overflow:hidden; }
      .grid { position:absolute; inset:0; opacity:__GRID_OPACITY__;
        background-image: linear-gradient(__GRID__ 1px, transparent 1px),
                          linear-gradient(90deg, __GRID__ 1px, transparent 1px);
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
      .panel { position:absolute; background:__PANEL_BG__; border:3px solid __PANEL_BD__; border-radius:8px; }
""".replace("__W__", str(W)).replace("__H__", str(H)).replace("__MONO__", MONO)
for _k, _v in C.items():
    CSS = CSS.replace("__" + _k.upper() + "__", _v)
CSS += CAP + NUM + TINY + "\n"


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
        svg = (svg_open() + f'<circle class="stroke" id="{pre}s1" stroke="{C["blue"]}" cx="{CX}" cy="{CY}" r="{r}"/>'
               + f'<circle class="stroke" id="{pre}s2" stroke="{C["green"]}" cx="{CX}" cy="{CY}" r="{int(r * 0.34)}"/>'
               + '</svg>')
        js = [(f"#{pre}s1", "dash", 0.30, 1.4), (f"#{pre}s2", "dash", 1.30, 0.9)]
    elif k == 1:
        bw, gap = 84, 26
        total = 6 * bw + 5 * gap
        x0 = CX - total // 2
        rects = "".join(f'<rect class="dot" id="{pre}s{j+1}" stroke="{C["blue"]}" x="{x0 + j * (bw + gap)}" '
                        f'y="{CY - 40 + (j % 3) * 30}" width="{bw}" height="{120 - (j % 3) * 24}" rx="4"/>'
                        for j in range(6))
        svg = svg_open() + rects + '</svg>'
        js = [(f"#{pre}s{j+1}", "fade", 0.30 + j * 0.16, 0.5) for j in range(6)]
    elif k == 2:
        n, r = 6, (230 if not VERTICAL else 260)
        pts = [(CX + r * math.cos(2 * math.pi * j / n - 1.57), CY + r * math.sin(2 * math.pi * j / n - 1.57))
               for j in range(n)]
        lines = "".join(f'<line class="stroke" id="{pre}l{j+1}" stroke="{C["blue"]}" x1="{CX}" y1="{CY}" '
                        f'x2="{x:.1f}" y2="{y:.1f}"/>' for j, (x, y) in enumerate(pts))
        dots = (f'<circle class="dot" id="{pre}s0" stroke="{C["green"]}" cx="{CX}" cy="{CY}" r="42"/>'
                + "".join(f'<circle class="dot" id="{pre}s{j+1}" stroke="{C["blue"]}" cx="{x:.1f}" cy="{y:.1f}" r="26"/>'
                          for j, (x, y) in enumerate(pts)))
        svg = svg_open() + lines + dots + '</svg>'
        js = [(f"#{pre}l{j+1}", "dash", 0.30 + j * 0.10, 0.4) for j in range(n)]
        js += [(f"#{pre}s0", "dash", 0.30, 1.0)]
        js += [(f"#{pre}s{j+1}", "dash", 0.80 + j * 0.10, 0.5) for j in range(n)]
    else:
        bw, bh = ((760, 520) if not VERTICAL else (820, 620))
        x0, y0 = CX - bw // 2, CY - bh // 2
        lid = y0 + int(bh * 0.30)
        svg = (svg_open() + f'<path class="stroke" id="{pre}s1" stroke="{C["blue"]}" '
               f'd="M{x0} {y0} L{x0 + bw} {y0} L{x0 + bw} {y0 + bh} L{x0} {y0 + bh} Z"/>'
               + f'<path class="stroke" id="{pre}s2" stroke="{C["yellow"]}" d="M{x0} {lid} L{x0 + bw} {lid}"/>'
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
    lines = "".join(f'<line class="stroke" id="{pre}l{k+1}" stroke="{C["blue"]}" x1="{pts[a][0]:.1f}" '
                    f'y1="{pts[a][1]:.1f}" x2="{pts[b][0]:.1f}" y2="{pts[b][1]:.1f}"/>'
                    for k, (a, b) in enumerate(edges))
    dots = "".join(f'<circle class="dot" id="{pre}s{j+1}" '
                   f'stroke="{C["green"] if j == i else C["blue"]}" cx="{pts[j][0]:.1f}" cy="{pts[j][1]:.1f}" '
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
        colour = C["green"] if j == 0 else C["muted"]
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
    # The row width is what the frame can hold: a landscape row has 1240px for 38px type, a
    # vertical row has about 860px, so the vertical cut takes fewer characters per row.
    row_chars = 52 if not VERTICAL else 38
    rows_max = max(2, min(5, (2 * RMAX_Y) // pitch + 1))
    # The caption is the paragraph's first sentence, so the list starts at the second one: a row
    # that repeats the caption wastes the frame.
    all_parts = sentences_in(text, rows_max + 1)
    parts = all_parts[1:] if len(all_parts) >= 2 else all_parts
    if len(parts) < 2:
        return None
    pre = f"b{i}"
    y0 = CY - (len(parts) - 1) * pitch // 2
    x0 = CX - (560 if not VERTICAL else 430)
    rows, js = [], []
    for j, part in enumerate(parts):
        rows.append(f'<div class="row" id="{pre}r{j+1}" style="left:{x0}px; top:{y0 + j * pitch}px; '
                    f'opacity:0"><span class="n">{j + 1}</span>&nbsp;&nbsp;{clip_words(part, row_chars)}</div>')
        js.append((f"#{pre}r{j+1}", "fade", 0.35 + j * 0.5, 0.45))
    return "".join(rows), "", js


def pack_orbit(i, text):
    """Shells of satellites travelling around a centre. The movement is the subject.

    Each shell is a group that turns once over the beat, so the constellation reads as a system in
    motion rather than a diagram. One satellite is drawn in green: this beat's subject.
    """
    pre = f"b{i}"
    shells = 3 if not VERTICAL else 2
    cy = CY - 30
    out = [svg_open()]
    js = []
    for s in range(shells):
        r = int((RMAX_X - 110) * (0.52 + 0.23 * s)) if not VERTICAL else int((RMAX_X - 80) * (0.48 + 0.25 * s))
        # The ring is an ellipse drawn by squashing the whole group, and the satellites are spun
        # inside it. Rotating an elliptical ARRANGEMENT would walk the satellites off the ring,
        # which is what the first build did; rotating inside a squashed group cannot.
        squash = 0.42 if not VERTICAL else 0.48
        out.append(f'<g transform="translate({CX} {cy}) scale(1 {squash})">'
                   f'<ellipse class="stroke" id="{pre}sh{s}" stroke="{C["muted"]}" cx="0" cy="0" '
                   f'rx="{r}" ry="{r}"/></g>')
        n = 4 + s * 2
        hero = (s == shells - 1)
        pts = "".join(
            f'<circle class="dot" id="{pre}s{s}_{j}" stroke="{C["green"] if (hero and j == 0) else C["blue"]}" '
            f'cx="{r * math.cos(2 * math.pi * j / n - 1.57):.1f}" '
            f'cy="{r * math.sin(2 * math.pi * j / n - 1.57):.1f}" '
            f'r="{20 if (hero and j == 0) else 11}"/>' for j in range(n))
        out.append(f'<g transform="translate({CX} {cy}) scale(1 {squash})">'
                   f'<g id="{pre}g{s}">{pts}</g></g>')
        js.append((f"#{pre}sh{s}", "fade", 0.15 + s * 0.12, 0.5))
        js.append({"sel": f"#{pre}g{s}", "kind": "spin", "delay": 0.15, "dur": 20 if not VERTICAL else 26,
                   "from": 0, "to": 360, "origin": "0px 0px"})
    out.append("</svg>")
    return "", "".join(out), js


def pack_race(i, text):
    """Two pulses over the same distance: the short path arrives while the long one is still going.

    Time is the subject, so the pack draws no figures of its own. The caption carries the numbers.
    """
    pre = f"b{i}"
    span = int(RMAX_X * 1.75) if not VERTICAL else int(RMAX_X * 1.5)
    x0 = CX - span // 2
    y_far = CY - 96 if not VERTICAL else CY - 130
    y_near = CY + 60 if not VERTICAL else CY + 110
    out = [svg_open()]
    lanes = [("long path", y_far, 8.4, C["blue"]), ("short path", y_near, 1.5, C["green"])]
    for k, (label, y, dur, colour) in enumerate(lanes):
        # The trail is deliberately dim and the pulse bright: same colour for both made the moving
        # dot invisible against its own trail, which is the whole point of the beat.
        out.append(f'<line class="stroke" id="{pre}tr{k}" stroke="{C["rule"]}" x1="{x0}" y1="{y}" '
                   f'x2="{x0 + span}" y2="{y}" style="opacity:0; transform-origin:{x0}px {y}px"/>')
        out.append(f'<circle class="dot" id="{pre}p{k}" stroke="{colour}" cx="{x0}" cy="{y}" r="22"/>')
    out.append("</svg>")
    # labels are plain divs, above the lanes, so they stay in the frame
    extra = "".join(
        f'<div class="nlabel" id="{pre}t{k}" style="left:{x0}px; top:{y - 56}px; opacity:0">{label}</div>'
        for k, (label, y, _, _) in enumerate(lanes))
    js = [(f"#{pre}lane0", "fade", 0.15, 0.4), (f"#{pre}lane1", "fade", 0.15, 0.4),
          (f"#{pre}fin0", "fade", 0.3, 0.4), (f"#{pre}fin1", "fade", 0.3, 0.4),
          (f"#{pre}t0", "fade", 0.3, 0.4), (f"#{pre}t1", "fade", 0.3, 0.4)]
    for k, (label, y, dur, colour) in enumerate(lanes):
        js.append({"sel": f"#{pre}tr{k}", "kind": "grow", "delay": 0.6, "dur": dur,
                   "to": {"scaleX": 1}})
        js.append({"sel": f"#{pre}p{k}", "kind": "move", "delay": 0.6, "dur": dur,
                   "from": {"x": 0}, "to": {"x": span}, "ease": "none"})
    return extra, "".join(out), js


def pack_hop(i, text):
    """A pulse travelling node to node, with each link lighting as it passes.

    The chain length follows the beat's position, so the same pack reads as a two satellite
    handover, a three leg path there and back, or a long chain across an ocean.
    """
    pre = f"b{i}"
    k = 2 if i <= 4 else (3 if i == 5 else 7)
    span = int(RMAX_X * 1.7) if not VERTICAL else int(RMAX_X * 1.45)
    x0 = CX - span // 2
    xs = [x0 + (span * j // (k - 1)) for j in range(k)]
    if k == 3:  # there and back: rises, crosses, drops to the ground
        ys = [CY + 150, CY - 150, CY + 150]
    else:
        ys = [CY - (40 if j % 2 else 0) for j in range(k)]
    out = [svg_open()]
    js = []
    for j in range(k - 1):
        out.append(f'<line class="stroke" id="{pre}l{j}" stroke="{C["rule"]}" x1="{xs[j]}" y1="{ys[j]}" '
                   f'x2="{xs[j + 1]}" y2="{ys[j + 1]}"/>')
        out.append(f'<line class="stroke" id="{pre}lv{j}" stroke="{C["blue"]}" x1="{xs[j]}" y1="{ys[j]}" '
                   f'x2="{xs[j + 1]}" y2="{ys[j + 1]}" style="opacity:0"/>')
    for j in range(k):
        out.append(f'<circle class="dot" id="{pre}n{j}" stroke="{C["blue"] if j < k - 1 else C["green"]}" '
                   f'cx="{xs[j]}" cy="{ys[j]}" r="26"/>')
    out.append(f'<circle class="dot" id="{pre}pulse" stroke="{C["yellow"]}" cx="{xs[0]}" cy="{ys[0]}" r="11"/>')
    out.append("</svg>")
    for j in range(k - 1):
        js.append((f"#{pre}l{j}", "dash", 0.2 + j * 0.05, 0.3))
    hop = 0.55 if k > 3 else 0.9
    for j in range(k - 1):
        step = {"x": xs[j + 1] - xs[j], "y": ys[j + 1] - ys[j]}
        if j == 0:
            js.append({"sel": f"#{pre}pulse", "kind": "move", "delay": 0.7, "dur": hop,
                       "from": {"x": 0, "y": 0, "opacity": 0}, "to": {**step, "opacity": 1},
                       "ease": "power1.inOut"})
        else:
            js.append({"sel": f"#{pre}pulse", "kind": "moveby", "delay": 0.7 + j * hop, "dur": hop,
                       "to": step, "ease": "power1.inOut"})
        js.append({"sel": f"#{pre}lv{j}", "kind": "fade", "delay": 0.7 + j * hop, "dur": hop * 0.8})
    return "", "".join(out), js


def pack_grid(i, text):
    """An antenna array rippling, with the beam angle tilting as the ripple passes.

    A grid of small elements is what a phased array actually is, and the ripple is what steering
    looks like: nothing moves, the timing changes.
    """
    pre = f"b{i}"
    cols, rows = (10, 6) if not VERTICAL else (8, 8)
    cw = 46 if not VERTICAL else 40
    gap = 10
    gw, gh = cols * cw + (cols - 1) * gap, rows * cw + (rows - 1) * gap
    gx, gy = CX - gw // 2, CY - gh // 2 - (30 if not VERTICAL else 40)
    out = [svg_open()]
    js = []
    cells = []
    for r_ in range(rows):
        for c_ in range(cols):
            x = gx + c_ * (cw + gap)
            y = gy + r_ * (cw + gap)
            cid = f"{pre}c{r_}_{c_}"
            cells.append((cid, (c_ + r_) / (cols + rows - 2)))
            out.append(f'<rect class="dot" id="{cid}" stroke="{C["blue"]}" x="{x}" y="{y}" '
                       f'width="{cw}" height="{cw}" rx="4" style="opacity:.35"/>')
    # the beam: two lines from the array centre, tilting as the ripple passes
    out.append(f'<g id="{pre}beam">'
               f'<line class="stroke" id="{pre}b1" stroke="{C["green"]}" x1="{CX}" y1="{gy + gh}" '
               f'x2="{CX - 120}" y2="{gy + gh + 190}"/>'
               f'<line class="stroke" id="{pre}b2" stroke="{C["green"]}" x1="{CX}" y1="{gy + gh}" '
               f'x2="{CX + 120}" y2="{gy + gh + 190}"/></g>')
    out.append("</svg>")
    for cid, t in cells:
        js.append({"sel": f"#{cid}", "kind": "pop", "delay": 0.25 + round(t * 2.2, 2), "dur": 0.7, "scale": 1.55})
    js.append((f"#{pre}beam", "fade", 1.6, 0.5))
    js.append({"sel": f"#{pre}beam", "kind": "rotate", "delay": 2.2, "dur": 3.0, "to": 18,
               "origin": f"{CX}px {gy + gh}px"})
    return "", "".join(out), js

def pack_scale(i, text):
    """Two magnitudes on one axis, drawn to scale, so the long one visibly dwarfs the short one.

    Reads the numbers out of the paragraph. Used where the argument is a comparison of sizes and a
    bar chart of every number in the sentence would be noise.
    """
    nums = numbers_in(text, 6)
    values = sorted({n["value"] for n in nums if n["value"] > 0})
    if len(values) < 2:
        return None
    lo, hi = values[0], values[-1]
    if hi == lo:
        return None
    unit = "ms" if "millisecond" in text.lower() else ("%" if "percent" in text.lower() else "")
    pre = f"b{i}"
    span = int(RMAX_X * 1.7) if not VERTICAL else int(RMAX_X * 1.4)
    x0 = CX - span // 2
    y_hi = CY - 70 if not VERTICAL else CY - 90
    y_lo = CY + 50 if not VERTICAL else CY + 80
    w_lo = max(16, int(span * lo / hi))
    def lbl(v):
        return f"{v:,.0f} {unit}".strip()
    out = [svg_open(),
           f'<line class="stroke" id="{pre}axis" stroke="{C["rule"]}" x1="{x0}" y1="{y_hi - 60}" '
           f'x2="{x0}" y2="{y_lo + 60}"/>',
           f'<line class="stroke" id="{pre}bhi" stroke="{C["blue"]}" x1="{x0}" y1="{y_hi}" '
           f'x2="{x0 + span}" y2="{y_hi}" style="opacity:0; transform-origin:{x0}px {y_hi}px"/>',
           f'<line class="stroke" id="{pre}blo" stroke="{C["green"]}" x1="{x0}" y1="{y_lo}" '
           f'x2="{x0 + w_lo}" y2="{y_lo}" style="opacity:0; transform-origin:{x0}px {y_lo}px"/>',
           "</svg>"]
    extra = (f'<div class="barlabel" id="{pre}thi" style="left:{x0 + 24}px; top:{y_hi - 58}px; opacity:0">{lbl(hi)}</div>'
             f'<div class="barlabel" id="{pre}tlo" style="left:{x0 + w_lo + 24}px; top:{y_lo - 58}px; opacity:0">{lbl(lo)}</div>')
    js = [(f"#{pre}axis", "fade", 0.2, 0.4),
          {"sel": f"#{pre}bhi", "kind": "grow", "delay": 0.5, "dur": 0.9},
          (f"#{pre}thi", "fade", 0.9, 0.4),
          {"sel": f"#{pre}blo", "kind": "grow", "delay": 1.6, "dur": 0.5},
          (f"#{pre}tlo", "fade", 1.9, 0.4)]
    return extra, "".join(out), js


PACK_FN = {"basic": pack_basic, "graph": pack_graph, "bars": pack_bars, "steps": pack_steps,
           "orbit": pack_orbit, "race": pack_race, "hop": pack_hop, "grid": pack_grid,
           "scale": pack_scale}

beats_html, beats_js, chosen = [], [], []
for i in range(N):
    start = STARTS[i]
    end = STARTS[i + 1] if i + 1 < N else END
    dur = round(end - start, 2)
    wanted = BEATS[i] if i < len(BEATS) else PACKS[i % len(PACKS)]
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
    for entry in js:
        if isinstance(entry, dict):
            sel = entry["sel"]
            at = round(start + entry["delay"], 2)
            d = entry.get("dur", 0.5)
            kind = entry["kind"]
            if kind == "spin":
                beats_js.append(f"    tl.fromTo('{sel}', {{ rotation: {entry['from']}, "
                                f"transformOrigin: '{entry['origin']}', immediateRender: false }}, "
                                f"{{ rotation: {entry['to']}, duration: {d}, ease: 'none' }}, {at});")
            elif kind == "move":
                frm = ", ".join(f"{k}: {v}" for k, v in entry["from"].items())
                to = ", ".join(f"{k}: {v}" for k, v in entry["to"].items())
                beats_js.append(f"    tl.fromTo('{sel}', {{ {frm}, immediateRender: false }}, "
                                f"{{ {to}, duration: {d}, ease: '{entry.get('ease', 'power1.out')}' }}, {at});")
            elif kind == "moveby":
                # a relative move keeps the element's authored position as its baseline, which a
                # second fromTo would otherwise overwrite for any seek before the tween runs
                bits = ", ".join(f'{k}: "+={v}"' for k, v in entry["to"].items() if v)
                beats_js.append(f"    tl.to('{sel}', {{ {bits}, duration: {d}, "
                                f"ease: '{entry.get('ease', 'power1.inOut')}' }}, {at});")
            elif kind == "grow":
                beats_js.append(f"    tl.fromTo('{sel}', {{ scaleX: 0, opacity: 0, "
                                f"transformOrigin: '0% 50%', immediateRender: false }}, "
                                f"{{ scaleX: 1, opacity: 1, duration: {d}, ease: 'none' }}, {at});")
            elif kind == "rotate":
                beats_js.append(f"    tl.to('{sel}', {{ rotation: {entry['to']}, "
                                f"transformOrigin: '{entry['origin']}', duration: {d}, "
                                f"ease: '{entry.get('ease', 'power1.inOut')}' }}, {at});")
            elif kind == "pop":
                s = entry.get("scale", 1.6)
                beats_js.append(f"    tl.fromTo('{sel}', {{ scale: 1, transformOrigin: '50% 50%', "
                                f"immediateRender: false }}, "
                                f"{{ scale: {s}, duration: {round(d / 2, 2)}, yoyo: true, repeat: 1, "
                                f"ease: 'power1.inOut' }}, {at});")
            else:
                beats_js.append(f"    tl.fromTo('{sel}', {{ opacity: 0 }}, {{ opacity: 1, duration: {d} }}, {at});")
            continue
        sel, kind, delay, d = entry
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
print(f"theme: {THEME}  bg {C['bg']}  ink {C['ink']}")
print(f"motifs asked for: {PACKS}")
print(f"motifs used:      {chosen}")
print("next: cd", P, "&& npm run check && npm run render")
