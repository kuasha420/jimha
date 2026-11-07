#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
ARTIFACT_DIR="${PSL_ARTIFACT_DIR:-/home/kuasha/.gemini/antigravity/brain/63bf44f8-6181-41b0-ba36-002664a21368}"

echo "=== JIMHA FORMALIZED AUDIT PIPELINE ==="
echo "1. Running unit test suites..."
pnpm test
cargo test --manifest-path "$ROOT_DIR/src-tauri/Cargo.toml"

echo "2. Building and installing latest release binary..."
pnpm build
cargo build --manifest-path "$ROOT_DIR/src-tauri/Cargo.toml" --release
install -Dm755 "$ROOT_DIR/target/release/jimha" "$HOME/.local/bin/jimha"

echo "3. Starting game daemon..."
pkill -f "$HOME/.local/bin/jimha" 2>/dev/null || true
"$HOME/.local/bin/jimha" &
JIMHA_PID=$!
sleep 1.2

echo "4. Capturing idle frame..."
spectacle -b -n -o "$ARTIFACT_DIR/audit_01_idle.png"

echo "5. Verifying PipeWire audio stream..."
wpctl status | grep -A 2 -i "jimha" || echo "Warning: jimha audio stream not yet registered"

echo "6. Ingesting test keys via ydotool..."
export YDOTOOL_SOCKET="/run/user/1000/.ydotool_socket"
if [ ! -S "$YDOTOOL_SOCKET" ]; then
    ydotoold --socket-path="$YDOTOOL_SOCKET" &
    sleep 0.5
fi

ydotool type "J"
sleep 0.2
spectacle -b -n -o "$ARTIFACT_DIR/audit_02_j.png"

ydotool key 57:1 57:0
sleep 0.2
spectacle -b -n -o "$ARTIFACT_DIR/audit_03_space.png"

echo "7. Generating low-FPS audit clip..."
ffmpeg -y -framerate 1 -pattern_type glob -i "$ARTIFACT_DIR/audit_0*.png" -vf "scale=1280:-1" -c:v libx264 -pix_fmt yuv420p "$ARTIFACT_DIR/audit_video_clip.mp4" 2>/dev/null

echo "8. Cleaning up test process..."
kill -9 "$JIMHA_PID" 2>/dev/null || true

echo "=== AUDIT COMPLETE: Evidence saved to $ARTIFACT_DIR ==="
