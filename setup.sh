#!/usr/bin/env bash
# One-time setup for a fresh machine: python deps + offline voices.
set -e
cd "$(dirname "$0")"
pip install --break-system-packages -q piper-tts cairosvg numpy pillow 2>&1 | grep -v -i warning || true
which ffmpeg >/dev/null || { echo "ffmpeg missing"; exit 1; }
mkdir -p voices
for v in en-us-ryan-medium en-us-lessac-medium; do
  if [ ! -f "voices/$v.onnx" ]; then
    curl -sSL -o "/tmp/$v.tar.gz" "https://github.com/rhasspy/piper/releases/download/v0.0.2/voice-$v.tar.gz"
    tar xzf "/tmp/$v.tar.gz" -C voices
  fi
done
python3 -c "import piper, cairosvg, numpy, PIL; print('setup ok')"
