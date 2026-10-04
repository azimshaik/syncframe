#!/usr/bin/env python3
"""Generate the product explainer composition in the 3Blue1Brown visual language.

Dark canvas, monospace type, geometric diagrams drawn on, opacity layering for attention, deliberate
pacing, one idea per beat. Beats are placed from the narration's measured boundaries, so the visuals land on
the words.

Usage: python3 build_3b1b.py <project-dir>
"""
import json
import pathlib
import sys

P = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else ".")
T = json.loads((P / "assets/voice/timings.json").read_text())
S = T["starts"]
TOTAL = T["total"]
TAIL = 3.2
END = round(TOTAL + TAIL, 2)


def L(i):
    return S[i - 1]


B = {
    "b1": (L(1), L(2) - L(1)),
    "b2": (L(2), L(4) - L(2)),
    "b3": (L(4), L(5) - L(4)),
    "b4": (L(5), L(6) - L(5)),
    "b5": (L(6), L(8) - L(6)),
    "b6": (L(8), L(9) - L(8)),
    "b7": (L(9), L(13) - L(9)),
    "b8": (L(13), round(END - L(13), 2)),
}

CSS = """
      :root { --bg:#1C1C1C; --blue:#58C4DD; --green:#83C167; --yellow:#FFFF00;
              --dim:#888888; --ink:#ECECEC; }
      html, body { margin:0; padding:0; background:var(--bg); }
      .stage { position:relative; width:1920px; height:1080px; background:var(--bg); overflow:hidden; }
      .grid { position:absolute; inset:0; opacity:.05;
        background-image: linear-gradient(#ECECEC 1px, transparent 1px),
                          linear-gradient(90deg, #ECECEC 1px, transparent 1px);
        background-size: 120px 120px; }
      .clip { position:absolute; inset:0; }
      .mono { font-family:'IBMPlexMono',monospace; }
      .cap { position:absolute; left:140px; bottom:110px; font-family:'IBMPlexMono',monospace;
             font-size:34px; color:var(--ink); letter-spacing:.01em; }
      .cap .hi { color:var(--yellow); }
      .cap .g { color:var(--green); }
      .cap .b { color:var(--blue); }
      .tiny { position:absolute; right:140px; top:96px; font-family:'IBMPlexMono',monospace; font-size:22px;
              color:var(--dim); letter-spacing:.18em; text-transform:uppercase; }
      svg { display:block; }
      .boxpath { fill:none; stroke-width:5; stroke-linejoin:round; }
      .item { rx:3; }
      .listrow { position:absolute; font-family:'IBMPlexMono',monospace; font-size:26px; color:var(--ink); }
      .listrow .dot { color:var(--blue); }
      .listrow .date { color:var(--dim); }
      .q { position:absolute; font-family:'IBMPlexMono',monospace; font-size:132px; color:var(--yellow); }
      .counter { position:absolute; right:150px; bottom:120px; font-family:'IBMPlexMono',monospace;
                 font-size:30px; color:var(--dim); }
      .counter b { color:var(--ink); font-weight:500; }
      .search { position:absolute; left:50%; top:50%; transform:translate(-50%,-50%);
                font-family:'IBMPlexMono',monospace; font-size:44px; color:var(--ink); }
      .search .caret { color:var(--yellow); }
      .verdict { position:absolute; left:50%; font-family:'IBMPlexMono',monospace; font-size:40px;
                 color:var(--green); transform:translateX(-50%); }
      .verb { position:absolute; font-family:'IBMPlexMono',monospace; font-size:56px; color:var(--ink); }
      .word { position:absolute; font-family:'IBMPlexMono',monospace; font-size:64px; color:var(--blue);
              font-weight:500; letter-spacing:-.01em; }
      .doc { position:absolute; border:3px solid var(--green); border-radius:6px; }
      .docrow { position:absolute; font-family:'IBMPlexMono',monospace; font-size:22px; color:var(--ink); }
"""


def box_svg(w=260, h=200, lid=True):
    """A box glyph: outline drawn on, with a lid line. Used for the single-box beats."""
    return f"""
      <svg width="{w}" height="{h}" viewBox="0 0 {w} {h}">
        <path class="boxpath" id="b1body" stroke="#58C4DD" d="M10 {h*0.32} L{w/2} 10 L{w-10} {h*0.32} L{w-10} {h-10} L{10} {h-10} Z" />
        <path class="boxpath" id="b1lid" stroke="#58C4DD" d="M10 {h*0.32} L{w/2} {h*0.56} L{w-10} {h*0.32}" />
      </svg>"""


