"""
Command line interface for JimHa's Magical Key Smash Game.
Supports standalone launch, windowed mode, and optional remote Knot Mesh dispatch.
"""

import argparse
import os
import shutil
import subprocess
import sys


def parse_args():
    parser = argparse.ArgumentParser(
        prog="jimha",
        description="JimHa's Magical Key Smash Game - Fullscreen kid-friendly interactive wonderland.",
    )
    parser.add_argument(
        "--windowed",
        action="store_true",
        help="Run in windowed mode instead of fullscreen (useful for debugging)",
    )
    parser.add_argument(
        "--no-audio",
        action="store_true",
        help="Disable synthesized pentatonic chime audio",
    )
    parser.add_argument(
        "--mesh-target",
        metavar="NODE",
        help="Knot Mesh remote target node (e.g. desktop, laptop)",
    )
    return parser.parse_args()


def run():
    args = parse_args()

    # Remote launch over Knot Mesh if requested
    if args.mesh_target:
        knot_bin = shutil.which("knot") or os.path.expanduser("~/.local/bin/knot")
        if not os.path.exists(knot_bin) and not shutil.which("knot"):
            sys.stderr.write("Error: 'knot' CLI not found on PATH or ~/.local/bin/knot.\n")
            sys.exit(1)
        remote_cmd = (
            "WAYLAND_DISPLAY=${WAYLAND_DISPLAY:-wayland-0} "
            "DISPLAY=${DISPLAY:-:0} "
            "XDG_RUNTIME_DIR=${XDG_RUNTIME_DIR:-/run/user/1000} "
            "QT_QPA_PLATFORM=wayland "
            "nohup jimha > /tmp/jimha.log 2>&1 &"
        )
        print(f"[*] Dispatching JimHa game to @{args.mesh_target} via Knot Mesh...")
        res = subprocess.run([knot_bin, "exec", args.mesh_target, remote_cmd])
        sys.exit(res.returncode)

    # Local GUI execution
    from PyQt6.QtWidgets import QApplication
    from jimha.main import JimHaGame

    # Wayland platform priority
    if "QT_QPA_PLATFORM" not in os.environ and "WAYLAND_DISPLAY" in os.environ:
        os.environ["QT_QPA_PLATFORM"] = "wayland;xcb"

    app = QApplication(sys.argv)
    app.setApplicationName("jimha")
    app.setDesktopFileName("jimha")
    game = JimHaGame(enable_audio=not args.no_audio, is_windowed=args.windowed)

    if args.windowed:
        game.resize(1280, 720)
        game.show()
    else:
        game.showFullScreen()

    sys.exit(app.exec())


if __name__ == "__main__":
    run()
