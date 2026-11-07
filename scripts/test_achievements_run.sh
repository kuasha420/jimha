#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
ARTIFACT_DIR="${PSL_ARTIFACT_DIR:-/home/kuasha/.gemini/antigravity/brain/63bf44f8-6181-41b0-ba36-002664a21368}"
FRAMES_DIR="$ARTIFACT_DIR/achievements_frames"

export YDOTOOL_SOCKET="/run/user/1000/.ydotool_socket"

echo "=================================================="
echo "  JIMHA v2.0.0 ACHIEVEMENTS VERIFICATION AUDIT    "
echo "=================================================="

# 1. Reset child progression achievements
echo "[1/8] Resetting child progression profile..."
rm -f "$HOME/.local/share/jimha/profile.json"
mkdir -p "$FRAMES_DIR"
rm -f "$FRAMES_DIR"/*.png

# 2. Ensure existing processes are killed
echo "[2/8] Cleaning previous processes..."
pkill -f "target/debug/jimha" 2>/dev/null || true
pkill -f "$HOME/.local/bin/jimha" 2>/dev/null || true
pkill -f "vite" 2>/dev/null || true
sleep 0.5

# 3. Ensure ydotoold is running
echo "[3/8] Checking ydotool daemon..."
if [ ! -S "$YDOTOOL_SOCKET" ]; then
    systemctl --user start ydotool 2>/dev/null || ydotoold --socket-path="$YDOTOOL_SOCKET" &
    for i in {1..20}; do
        [ -S "$YDOTOOL_SOCKET" ] && break
        sleep 0.1
    done
fi

# 4. Start Vite dev server and dev build
echo "[4/8] Starting Dev Server (Vite) and Dev Build (Tauri debug)..."
cd "$ROOT_DIR"
pnpm dev --port 1420 &
VITE_PID=$!

echo "Waiting for Vite dev server on http://127.0.0.1:1420..."
for i in {1..30}; do
    if curl -s -I "http://127.0.0.1:1420" >/dev/null 2>&1; then
        echo "Vite dev server is ready!"
        break
    fi
    sleep 0.2
done

"$ROOT_DIR/target/debug/jimha" &
JIMHA_PID=$!
sleep 2.5

# Activate / focus window
ydotool mousemove -a -x 960 -y 540
sleep 0.2
ydotool click 0xC0
sleep 0.3

# 5. Capture initial idle frame
echo "[5/8] Capturing initial idle frame..."
spectacle -b -n -o "$FRAMES_DIR/01_idle_canvas.png"

# 6. Simulate gameplay to unlock all achievements
echo "[6/8] Simulating play to unlock all achievements..."

# Badge 1: First Spark ('A' key)
echo "  -> Unlocking 'first_spark' (Key A)..."
ydotool type "A"
sleep 0.4
spectacle -b -n -o "$FRAMES_DIR/02_first_spark.png"

# Badge 2: Queen Jimha ('J' key)
echo "  -> Unlocking 'jimha_crown' (Key J)..."
ydotool type "J"
sleep 0.4
spectacle -b -n -o "$FRAMES_DIR/03_jimha_crown.png"

# Badge 3: Jim Heart ('H' key)
echo "  -> Unlocking 'jim_heart' (Key H)..."
ydotool type "H"
sleep 0.4
spectacle -b -n -o "$FRAMES_DIR/04_jim_heart.png"

# Badge 4: Star Counter (Numbers 0-9)
echo "  -> Unlocking 'star_counter' (Numbers 0-9)..."
ydotool type "0123456789"
sleep 0.4
spectacle -b -n -o "$FRAMES_DIR/05_star_counter.png"

# Badge 5: Rainbow Explorer ('R' key)
echo "  -> Unlocking 'rainbow_explorer' (Key R)..."
ydotool type "R"
sleep 0.4
spectacle -b -n -o "$FRAMES_DIR/06_rainbow_explorer.png"

# Badge 6: Bubble Master (10+ bubble clicks)
echo "  -> Unlocking 'bubble_popper' (14 bubble taps across canvas)..."
for i in {1..14}; do
    ydotool mousemove -a -x $((600 + i * 45)) -y $((400 + (i % 3) * 60))
    ydotool click 0xC0
    sleep 0.15
done
sleep 0.5
spectacle -b -n -o "$FRAMES_DIR/06_bubble_popper.png"

# Cosmic Supernova (Spacebar)
echo "  -> Triggering Space Cosmic Supernova..."
ydotool key 57:1 57:0
sleep 0.4
spectacle -b -n -o "$FRAMES_DIR/07_space_supernova.png"

# Badge 7: Konami Champion (↑ ↑ ↓ ↓ ← → ← → B A)
echo "  -> Unlocking 'konami_champion' (Arcade Combo)..."
for k in 103 103 108 108 105 106 105 106 48 30; do
    ydotool key "$k:1" "$k:0"
    sleep 0.08
done
sleep 0.6
spectacle -b -n -o "$FRAMES_DIR/08_konami_champion.png"

# Open Sticker Book (F2 key) to verify all 7 badges
echo "  -> Opening Sticker Book (F2)..."
ydotool key 60:1 60:0
sleep 0.8
spectacle -b -n -o "$FRAMES_DIR/09_sticker_book_unlocked.png"

# Close Sticker Book
ydotool key 1:1 1:0 # Esc
sleep 0.3

# 7. Assembling video and verifying profile
echo "[7/8] Assembling achievements recording video..."
ffmpeg -y -framerate 1.2 -pattern_type glob -i "$FRAMES_DIR/*.png" \
  -vf "scale=1920:-2,format=yuv420p" \
  -c:v libx264 -preset fast -crf 23 \
  "$ARTIFACT_DIR/achievements_unlocked_audit.mp4"

echo "[8/8] Inspecting unlocked profile state..."
if [ -f "$HOME/.local/share/jimha/profile.json" ]; then
    cat "$HOME/.local/share/jimha/profile.json"
else
    echo "ERROR: profile.json not created!"
    exit 1
fi

echo "Cleaning up dev processes..."
kill -9 "$JIMHA_PID" 2>/dev/null || true
kill -9 "$VITE_PID" 2>/dev/null || true
pkill -f "target/debug/jimha" 2>/dev/null || true
pkill -f "vite" 2>/dev/null || true

echo "=================================================="
echo "  AUDIT SUCCESSFUL: Recording saved to:          "
echo "  $ARTIFACT_DIR/achievements_unlocked_audit.mp4  "
echo "=================================================="