HTML = f"""<!doctype html>
<html><head><meta charset="utf-8">
<style>
@font-face {{ font-family:'IBMPlexMono'; src:url('assets/fonts/IBMPlexMono-Regular.ttf'); }}
{CSS}
</style></head>
<body>
<div class="stage" id="stage" data-composition-id="main" data-width="1920" data-height="1080">
  <div class="grid"></div>

  <!-- 1: every box is a black box -->
  <div class="clip" id="beat-b1" data-start="{B['b1'][0]}" data-duration="{B['b1'][1]}" data-track-index="1">
    <div style="position:absolute; left:50%; top:45%; transform:translate(-50%,-50%);">
      <div id="b1box">{box_svg(420, 320)}</div>
    </div>
    <div class="q" id="b1q" style="left:50%; top:45%; transform:translate(-50%,-50%); font-size:150px;">?</div>
    <div class="cap" id="b1cap">every box is a <span class="hi">black box</span></div>
  </div>

  <!-- 2: open you know, sealed you do not -->
  <div class="clip" id="beat-b2" data-start="{B['b2'][0]}" data-duration="{B['b2'][1]}" data-track-index="2">
    <div style="position:absolute; left:50%; top:42%; transform:translate(-50%,-50%);">
      <svg width="420" height="320" viewBox="0 0 420 320">
        <path class="boxpath" id="b2body" stroke="#58C4DD" d="M20 110 L210 20 L400 110 L400 300 L20 300 Z" />
        <g id="b2items">
          <rect class="item" x="70" y="140" width="70" height="52" fill="#83C167" opacity="1"/>
          <rect class="item" x="160" y="150" width="96" height="40" fill="#58C4DD" opacity="1"/>
          <rect class="item" x="275" y="138" width="80" height="56" fill="#FFFF00" opacity="1"/>
          <rect class="item" x="110" y="215" width="120" height="46" fill="#58C4DD" opacity="1"/>
          <rect class="item" x="250" y="225" width="86" height="38" fill="#83C167" opacity="1"/>
        </g>
        <path class="boxpath" id="b2lid" stroke="#58C4DD" d="M20 110 L210 200 L400 110" />
      </svg>
    </div>
    <div class="cap" id="b2cap1">while it is open, you know what is inside</div>
    <div class="cap" id="b2cap2" style="opacity:0;">sealed, <span class="hi">that record is gone</span></div>
  </div>

  <!-- 3: the garage, 24 boxes -->
  <div class="clip" id="beat-b3" data-start="{B['b3'][0]}" data-duration="{B['b3'][1]}" data-track-index="3">
    <div id="garage" style="position:absolute; left:150px; top:230px; display:grid;
         grid-template-columns:repeat(8, 120px); gap:34px;"></div>
    <div class="cap" id="b3cap">twenty four boxes, one <span class="hi">staple gun</span></div>
  </div>

  <!-- 4: opening one at a time -->
  <div class="clip" id="beat-b4" data-start="{B['b4'][0]}" data-duration="{B['b4'][1]}" data-track-index="3">
    <div id="garage2" style="position:absolute; left:150px; top:230px; display:grid;
         grid-template-columns:repeat(8, 120px); gap:34px;"></div>
    <div class="counter" id="b4count"><b>0</b> opened</div>
    <div class="cap" id="b4cap" style="opacity:0;">the question is free, the answer is not</div>
  </div>

  <!-- 5: four seconds, one photo -->
  <div class="clip" id="beat-b5" data-start="{B['b5'][0]}" data-duration="{B['b5'][1]}" data-track-index="3">
    <div style="position:absolute; left:190px; top:300px;">
      <svg width="360" height="288" viewBox="0 0 360 288">
        <path class="boxpath" id="b5body" stroke="#58C4DD" d="M18 96 L180 18 L342 96 L342 270 L18 270 Z" />
        <path class="boxpath" id="b5lid" stroke="#58C4DD" d="M18 96 L180 168 L342 96" />
      </svg>
    </div>
    <div id="b5list"></div>
    <div class="cap" id="b5cap1" style="opacity:0;">four seconds, while the box is still open</div>
    <div class="cap" id="b5cap2" style="opacity:0;">the box stops being a container and becomes a <span class="b">record</span></div>
  </div>

  <!-- 6: the lookup -->
  <div class="clip" id="beat-b6" data-start="{B['b6'][0]}" data-duration="{B['b6'][1]}" data-track-index="3">
    <div id="garage3" style="position:absolute; left:150px; top:170px; display:grid;
         grid-template-columns:repeat(8, 120px); gap:34px;"></div>
    <div class="search" id="b6search" style="top:74%;"><span id="b6typed"></span><span class="caret">_</span></div>
    <div class="verdict" id="b6verdict" style="top:86%; opacity:0;">box 6</div>
  </div>

  <!-- 7: the harder question -->
  <div class="clip" id="beat-b7" data-start="{B['b7'][0]}" data-duration="{B['b7'][1]}" data-track-index="3">
    <div style="position:absolute; left:190px; top:280px;">
      <svg width="340" height="272" viewBox="0 0 340 272" style="transform:rotate(-4deg);">
        <path class="boxpath" id="b7body" stroke="#FFFF00" d="M17 90 L170 16 L323 90 L323 255 L17 255 Z" />
        <path class="boxpath" id="b7lid" stroke="#FFFF00" d="M17 90 L170 158 L323 90" />
      </svg>
    </div>
    <div id="b7list"></div>
    <div class="doc" id="b7doc" style="opacity:0; left:1120px; top:300px; width:560px; height:320px;"></div>
    <div class="docrow" id="b7doct" style="opacity:0; left:1160px; top:330px; color:#83C167;">itemised export</div>
    <div id="b7rows"></div>
    <div class="cap" id="b7cap1">finding it is only the first question</div>
    <div class="cap" id="b7cap2" style="opacity:0;">an insurance form asks you to <span class="hi">prove what you owned</span></div>
  </div>

  <!-- 8: three verbs -->
  <div class="clip" id="beat-b8" data-start="{B['b8'][0]}" data-duration="{B['b8'][1]}" data-track-index="3">
    <div class="verb" id="v1" style="left:240px; top:420px;">photograph the box</div>
    <div class="verb" id="v2" style="left:240px; top:520px;">search the list</div>
    <div class="verb" id="v3" style="left:240px; top:620px;">export the proof</div>
    <div class="word" id="w1" style="left:1320px; top:520px;">the product</div>
  </div>

  <audio id="vo" src="assets/voice/vo-fast.wav" data-start="0" data-duration="{TOTAL}" data-volume="1"></audio>
</div>

<script src="https://cdn.jsdelivr.net/npm/gsap@3.12.5/dist/gsap.min.js"></script>
<script>
  const T = {json.dumps({k: round(v[0], 2) for k, v in B.items()})};
  const END = {END};

  // a box glyph as a function of its state, so every grid uses the same drawing
  function boxSVG(state) {{
    const stroke = state === 'open' ? '#555555' : (state === 'found' ? '#83C167' : '#58C4DD');
    return `<svg width="120" height="104" viewBox="0 0 120 104">
      <path d="M8 36 L60 10 L112 36 L112 96 L8 96 Z" fill="none" stroke="${{stroke}}" stroke-width="3.5"/>
      <path d="M8 36 L60 58 L112 36" fill="none" stroke="${{stroke}}" stroke-width="3.5"/>
    </svg>`;
  }}

  function fillGrid(id, count, state) {{
    const el = document.getElementById(id);
    el.innerHTML = '';
    const made = [];
    for (let i = 0; i < count; i++) {{
      const d = document.createElement('div');
      d.className = 'slot';
      d.dataset.i = i;
      d.style.opacity = state === 'sealed' ? '0.32' : '1';
      d.innerHTML = boxSVG(state === 'sealed' ? 'sealed' : 'live');
      el.appendChild(d);
      made.push(d);
    }}
    return made;
  }}

  function addList(container, rows, startIndex, withDate) {{
    const el = document.getElementById(container);
    const made = [];
    rows.forEach((r, k) => {{
      const d = document.createElement('div');
      d.className = 'listrow';
      d.id = `${{container}}-r${{k}}`;
      d.style.left = (withDate ? 1140 : 560) + 'px';
      d.style.top = (withDate ? 400 + k * 46 : 250 + k * 56) + 'px';
      d.style.opacity = '0';
      d.innerHTML = withDate
        ? `<span class="dot">·</span> ${{r}} <span class="date">&nbsp;&nbsp;03 · 2026</span>`
        : `<span class="dot">·</span> ${{r}}`;
      el.appendChild(d);
      made.push(d);
    }});
    return made;
  }}

  const ITEMS = ['staple gun', 'cordless drill', 'extension cables', 'paint tins', 'tool roll'];
  const PROOF = ['cordless drill', 'paint tins', 'tool roll'];

  fillGrid('garage', 24, 'sealed');
  const SLOTS4 = fillGrid('garage2', 24, 'live');
  const SLOTS6 = fillGrid('garage3', 24, 'live');
  const LIST5 = addList('b5list', ITEMS, 0, false);
  const LIST7 = addList('b7list', PROOF, 0, false);
  const ROWS7 = addList('b7rows', PROOF, 0, true);

  const tl = gsap.timeline({{ paused: true }});
  const drawable = (sel) => {{
    const path = document.querySelector(sel);
    const len = path.getTotalLength();
    gsap.set(path, {{ strokeDasharray: len, strokeDashoffset: len }});
    return {{ path, len }};
  }};

  // ---- beat 1: the box is drawn, the question appears
  {{
    const body = drawable('#b1body'), lid = drawable('#b1lid');
    tl.fromTo('#beat-b1', {{ opacity: 0 }}, {{ opacity: 1, duration: .5 }}, T.b1);
    tl.to('#b1body', {{ strokeDashoffset: 0, duration: 1.1, ease: 'power1.inOut' }}, T.b1 + .1);
    tl.to('#b1lid', {{ strokeDashoffset: 0, duration: .8, ease: 'power1.inOut' }}, T.b1 + .9);
    tl.fromTo('#b1q', {{ opacity: 0, scale: .6 }}, {{ opacity: 1, scale: 1, duration: .7, ease: 'power2.out' }}, T.b1 + 1.5);
    tl.fromTo('#b1cap', {{ opacity: 0, y: 14 }}, {{ opacity: 1, y: 0, duration: .6 }}, T.b1 + 1.7);
  }}

  // ---- beat 2: contents bright, then sealed and dimmed
  {{
    tl.fromTo('#beat-b2', {{ opacity: 0 }}, {{ opacity: 1, duration: .5 }}, T.b2);
    tl.fromTo('#b2cap1', {{ opacity: 0 }}, {{ opacity: 1, duration: .5 }}, T.b2 + .15);
    tl.to('#b2items rect', {{ opacity: 0.15, duration: .9, stagger: .06, ease: 'power1.inOut' }}, T.b2 + 4.4);
    tl.fromTo('#b2cap1', {{ opacity: 1 }}, {{ opacity: 0, duration: .4 }}, T.b2 + 4.6);
    tl.fromTo('#b2cap2', {{ opacity: 0 }}, {{ opacity: 1, duration: .5 }}, T.b2 + 4.9);
  }}

  // ---- beat 3: the garage appears
  {{
    tl.fromTo('#beat-b3', {{ opacity: 0 }}, {{ opacity: 1, duration: .5 }}, T.b3);
    tl.fromTo('#beat-b3 .slot', {{ opacity: 0, y: 16 }},
              {{ opacity: .32, y: 0, duration: .45, stagger: .035, ease: 'power2.out' }}, T.b3 + .1);
    tl.fromTo('#b3cap', {{ opacity: 0, y: 14 }}, {{ opacity: 1, y: 0, duration: .5 }}, T.b3 + .5);
  }}

  // ---- beat 4: opening them one at a time
  {{
    tl.fromTo('#beat-b4', {{ opacity: 0 }}, {{ opacity: 1, duration: .4 }}, T.b4);
    const openTimes = [0.1, 0.55, 1.0, 1.45, 1.9, 2.35, 2.8, 3.25, 3.7];
    openTimes.forEach((t, i) => {{
      const cell = SLOTS4[i];
      tl.to(cell, {{ opacity: .3, duration: .3 }}, T.b4 + t);
      tl.call(() => {{
        cell.innerHTML = boxSVG('open');
        document.getElementById('b4count').innerHTML = '<b>' + (i + 1) + '</b> opened';
      }}, null, T.b4 + t + .05);
    }});
    tl.fromTo('#b4cap', {{ opacity: 0 }}, {{ opacity: 1, duration: .5 }}, T.b4 + 4.4);
  }}

  // ---- beat 5: the photo, then the record
  {{
    tl.fromTo('#beat-b5', {{ opacity: 0 }}, {{ opacity: 1, duration: .4 }}, T.b5);
    tl.fromTo('#b5cap1', {{ opacity: 0 }}, {{ opacity: 1, duration: .5 }}, T.b5 + .2);
    tl.to('#beat-b5', {{ backgroundColor: 'rgba(255,255,255,0.10)', duration: .12 }}, T.b5 + 2.6);
    tl.to('#beat-b5', {{ backgroundColor: 'rgba(255,255,255,0)', duration: .5 }}, T.b5 + 2.75);
    tl.fromTo('#b5body', {{ stroke: '#FFFF00' }}, {{ stroke: '#58C4DD', duration: 1.0 }}, T.b5 + 2.8);
    ITEMS.forEach((it, k) => {{
      tl.fromTo(LIST5[k], {{ opacity: 0, x: -18 }},
                {{ opacity: 1, x: 0, duration: .45, ease: 'power2.out' }}, T.b5 + 3.2 + k * .28);
    }});
    tl.fromTo('#b5cap1', {{ opacity: 1 }}, {{ opacity: 0, duration: .35 }}, T.b5 + 4.6);
    tl.fromTo('#b5cap2', {{ opacity: 0 }}, {{ opacity: 1, duration: .5 }}, T.b5 + 4.9);
  }}

  // ---- beat 6: the lookup
  {{
    tl.fromTo('#beat-b6', {{ opacity: 0 }}, {{ opacity: 1, duration: .4 }}, T.b6);
    tl.fromTo('#beat-b6 .slot', {{ opacity: .32 }}, {{ opacity: .32, duration: .3 }}, T.b6);
    const word = 'staple gun';
    for (let i = 1; i <= word.length; i++) {{
      tl.call(() => {{ document.getElementById('b6typed').textContent = word.slice(0, i); }},
              null, T.b6 + .35 + i * .075);
    }}
    tl.call(() => {{
      const el = SLOTS6[5];
      el.innerHTML = boxSVG('found');
      el.style.opacity = '1';
    }}, null, T.b6 + 1.5);
    tl.fromTo('#b6verdict', {{ opacity: 0, y: 10 }}, {{ opacity: 1, y: 0, duration: .45 }}, T.b6 + 1.7);
  }}

  // ---- beat 7: the harder question
  {{
    tl.fromTo('#beat-b7', {{ opacity: 0 }}, {{ opacity: 1, duration: .4 }}, T.b7);
    tl.fromTo('#b7body', {{ strokeDasharray: 1200, strokeDashoffset: 0 }},
              {{ strokeDasharray: 1200, strokeDashoffset: 0, duration: .3 }}, T.b7);
    tl.fromTo('#b7cap1', {{ opacity: 0 }}, {{ opacity: 1, duration: .5 }}, T.b7 + .2);
    tl.fromTo('#b7cap1', {{ opacity: 1 }}, {{ opacity: 0, duration: .4 }}, T.b7 + 4.0);
    tl.fromTo('#b7cap2', {{ opacity: 0 }}, {{ opacity: 1, duration: .5 }}, T.b7 + 4.3);
    PROOF.forEach((pr, k) => {{
      tl.fromTo(LIST7[k], {{ opacity: 0, x: -16 }},
                {{ opacity: 1, x: 0, duration: .45 }}, T.b7 + 1.0 + k * .3);
    }});
    tl.fromTo('#b7doc', {{ opacity: 0 }}, {{ opacity: .9, duration: .6 }}, T.b7 + 12.0);
    tl.fromTo('#b7doct', {{ opacity: 0 }}, {{ opacity: 1, duration: .4 }}, T.b7 + 12.3);
    PROOF.forEach((p, k) => {{
      tl.fromTo(ROWS7[k], {{ opacity: 0, x: -14 }},
                {{ opacity: 1, x: 0, duration: .4 }}, T.b7 + 12.7 + k * .3);
    }});
  }}

  // ---- beat 8: the three verbs
  {{
    tl.fromTo('#beat-b8', {{ opacity: 0 }}, {{ opacity: 1, duration: .5 }}, T.b8);
    ['#v1', '#v2', '#v3'].forEach((sel, k) => {{
      tl.fromTo(sel, {{ opacity: 0, x: -22 }}, {{ opacity: 1, x: 0, duration: .55, ease: 'power2.out' }},
                T.b8 + .2 + k * .9);
    }});
    tl.fromTo('#w1', {{ opacity: 0, x: 16 }}, {{ opacity: 1, x: 0, duration: .7, ease: 'power2.out' }}, T.b8 + 2.6);
  }}

  tl.to({{}}, {{ duration: .1 }}, END - 0.1);
  window.__timelines = window.__timelines || {{}};
  window.__timelines.main = tl;
</script>
</body></html>
"""

(P / "index.html").write_text(HTML)
print(f"wrote {P/'index.html'}")
print(f"end {END}s | beats:", {k: v for k, v in B.items()})
