#!/usr/bin/env bash
# ==============================================================================
# Jimha Product Showcase Capture Pipeline (Screenshots, 60fps Trailer & GIF)
# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Arafat Zahan (@kuasha420)
# ==============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
ASSETS_DIR="$ROOT_DIR/assets"
TEMP_DIR="$(mktemp -d)"

export YDOTOOL_SOCKET="/run/user/1000/.ydotool_socket"
export WAYLAND_DISPLAY="${WAYLAND_DISPLAY:-wayland-1}"
export DISPLAY="${DISPLAY:-:0}"
export XDG_DATA_HOME="$TEMP_DIR/data"

cleanup() {
    echo "[Clean] Tearing down background capture processes..."
    kill -SIGINT "${REC_PID:-}" 2>/dev/null || true
    kill -9 "${JIMHA_PID:-}" 2>/dev/null || true
    pkill -f "gpu-screen-recorder" 2>/dev/null || true
    pkill -f "$HOME/.local/bin/jimha" 2>/dev/null || true
    rm -rf "$TEMP_DIR"
}
trap cleanup EXIT

echo "=================================================="
echo "  JIMHA v2.0.0 PRODUCT SHOWCASE CAPTURE PIPELINE  "
echo "=================================================="

# 1. Setup sandboxed child progression profile with all 10 stickers
echo "[1/6] Initializing sandboxed progression profile with 10 badges..."
mkdir -p "$XDG_DATA_HOME/jimha"
mkdir -p "$TEMP_DIR/raw_screenshots"

cat << 'EOF' > "$XDG_DATA_HOME/jimha/profile.json"
{
  "child_name": "Jimha",
  "total_play_time_sec": 720,
  "total_key_presses": 156,
  "total_bubbles_popped": 42,
  "unlocked_stickers": [
    "first_spark",
    "bubble_popper",
    "jimha_crown",
    "jim_heart",
    "star_counter",
    "rainbow_explorer",
    "konami_champion",
    "melody_maestro",
    "chord_harmonizer",
    "lullaby_listener"
  ],
  "settings": {
    "esc_hold_seconds": 2.5,
    "parent_gate_seconds": 2.0,
    "audio_volume": 0.8,
    "instrument": "celesta"
  }
}
EOF

# 2. Verify dependencies
echo "[2/6] Verifying toolchain & capture daemon..."
pkill -f "$HOME/.local/bin/jimha" 2>/dev/null || true
sleep 0.5

if [ ! -S "$YDOTOOL_SOCKET" ]; then
    echo "Starting ydotool daemon..."
    systemctl --user start ydotool 2>/dev/null || ydotoold --socket-path="$YDOTOOL_SOCKET" &
    for i in {1..20}; do
        [ -S "$YDOTOOL_SOCKET" ] && break
        sleep 0.1
    done
fi

# 3. Launch production binary
echo "[3/6] Launching production Jimha binary..."
"$HOME/.local/bin/jimha" &
JIMHA_PID=$!
sleep 3.0

# Focus window
ydotool mousemove -a -x 1720 -y 720
sleep 0.2
ydotool click 0xC0
sleep 0.5

# 4. Start 60fps GPU Screen Recording with default audio
echo "[4/6] Starting 60 FPS hardware-accelerated video recording..."
RAW_VIDEO="$TEMP_DIR/raw_trailer.mp4"
gpu-screen-recorder -w screen -f 60 -a default_output -o "$RAW_VIDEO" &
REC_PID=$!
sleep 1.0

# 5. Interactive Gameplay & Screenshot Choreography
echo "[5/6] Executing interactive choreography & capturing raw screenshots..."

# A. Idle Attract Drift (floating bubbles, ambient music box)
echo "  -> [Shot 1] Capturing Sensory Lagoon Attract Mode..."
sleep 2.5
spectacle -b -n -o "$TEMP_DIR/raw_screenshots/screenshot_1_welcome.png"
sleep 0.5

# B. Bubble Popping Interaction (10 taps across screen)
echo "  -> Popping bubbles across lagoon..."
for i in {1..8}; do
    ydotool mousemove -a -x $((1000 + i * 140)) -y $((500 + (i % 3) * 120))
    ydotool click 0xC0
    sleep 0.18
done
sleep 0.5

