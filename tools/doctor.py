#!/usr/bin/env python3
"""Check the tools needed to build a syncframe video. This script installs nothing."""
import os
import pathlib
import re
import shutil
import subprocess
import sys

def version(command):
    try:
        result = subprocess.run(command, capture_output=True, text=True, check=True)
    except (OSError, subprocess.CalledProcessError):
        return None
    return result.stdout.strip()


def env_file_candidates():
    candidates = []
    path = pathlib.Path.cwd()
    for _ in range(5):
        candidates.append(path / ".env")
        if path.parent == path:
            break
        path = path.parent
    candidates.extend((
        pathlib.Path("~/.env").expanduser(),
        pathlib.Path("~/.config/syncframe/.env").expanduser(),
    ))
    return candidates


def env_file_values():
    values = {}
    for path in env_file_candidates():
        if not path.is_file():
            continue
        for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
            match = re.match(r"\s*([A-Za-z0-9_]+)\s*=\s*(.*)", line)
            if match:
                values.setdefault(match.group(1), match.group(2).strip().strip("\"'"))
    return values


print("syncframe doctor")
print()
missing = []

python_version = sys.version_info
if python_version >= (3, 10):
    print(f"  ok        Python {python_version.major}.{python_version.minor}")
else:
    print(f"  MISSING   Python {python_version.major}.{python_version.minor} is too old; use 3.10 or newer")
    missing.append("Python 3.10 or newer")

for tool in ("ffmpeg", "ffprobe"):
    path = shutil.which(tool)
    if path:
        print(f"  ok        {tool}")
    else:
        print(f"  MISSING   {tool} is not on PATH")
        missing.append(tool)

node_version = version(["node", "--version"])
node_match = re.fullmatch(r"v?(\d+)(?:\.\d+)*(?:[-+].*)?", node_version or "")
if node_match and int(node_match.group(1)) >= 20:
    print(f"  ok        Node.js {node_version}")
else:
    detail = f" ({node_version})" if node_version else ""
    print(f"  MISSING   Node.js 20 or newer{detail}")
    missing.append("Node.js 20 or newer")

if shutil.which("npx"):
    print("  ok        npx")
else:
    print("  MISSING   npx (install Node.js 20 or newer)")
    missing.append("npx")

env_values = env_file_values()
gemini_key = any(
    os.environ.get(name) or env_values.get(name)
    for name in ("GEMINI_API_KEY", "GOOGLE_API_KEY")
)
elevenlabs_key = (
    bool(os.environ.get("ELEVENLABS_API_KEY")) and bool(os.environ.get("EL_VOICE_ID"))
) or bool(env_values.get("ELEVENLABS_API_KEY") and env_values.get("EL_VOICE_ID"))
if gemini_key:
    print("  ok        Gemini TTS credentials are configured")
elif elevenlabs_key:
    print("  ok        ElevenLabs TTS credentials are configured")
else:
    print("  note      No TTS credentials found; needed only to generate narration")

print()
if missing:
    print("Install the missing tools, then run this check again.")
    sys.exit(1)

print("Required tools are available. TTS credentials are optional until you generate narration.")
