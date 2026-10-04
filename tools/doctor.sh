#!/bin/bash
# What this needs, and what is missing. It installs nothing.
# Run it after cloning: bash tools/doctor.sh
set -u

ok=0; bad=0
say()  { printf "  %-9s %s\n" "$1" "$2"; }
pass() { say "ok" "$1"; ok=$((ok+1)); }
fail() { say "MISSING" "$1"; echo "            install: $2"; bad=$((bad+1)); }

echo "syncframe doctor"
echo ""

# python 3.10 or newer
if command -v python3 >/dev/null 2>&1; then
  PV=$(python3 -c 'import sys;print("%d.%d"%sys.version_info[:2])' 2>/dev/null)
  if python3 -c 'import sys;sys.exit(0 if sys.version_info>=(3,10) else 1)' 2>/dev/null; then
    pass "python3 $PV"
  else
    fail "python3 $PV is too old, this needs 3.10 or newer" "brew install python@3.12   (macOS), or your package manager"
  fi
else
  fail "python3" "brew install python@3.12   (macOS), or your package manager"
fi

# ffmpeg and ffprobe
for t in ffmpeg ffprobe; do
  if command -v $t >/dev/null 2>&1; then pass "$t"; else fail "$t" "brew install ffmpeg   (macOS), sudo apt install ffmpeg   (Debian/Ubuntu)"; fi
done

# node 20 or newer, for the renderer
if command -v node >/dev/null 2>&1; then
  NV=$(node -v)
  if [ "$(printf '%s\n' v20.0.0 "$NV" | sort -V | head -1)" = "v20.0.0" ]; then
    pass "node $NV"
  else
    fail "node $NV is older than v20" "brew install node@20   (macOS), or nvm install 20"
  fi
else
  fail "node" "brew install node@20   (macOS), or nvm install 20"
fi
if command -v npx >/dev/null 2>&1; then pass "npx"; else fail "npx" "it comes with node"; fi

# the key: the one thing you bring
if [ -n "${GEMINI_API_KEY:-}" ]; then
  pass "GEMINI_API_KEY (in the environment)"
elif [ -f .env ] && grep -q "GEMINI_API_KEY" .env 2>/dev/null; then
  pass "GEMINI_API_KEY (in ./.env)"
else
  fail "GEMINI_API_KEY" "get one at https://aistudio.google.com/apikey then: export GEMINI_API_KEY=..."
fi

echo ""
if [ $bad -eq 0 ]; then
  echo "Everything is here. Next: python3 tools/tts.py examples/knowledge-graph-script.txt my-piece/vo"
else
  echo "$bad item(s) missing, $ok ok. Fix those, then run this again."
fi
exit $([ $bad -eq 0 ] && echo 0 || echo 1)
