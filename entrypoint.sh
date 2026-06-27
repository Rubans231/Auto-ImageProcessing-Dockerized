#!/usr/bin/env bash
set -e

echo "🚀 [CONTAINER] Booting headless ComfyUI backend via comfy-cli..."
# Launch comfy in background mode and pipe outputs to a system log file
comfy launch -- --listen 127.0.0.1 --port 8188 >/var/log/comfyui.log 2>&1 &

echo "⏳ [CONTAINER] Waiting for ComfyUI port initialization..."
until curl -s http://127.0.0.1:8188/history >/dev/null; do
  sleep 1
done
echo "🟢 [CONTAINER] Headless ComfyUI instance online and responding."

echo "🤖 [CONTAINER] Initializing internal Unix Domain Socket proxy engine..."
# Execute server.py as the primary container process
python3 src/server.py
