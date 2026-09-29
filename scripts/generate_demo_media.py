#!/usr/bin/env python3
"""
Generate Steam-like showcase media (screenshots, animated GIF preview, and MP4 trailer)
for JimHa's Key Smash Game.
"""

import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

# Enforce offscreen Qt platform
os.environ["QT_QPA_PLATFORM"] = "offscreen"

# Ensure repo root is on sys.path
REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from PyQt6.QtCore import QEvent, Qt
from PyQt6.QtGui import QColor, QImage, QKeyEvent, QPainter
from PyQt6.QtWidgets import QApplication

from jimha.main import JimHaGame


def render_game_frame(game: JimHaGame, width: int = 1280, height: int = 720) -> QImage:
    """Render the game widget onto a high-res QImage."""
    img = QImage(width, height, QImage.Format.Format_ARGB32)
    img.fill(QColor(0, 0, 0, 255))
    painter = QPainter(img)
    game.render(painter)
    painter.end()
    return img


def main():
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)

    width = 1280
    height = 720
    assets_dir = REPO_ROOT / "assets"
    assets_dir.mkdir(parents=True, exist_ok=True)
    temp_frames_dir = Path("/tmp/jimha_demo_frames")
    if temp_frames_dir.exists():
        shutil.rmtree(temp_frames_dir)
    temp_frames_dir.mkdir(parents=True, exist_ok=True)

    print("[1/3] Generating individual Steam-style screenshots...")
    game = JimHaGame(enable_audio=False)
    game.resize(width, height)
    game.show()

    # 1. Welcome Screen
    for _ in range(30):
        game._on_tick()
    img_welcome = render_game_frame(game, width, height)
    img_welcome.save(str(assets_dir / "screenshot_1_welcome.png"))
    print("  -> Saved screenshot_1_welcome.png")

    # 2. Key 'J' - Crown for JimHa
    press_j = QKeyEvent(QEvent.Type.KeyPress, Qt.Key.Key_J, Qt.KeyboardModifier.NoModifier, "j")
    game.keyPressEvent(press_j)
    for _ in range(12):  # let particles spread and spring bounce reach peak
        game._on_tick()
    img_j = render_game_frame(game, width, height)
    img_j.save(str(assets_dir / "screenshot_2_jimha_crown.png"))
    print("  -> Saved screenshot_2_jimha_crown.png")

    # 3. Key 'H' - Jim Heart Easter Egg
    press_h = QKeyEvent(QEvent.Type.KeyPress, Qt.Key.Key_H, Qt.KeyboardModifier.NoModifier, "h")
    game.keyPressEvent(press_h)
    for _ in range(12):
        game._on_tick()
    img_h = render_game_frame(game, width, height)
    img_h.save(str(assets_dir / "screenshot_3_easter_egg.png"))
    print("  -> Saved screenshot_3_easter_egg.png")

    # 4. Key Space - Cosmic Supernova
    press_space = QKeyEvent(QEvent.Type.KeyPress, Qt.Key.Key_Space, Qt.KeyboardModifier.NoModifier, " ")
    game.keyPressEvent(press_space)
    for _ in range(12):
        game._on_tick()
    img_space = render_game_frame(game, width, height)
    img_space.save(str(assets_dir / "screenshot_4_supernova.png"))
    print("  -> Saved screenshot_4_supernova.png")

    # 5. Exit Protection HUD (holding ESC)
    esc_down = QKeyEvent(QEvent.Type.KeyPress, Qt.Key.Key_Escape, Qt.KeyboardModifier.NoModifier)
    game.keyPressEvent(esc_down)
    # Simulate holding for 1.8 seconds (progress ~ 60%)
    game.esc_hold_progress = 0.62
    game.esc_press_start_time = time.time() - 1.86
    img_esc = render_game_frame(game, width, height)
    img_esc.save(str(assets_dir / "screenshot_5_exit_hud.png"))
    print("  -> Saved screenshot_5_exit_hud.png")

    # Reset game for trailer recording
    game.close()

    print("[2/3] Recording animated gameplay clip sequence...")
    rec_game = JimHaGame(enable_audio=False)
    rec_game.resize(width, height)
    rec_game.show()

    fps = 30
    dt_step = 1.0 / fps
    total_frames = 0

    def record_step(n_frames: int):
        nonlocal total_frames
        for _ in range(n_frames):
            rec_game._on_tick()
            frame_img = render_game_frame(rec_game, width, height)
            frame_img.save(str(temp_frames_dir / f"frame_{total_frames:04d}.png"))
            total_frames += 1

    # Phase 1: Welcome title twinkling (1.2s)
    record_step(int(1.2 * fps))

    # Phase 2: Press 'J' (JimHa!)
    press_j = QKeyEvent(QEvent.Type.KeyPress, Qt.Key.Key_J, Qt.KeyboardModifier.NoModifier, "j")
    rec_game.keyPressEvent(press_j)
    record_step(int(1.6 * fps))

    # Phase 3: Press 'H' (Easter Egg!)
    press_h = QKeyEvent(QEvent.Type.KeyPress, Qt.Key.Key_H, Qt.KeyboardModifier.NoModifier, "h")
    rec_game.keyPressEvent(press_h)
    record_step(int(1.6 * fps))

    # Phase 4: Press Space (Supernova!)
    press_sp = QKeyEvent(QEvent.Type.KeyPress, Qt.Key.Key_Space, Qt.KeyboardModifier.NoModifier, " ")
    rec_game.keyPressEvent(press_sp)
    record_step(int(1.6 * fps))

    # Phase 5: Hold ESC to exit
    esc_down = QKeyEvent(QEvent.Type.KeyPress, Qt.Key.Key_Escape, Qt.KeyboardModifier.NoModifier)
    rec_game.keyPressEvent(esc_down)
    rec_game.esc_press_start_time = time.time()
    # 2.0s hold
    for i in range(int(2.0 * fps)):
        rec_game.esc_hold_progress = min(0.95, (i + 1) / (fps * 2.2))
        rec_game._on_tick()
        frame_img = render_game_frame(rec_game, width, height)
        frame_img.save(str(temp_frames_dir / f"frame_{total_frames:04d}.png"))
        total_frames += 1

    print(f"  -> Generated {total_frames} frames in {temp_frames_dir}")

    print("[3/3] Encoding MP4 trailer and optimized looping GIF preview...")
    mp4_out = assets_dir / "demo_trailer.mp4"
    gif_out = assets_dir / "demo_preview.gif"

    # Encode MP4 (H.264, yuv420p for universal browser playback)
    cmd_mp4 = [
        "ffmpeg", "-y",
        "-framerate", str(fps),
        "-i", str(temp_frames_dir / "frame_%04d.png"),
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-movflags", "+faststart",
        str(mp4_out)
    ]
    subprocess.run(cmd_mp4, check=True)
    print(f"  -> Generated {mp4_out} ({mp4_out.stat().st_size / 1024:.1f} KB)")

    # Encode high quality looping GIF with palettegen (width 800 for optimal README load time)
    palette_file = temp_frames_dir / "palette.png"
    cmd_palette = [
        "ffmpeg", "-y",
        "-i", str(mp4_out),
        "-vf", "fps=18,scale=800:-1:flags=lanczos,palettegen=stats_mode=diff",
        str(palette_file)
    ]
    subprocess.run(cmd_palette, check=True)

    cmd_gif = [
        "ffmpeg", "-y",
        "-i", str(mp4_out),
        "-i", str(palette_file),
        "-lavfi", "fps=18,scale=800:-1:flags=lanczos [x]; [x][1:v] paletteuse=dither=bayer:bayer_scale=3",
        str(gif_out)
    ]
    subprocess.run(cmd_gif, check=True)
    print(f"  -> Generated {gif_out} ({gif_out.stat().st_size / (1024*1024):.2f} MB)")

    # Clean up frames
    shutil.rmtree(temp_frames_dir)
    print("[SUCCESS] All Steam-style media assets generated successfully!")


if __name__ == "__main__":
    main()