# C. Queen Jimha Crown ('J')
echo "  -> [Shot 2] Queen Jimha ('J')..."
ydotool type "J"
sleep 0.35
spectacle -b -n -o "$TEMP_DIR/raw_screenshots/screenshot_2_jimha_crown.png"
sleep 1.2

# D. Jim Heart Easter Egg ('H')
echo "  -> [Shot 3] Jim Heart Easter Egg ('H')..."
ydotool type "H"
sleep 0.35
spectacle -b -n -o "$TEMP_DIR/raw_screenshots/screenshot_3_easter_egg.png"
sleep 1.2

# E. Spacebar Harmonic Supernova (Space)
echo "  -> [Shot 4] Cosmic Supernova / Harmonic Wonder (Space)..."
ydotool key 57:1 57:0
sleep 0.35
spectacle -b -n -o "$TEMP_DIR/raw_screenshots/screenshot_4_supernova.png"
sleep 1.2

# F. Toddler-Safe Radial Exit HUD (Shift + Esc hold)
echo "  -> [Shot 5] Toddler-Safe Radial Exit HUD (Hold Shift+Esc)..."
ydotool key 42:1 1:1
sleep 1.2
spectacle -b -n -o "$TEMP_DIR/raw_screenshots/screenshot_5_exit_hud.png"
ydotool key 1:0 42:0
sleep 0.8

# G. Golden Sticker Book with 10 Badges (F2)
echo "  -> [Shot 6] Golden Sticker Book (F2)..."
ydotool key 60:1 60:0
sleep 1.2
spectacle -b -n -o "$TEMP_DIR/raw_screenshots/screenshot_6_sticker_book.png"

# Tap unlocked badge to demonstrate fanfare replay
ydotool mousemove -a -x 1720 -y 720
ydotool click 0xC0
sleep 1.5

# Dismiss Sticker Book
ydotool key 1:1 1:0
sleep 0.8

# H. KWin Parent Virtual Switcher (Double Tap Up)
echo "  -> [Shot 7] Parent Virtual Switcher (Double Up)..."
ydotool key 103:1 103:0
sleep 0.08
ydotool key 103:1 103:0
sleep 0.5
spectacle -b -n -o "$TEMP_DIR/raw_screenshots/screenshot_7_virtual_switcher.png"
ydotool key 1:1 1:0
sleep 1.0

# Extra peaceful attract drift before cut
sleep 2.0

# Stop recording cleanly
echo "Stopping video recording..."
kill -SIGINT "$REC_PID" 2>/dev/null || true
wait "$REC_PID" 2>/dev/null || true
unset REC_PID

# Stop Jimha
kill -9 "$JIMHA_PID" 2>/dev/null || true
wait "$JIMHA_PID" 2>/dev/null || true
unset JIMHA_PID

# 6. Post-Processing & Optimization
echo "[6/6] Post-processing assets..."

# Optimize screenshots with ImageMagick to crisp 1920x804 (21:9 ultrawide)
for f in "$TEMP_DIR/raw_screenshots"/*.png; do
    fname="$(basename "$f")"
    echo "  -> Optimizing $fname..."
    magick "$f" -resize 1920x804 -quality 92 "$ASSETS_DIR/$fname"
done

# Transcode high-quality 1080p 60fps MP4 trailer
echo "  -> Transcoding 60fps video trailer (assets/demo_trailer.mp4)..."
ffmpeg -y -i "$RAW_VIDEO" \
  -vf "scale=1920:-2,format=yuv420p" \
  -c:v libx264 -preset slow -crf 20 \
  -c:a aac -b:a 192k \
  "$ASSETS_DIR/demo_trailer.mp4"

# Generate 2-pass palettegen animated preview GIF
echo "  -> Generating animated preview GIF (assets/demo_preview.gif)..."
ffmpeg -y -ss 00:00:02 -t 12 -i "$ASSETS_DIR/demo_trailer.mp4" \
  -vf "fps=14,scale=800:-1:flags=lanczos,split[s0][s1];[s0]palettegen=max_colors=128:stats_mode=diff[p];[s1][p]paletteuse=dither=bayer:bayer_scale=4" \
  "$ASSETS_DIR/demo_preview.gif"

echo "=================================================="
echo "  CAPTURE COMPLETE: All assets updated in:        "
echo "  $ASSETS_DIR                                     "
echo "=================================================="
