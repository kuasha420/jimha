#!/usr/bin/env python3
"""
JimHa's Magical Key Smash Game
A fullscreen, kid-friendly interactive wonderland for JimHa.
Keys pop up in giant, vibrant animations with companion words, emojis, particle bursts, and soothing chimes.
Exit protection: Press and hold ESC continuously for 3.0 seconds to quit.
"""

import json
import logging
import math
import random
import re
import shutil
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger("jimha")

from PyQt6.QtCore import QEvent, QPointF, QRectF, Qt, QTimer
from PyQt6.QtGui import (
    QCloseEvent,
    QColor,
    QFocusEvent,
    QFont,
    QFontMetrics,
    QIcon,
    QKeyEvent,
    QLinearGradient,
    QMouseEvent,
    QPainter,
    QPainterPath,
    QPaintEvent,
    QPen,
    QPixmap,
    QRadialGradient,
    QShowEvent,
)
from PyQt6.QtWidgets import QApplication, QWidget

# Import sound bank
try:
    from jimha.sound_synth import SoundBank
except ImportError:
    from sound_synth import SoundBank

# PyQt6 SIP binding compatibility:
# In Qt C++ and PySide6, QTimer.singleShot accepts an optional receiver context object
# (QTimer.singleShot(msec, context, slot)) to bind timer lifecycle to receiver.
# PyQt6 omitted this overload from its SIP wrapper. We adapt it transparently.
_orig_single_shot = QTimer.singleShot


def _compat_single_shot(msec, *args):
    if len(args) == 2 and not isinstance(args[0], Qt.TimerType):
        return _orig_single_shot(msec, args[1])
    return _orig_single_shot(msec, *args)


QTimer.singleShot = staticmethod(_compat_single_shot)

# High-contrast, joyful pastel & neon palette
PALETTE = [
    QColor("#FF4081"),  # Bubblegum Pink
    QColor("#00E676"),  # Electric Mint
    QColor("#FFD600"),  # Sunshine Yellow
    QColor("#00E5FF"),  # Cyan Aqua
    QColor("#FF6D00"),  # Bright Orange
    QColor("#E040FB"),  # Vibrant Lavender
    QColor("#7C4DFF"),  # Royal Violet
    QColor("#FF5252"),  # Coral Red
    QColor("#1DE9B6"),  # Seafoam Teal
]

# Alphabet dictionary with emojis & companion words
#
# 💖 THE "JIM HEART" EASTER EGG LORE:
# Born during JimHa's very first agentic pair programming session with her father (Arafat Zahan).
# The initial challenge was spoken via Bangla voice dictation from a handheld Steam Deck,
# instructing an autonomous AI agent over the Knot Mesh to project a game onto the Desktop PC:
#   "ডিয়ার এজেন্ট, তুমি এমন একটা গেম বানাও যেটা আমার 16-17 বছর বয়সী মেয়ে জিম হার্ট এর জন্য..."
#
# The speech-to-text engine charmingly mistranslated "JimHa" (জিমহা) into "Jim Heart" (জিম হার্ট)
# (and 16-17 months as years). Taking the prompt literally, the agent scaffolded `apps/jimheart`
# with key 'J' set to ("💎", "Jim Heart!").
#
# Upon seeing the prototype, her father clarified:
#   "jimha -----Not JimHa, but now that we have put it, let's keep it as a Easter egg.
#    But my daughter's name is the previously mentioned JimHa."
#
# Key 'J' was rightfully crowned with ("👑", "JimHa! ✨"), while 'H' was immortalized as
# ("💖", "Jim Heart (Easter Egg! 💖)") to preserve the serendipitous spark of their first session!
ALPHABET_COMPANIONS = {
    "A": ("🍎", "Apple"),
    "B": ("🦋", "Butterfly"),
    "C": ("🐱", "Cat"),
    "D": ("🐶", "Dog"),
    "E": ("🐘", "Elephant"),
    "F": ("🌸", "Flower"),
    "G": ("🎸", "Guitar"),
    "H": ("💖", "Jim Heart (Easter Egg! 💖)"),  # The legendary voice-dictation spark!
    "I": ("🍦", "Ice Cream"),
    "J": ("👑", "JimHa! ✨"),  # The queen herself!
    "K": ("🪁", "Kite"),
    "L": ("🦁", "Lion"),
    "M": ("🌙", "Moon"),
    "N": ("🌈", "Nature"),
    "O": ("🦉", "Owl"),
    "P": ("🐼", "Panda"),
    "Q": ("👑", "Queen"),
    "R": ("🚀", "Rocket"),
    "S": ("⭐", "Star"),
    "T": ("🐯", "Tiger"),
    "U": ("🦄", "Unicorn"),
    "V": ("🎻", "Violin"),
    "W": ("🌊", "Wave"),
    "X": ("🎁", "Xylophone"),
    "Y": ("⛵", "Yacht"),
    "Z": ("🦓", "Zebra"),
}


@dataclass
class Particle:
    x: float
    y: float
    vx: float
    vy: float
    size: float
    color: QColor
    shape: str  # 'star', 'circle', 'heart', 'confetti'
    life: float  # 0.0 to 1.0 (1.0 = brand new, 0.0 = dead)
    decay_rate: float
    rotation: float
    rot_speed: float


@dataclass
class FloatingBubble:
    x: float
    y: float
    vx: float
    vy: float
    radius: float
    color: QColor
    life: float


class RekkaBuffer:
    """Arcade combo buffer tracking key sequences with timeout decay."""

    def __init__(self, decay_timeout: float = 0.8):
        self.decay_timeout = decay_timeout
        self.buffer: List[str] = []
        self.last_input_time: float = 0.0

    def add(self, key_token: str, now: Optional[float] = None) -> None:
        if now is None:
            now = time.time()
        if self.buffer and (now - self.last_input_time > self.decay_timeout):
            self.buffer.clear()
        self.buffer.append(key_token.upper())
        self.last_input_time = now
        if len(self.buffer) > 30:
            self.buffer = self.buffer[-30:]

    def clear(self) -> None:
        self.buffer.clear()
        self.last_input_time = 0.0

    def check_decay(self, now: Optional[float] = None) -> bool:
        if now is None:
            now = time.time()
        if self.buffer and (now - self.last_input_time > self.decay_timeout):
            self.buffer.clear()
            return True
        return False

    def matches(self, sequence: List[str]) -> bool:
        if len(self.buffer) < len(sequence):
            return False
        return self.buffer[-len(sequence):] == [s.upper() for s in sequence]

    def ends_with(self, sequence: List[str]) -> bool:
        """Alias for matches to inspect trailing key sequence."""
        return self.matches(sequence)


KONAMI_SEQUENCE = ["UP", "UP", "DOWN", "DOWN", "LEFT", "RIGHT", "LEFT", "RIGHT", "B", "A"]
QUICK_SWITCH_SEQUENCE = ["UP", "UP", "DOWN", "DOWN"]
NAVIGATOR_SEQUENCE = ["UP", "UP"]


def ensure_kwin_shortcut_inhibition() -> bool:
    """
    Ensure KWin disables global shortcuts (Alt+Tab, Alt+F4, Meta) for JimHa window.

    Checks if running under KDE Plasma by verifying the presence of kreadconfig6 and
    kwriteconfig6. If jimha_lockdown is not registered in kwinrulesrc, adds the rule
    with disableglobalshortcuts=true (forced) and reconfigures KWin via DBus.

    Returns True if successfully verified or configured, False otherwise.
    All subprocess and OS errors are caught and logged transparently to ensure JimHa
    gracefully runs on non-KDE environments or headless test setups.
    """
    try:
        kread_bin = shutil.which("kreadconfig6")
        kwrite_bin = shutil.which("kwriteconfig6")
        if not kread_bin or not kwrite_bin:
            return False

        # Read existing rules list from General group in kwinrulesrc
        res = subprocess.run(
            [kread_bin, "--file", "kwinrulesrc", "--group", "General", "--key", "rules"],
            capture_output=True,
            text=True,
            check=False,
        )
        current_rules = res.stdout.strip() if res.returncode == 0 else ""
        rules_list = [r.strip() for r in current_rules.split(",") if r.strip()]

        if "jimha_lockdown" not in rules_list:
            rules_list.append("jimha_lockdown")
            new_rules = ",".join(rules_list)
            new_count = str(len(rules_list))

            subprocess.run(
                [kwrite_bin, "--file", "kwinrulesrc", "--group", "General", "--key", "rules", new_rules],
                check=True,
            )
            subprocess.run(
                [kwrite_bin, "--file", "kwinrulesrc", "--group", "General", "--key", "count", new_count],
                check=True,
            )

            # Rule properties for jimha_lockdown
            rule_props = [
                ("description", "JimHa Toddler Game Lockdown"),
                ("wmclass", "jimha"),
                ("wmclassmatch", "1"),
                ("types", "1"),
                ("disableglobalshortcuts", "true"),
                ("disableglobalshortcutsrule", "2"),
            ]
            for key, val in rule_props:
                subprocess.run(
                    [kwrite_bin, "--file", "kwinrulesrc", "--group", "jimha_lockdown", "--key", key, val],
                    check=True,
                )

            # Notify KWin to reload rules via DBus
            qdbus_bin = shutil.which("qdbus") or shutil.which("qdbus6")
            if qdbus_bin:
                subprocess.run([qdbus_bin, "org.kde.KWin", "/KWin", "reconfigure"], check=True)

        return True
    except (subprocess.SubprocessError, FileNotFoundError, Exception) as err:
        logger.warning("KWin shortcut inhibition configuration failed: %s", err)
        return False


def query_open_windows() -> List[Dict[str, str]]:
    """
    Query live client windows currently managed by KWin via D-Bus WindowsRunner.

    Extracts window match ID, window caption, and icon name. Automatically filters out
    JimHa window instances and empty window titles. Deduplicates by match_id.
    Returns a fallback desktop entry if no client windows are found or on D-Bus errors.
    """
    qdbus_bin = shutil.which("qdbus") or shutil.which("qdbus6") or "qdbus"
    windows: List[Dict[str, str]] = []
    seen = set()

    try:
        res = subprocess.run(
            [qdbus_bin, "--literal", "org.kde.KWin", "/WindowsRunner", "org.kde.krunner1.Match", ""],
            capture_output=True,
            text=True,
            timeout=2.0,
            check=False,
        )
        if res.returncode != 0:
            logger.warning(
                "query_open_windows D-Bus command failed (exit %d): %s",
                res.returncode,
                res.stderr.strip() if res.stderr else "",
            )
        elif res.stdout:
            pattern = re.compile(r'\[Argument: \(sss[a-z0-9{}()]+\) "([^"]+)", "([^"]*)", "([^"]*)"')
            for match in pattern.finditer(res.stdout):
                match_id = match.group(1).strip()
                title = match.group(2).strip()
                icon = match.group(3).strip()

                if not match_id or match_id in seen:
                    continue
                if not title or title.startswith("JimHa's Magical Key Smash Game"):
                    continue

                seen.add(match_id)
                windows.append({"id": match_id, "title": title, "icon": icon})
    except Exception as err:
        logger.warning("query_open_windows failed: %s", err)

    if not windows:
        windows = [{"id": "desktop", "title": "Desktop / Workspace", "icon": "user-desktop"}]

    logger.debug("query_open_windows discovered %d windows: %s", len(windows), [w["title"] for w in windows])
    return windows


def activate_window_by_id(match_id: str) -> bool:
    """
    Activate a specific window or toggle desktop view via KWin D-Bus.

    If match_id is 'desktop', requests KWin to show the desktop.
    Otherwise invokes WindowsRunner Run with the given match_id.
    Returns True if the invocation completed successfully.
    """
    qdbus_bin = shutil.which("qdbus") or shutil.which("qdbus6") or "qdbus"
    try:
        if match_id == "desktop":
            res = subprocess.run(
                [qdbus_bin, "org.kde.KWin", "/KWin", "showDesktop", "true"],
                capture_output=True,
                text=True,
                timeout=2.0,
                check=False,
            )
        else:
            res = subprocess.run(
                [qdbus_bin, "org.kde.KWin", "/WindowsRunner", "org.kde.krunner1.Run", match_id, ""],
                capture_output=True,
                text=True,
                timeout=2.0,
                check=False,
            )
        if res.returncode != 0:
            logger.warning(
                "activate_window_by_id failed (exit %d): %s",
                res.returncode,
                res.stderr.strip() if res.stderr else "",
            )
            return False
        logger.debug("activate_window_by_id(%s) succeeded", match_id)
        return True
    except Exception as err:
        logger.warning("activate_window_by_id exception: %s", err)
        return False


def synthesize_kwin_handover_script(target_match_id: Optional[str] = None) -> Tuple[str, str]:
    """
    Synthesize transient KWin script for authoritative window handover.

    Returns tuple of (clean_target, js_script_content).
    """
    if target_match_id == "desktop":
        clean_target = "desktop"
    elif target_match_id:
        uuid_match = re.search(
            r"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}",
            target_match_id,
        )
        if uuid_match:
            clean_target = uuid_match.group(0).lower()
        else:
            clean_target = target_match_id.strip()
    else:
        clean_target = ""

    script = (
        "var wins = workspace.windowList();\n"
        "for (var i = 0; i < wins.length; i++) {\n"
        "    var w = wins[i];\n"
        '    if (w.resourceClass === "jimha" || (w.caption && w.caption.indexOf("JimHa\'s Magical Key Smash") !== -1)) {\n'
        "        w.minimized = true;\n"
        "    }\n"
        "}\n"
        f"var target = {json.dumps(clean_target)};\n"
        'if (target === "desktop") {\n'
        "    workspace.slotToggleShowDesktop();\n"
        "} else if (target) {\n"
        "    for (var i = 0; i < wins.length; i++) {\n"
        "        var w = wins[i];\n"
        '        var wid = (w.internalId || w.uuid || "").toString().toLowerCase();\n'
        "        if (wid && wid.indexOf(target) !== -1) {\n"
        "            w.minimized = false;\n"
        "            workspace.activeWindow = w;\n"
        "            workspace.raiseWindow(w);\n"
        "            break;\n"
        "        }\n"
        "    }\n"
        "} else {\n"
        "    var stack = workspace.stackingOrder;\n"
        "    for (var i = stack.length - 1; i >= 0; i--) {\n"
        "        var sw = stack[i];\n"
        '        if (sw.resourceClass !== "jimha" && !sw.minimized && sw.normalWindow) {\n'
        "            workspace.activeWindow = sw;\n"
        "            workspace.raiseWindow(sw);\n"
        "            break;\n"
        "        }\n"
        "    }\n"
        "}\n"
    )
    return clean_target, script


def execute_kwin_handover(target_match_id: Optional[str] = None) -> bool:
    """
    Execute authoritative KWin window handover via transient KWin D-Bus script.

    Minimizes JimHa and activates target window (or desktop, or top window in stacking order).
    Returns True on success, False on failure.
    """
    qdbus_bin = shutil.which("qdbus") or shutil.which("qdbus6")
    if not qdbus_bin:
        logger.debug("execute_kwin_handover: qdbus or qdbus6 binary not found")
        return False

    clean_target, script_content = synthesize_kwin_handover_script(target_match_id)
    plugin_name = "jimha_handover"
    temp_path = None
    script_loaded = False

    try:
        with tempfile.NamedTemporaryFile(mode="w", suffix=".js", delete=False) as tf:
            tf.write(script_content)
            temp_path = tf.name

        # Best effort unload prior instance
        subprocess.run(
            [qdbus_bin, "org.kde.KWin", "/Scripting", "org.kde.kwin.Scripting.unloadScript", plugin_name],
            capture_output=True,
            text=True,
            timeout=2.0,
            check=False,
        )

        # Load script
        res_load = subprocess.run(
            [qdbus_bin, "org.kde.KWin", "/Scripting", "org.kde.kwin.Scripting.loadScript", temp_path, plugin_name],
            capture_output=True,
            text=True,
            timeout=2.0,
            check=False,
        )
        if res_load.returncode != 0:
            logger.warning(
                "Failed to load KWin handover script (exit %d): %s",
                res_load.returncode,
                res_load.stderr.strip() if res_load.stderr else "",
            )
            return False

        script_loaded = True

        # Extract script id number from stdout
        stdout_str = res_load.stdout.strip() if res_load.stdout else ""
        id_match = re.search(r"-?\d+", stdout_str)
        if not id_match or int(id_match.group(0)) < 0:
            logger.warning("Invalid script id returned from loadScript: %s", stdout_str)
            return False
        script_id = id_match.group(0)

        # Run script
        res_run = subprocess.run(
            [qdbus_bin, "org.kde.KWin", f"/Scripting/Script{script_id}", "org.kde.kwin.Script.run"],
            capture_output=True,
            text=True,
            timeout=2.0,
            check=False,
        )

        if res_run.returncode != 0:
            logger.warning(
                "Failed to run KWin handover script (exit %d): %s",
                res_run.returncode,
                res_run.stderr.strip() if res_run.stderr else "",
            )
            return False

        logger.debug("execute_kwin_handover(%s) succeeded with script id %s", clean_target, script_id)
        return True

    except Exception as err:
        logger.warning("execute_kwin_handover exception: %s", err)
        return False
    finally:
        if script_loaded:
            try:
                subprocess.run(
                    [qdbus_bin, "org.kde.KWin", "/Scripting", "org.kde.kwin.Scripting.unloadScript", plugin_name],
                    capture_output=True,
                    text=True,
                    timeout=2.0,
                    check=False,
                )
            except Exception as unload_err:
                logger.warning("Failed to unload KWin handover script: %s", unload_err)
        if temp_path:
            try:
                Path(temp_path).unlink(missing_ok=True)
            except OSError as unlink_err:
                logger.warning("Failed to unlink temporary KWin script %s: %s", temp_path, unlink_err)


class JimHaGame(QWidget):
    """Fullscreen interactive visual playground with long-hold ESC exit protection."""

    def __init__(self, parent=None, enable_audio=True, is_windowed=False):
        super().__init__(parent)
        self.setWindowTitle("JimHa's Magical Key Smash Game")
        self.is_windowed = is_windowed
        self._exit_authorized = False
        self._handover_active: bool = False

        # Ensure KWin shortcut inhibition rule under KDE Plasma Wayland
        ensure_kwin_shortcut_inhibition()

        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setMouseTracking(True)

        # In default fullscreen mode, enforce stays-on-top frameless kiosk window hints
        if not self.is_windowed:
            self.setWindowFlags(
                Qt.WindowType.Window
                | Qt.WindowType.FramelessWindowHint
                | Qt.WindowType.WindowStaysOnTopHint
            )

        # Audio synthesizer bank
        self.enable_audio = enable_audio
        if self.enable_audio:
            self.sound_bank = SoundBank()
            self.sound_bank.init_qt_effects()
        else:
            self.sound_bank = None

        # Display State
        self.current_key_title = "JIMHA"
        self.current_subtitle = "💖 Smash any button to play! 💖"
        self.current_emoji = "✨"
        self.current_color = QColor("#FF4081")

        # Animation state for the main card
        self.card_age = 0.0  # seconds since key press
        self.card_scale = 1.0
        self.card_alpha = 1.0
        self.background_hue = 260.0  # subtle shifting background

        # Particles & Bubbles
        self.particles: List[Particle] = []
        self.bubbles: List[FloatingBubble] = []

        # Background stars
        self.bg_stars: List[Tuple[float, float, float, float]] = []  # (rel_x, rel_y, size, phase)
        for _ in range(70):
            self.bg_stars.append((random.random(), random.random(), random.uniform(2.0, 5.0), random.uniform(0, math.pi * 2)))

        # Escape Hold Exit Protection
        self.esc_hold_required_sec = 3.0
        self.esc_is_pressed = False
        self.esc_press_start_time = 0.0
        self.esc_hold_progress = 0.0  # 0.0 to 1.0

        # Option A: Alt+Tab Continuous Hold Adult Gate
        self.alt_tab_hold_required_sec = 2.0
        self.alt_tab_is_pressed = False
        self.alt_tab_start_time = 0.0
        self.alt_tab_hold_progress = 0.0  # 0.0 to 1.0
        self.alt_pressed = False
        self.tab_pressed = False

        # Option C: Rekka Arcade Combo Engine & Navigator Mode
        self.rekka_buffer = RekkaBuffer(decay_timeout=0.8)
        self.rekka_nav_active = False
        self.rekka_nav_last_action_time = 0.0
        self.rekka_nav_idle_timeout = 5.0
        self.rekka_nav_index = 0

        # Option C Phase 3: In-Game Virtual Rekka Switcher Carousel
        self.virtual_switcher_active: bool = False
        self.virtual_switcher_windows: List[Dict[str, str]] = []
        self.virtual_switcher_index: int = 0
        self.virtual_switcher_last_action_time: float = 0.0
        self.virtual_switcher_pixmaps: Dict[str, QPixmap] = {}

        # Quick-Switch deferred handover timer
        self._quick_switch_timer = QTimer(self)
        self._quick_switch_timer.setSingleShot(True)
        self._quick_switch_timer.timeout.connect(self._on_quick_switch_timeout)
        self._pending_handover_target_id: Optional[str] = None

        # Frame timer (adaptive 60/30 FPS)
        self.last_frame_time = time.time()
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._on_tick)
        self.timer.start(16)

    def trigger_key(self, title: str, subtitle: str = "", emoji: str = "✨", color: Optional[QColor] = None) -> None:
        """Activate a new key event with spring animations and particle fireworks."""
        self.current_key_title = title
        self.current_subtitle = subtitle
        self.current_emoji = emoji
        self.current_color = color if color is not None else random.choice(PALETTE)
        self.card_age = 0.0
        self.card_scale = 0.2
        self.card_alpha = 1.0

        # Play harmonic pentatonic chime
        if self.sound_bank:
            self.sound_bank.play_key(title)

        # Spawn particle fireworks
        center_x = self.width() / 2.0
        center_y = self.height() / 2.0
        self._spawn_particle_burst(center_x, center_y, count=45)

    def _spawn_particle_burst(self, x: float, y: float, count: int = 35, colors: Optional[List[QColor]] = None) -> None:
        """Create a vibrant shower of multi-shaped confetti, stars, and hearts."""
        shapes = ["star", "circle", "heart", "confetti"]
        palette = colors if colors is not None else PALETTE
        for _ in range(count):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(150.0, 750.0)
            vx = math.cos(angle) * speed
            vy = math.sin(angle) * speed - random.uniform(50.0, 200.0)
            size = random.uniform(8.0, 24.0)
            color = random.choice(palette)
            shape = random.choice(shapes)
            decay_rate = random.uniform(0.4, 0.9)  # life drops by this per sec
            rot_speed = random.uniform(-360.0, 360.0)

            self.particles.append(
                Particle(
                    x=x,
                    y=y,
                    vx=vx,
                    vy=vy,
                    size=size,
                    color=color,
                    shape=shape,
                    life=1.0,
                    decay_rate=decay_rate,
                    rotation=random.uniform(0, 360),
                    rot_speed=rot_speed,
                )
            )

    def _spawn_bubble(self, x: float, y: float) -> None:
        """Spawn a floating bubble from mouse/touch interaction."""
        radius = random.uniform(16.0, 48.0)
        color = random.choice(PALETTE)
        vx = random.uniform(-40.0, 40.0)
        vy = random.uniform(-120.0, -40.0)
        self.bubbles.append(
            FloatingBubble(
                x=x,
                y=y,
                vx=vx,
                vy=vy,
                radius=radius,
                color=color,
                life=1.0,
            )
        )

    def _on_tick(self) -> None:
        """60 FPS physics, animation update, and ESC hold evaluation."""
        now = time.time()
        dt = max(0.001, min(0.1, now - self.last_frame_time))
        self.last_frame_time = now

        # Update card age and elastic bounce scale
        self.card_age += dt
        if self.card_age < 0.35:
            # Elastic spring: 0.2 -> 1.25 -> 1.0
            progress = self.card_age / 0.35
            self.card_scale = 0.2 + 0.8 * (1.0 + math.sin(progress * math.pi) * 0.35)
        else:
            self.card_scale = 1.0

        # Dynamic framerate scaling: 60 FPS active, 30 FPS idle
        has_active_fx = bool(
            self.particles
            or self.bubbles
            or self.card_age < 1.2
            or self.esc_is_pressed
            or self.alt_tab_is_pressed
            or self.rekka_nav_active
            or self.virtual_switcher_active
        )
        target_interval = 16 if has_active_fx else 33
        if self.timer.interval() != target_interval:
            self.timer.setInterval(target_interval)

        # Slow background hue drift
        self.background_hue = (self.background_hue + dt * 3.0) % 360.0

        # ESC hold progress update
        if self.esc_is_pressed:
            elapsed = now - self.esc_press_start_time
            self.esc_hold_progress = min(1.0, elapsed / self.esc_hold_required_sec)
            if self.esc_hold_progress >= 1.0:
                self._exit_authorized = True
                if not self.is_windowed:
                    self._safe_release_keyboard()
                self.timer.stop()
                if self.sound_bank:
                    self.sound_bank.close()
                QApplication.quit()
                return
        else:
            self.esc_hold_progress = 0.0

        # Option A: Alt+Tab hold progress update
        if self.alt_tab_is_pressed:
            elapsed = now - self.alt_tab_start_time
            self.alt_tab_hold_progress = min(1.0, elapsed / self.alt_tab_hold_required_sec)
            if self.alt_tab_hold_progress >= 1.0:
                self._handover_to_desktop()
                return
        else:
            self.alt_tab_hold_progress = 0.0

        # Option C: Rekka timeout decay and Navigator idle auto-commit
        self.rekka_buffer.check_decay(now)
        if self.rekka_nav_active:
            if now - self.rekka_nav_last_action_time >= self.rekka_nav_idle_timeout:
                self._handover_to_desktop()
                return

        # Option C Phase 3: Virtual Switcher idle timeout (15.0s gently returns to canvas without minimizing)
        if self.virtual_switcher_active:
            if now - self.virtual_switcher_last_action_time >= 15.0:
                self.virtual_switcher_active = False
                self.update()

        # Update Particles
        alive_particles: List[Particle] = []
        gravity = 400.0  # px/s^2
        for p in self.particles:
            p.x += p.vx * dt
            p.y += p.vy * dt
            p.vy += gravity * dt
            p.rotation += p.rot_speed * dt
            p.life -= p.decay_rate * dt
            if p.life > 0 and p.y < self.height() + 100:
                alive_particles.append(p)
        self.particles = alive_particles

        # Update Bubbles
        alive_bubbles: List[FloatingBubble] = []
        for b in self.bubbles:
            b.x += b.vx * dt
            b.y += b.vy * dt
            b.life -= 0.15 * dt
            if b.life > 0 and b.y > -100:
                alive_bubbles.append(b)
        self.bubbles = alive_bubbles

        self.update()

    def event(self, event: QEvent) -> bool:
        """
        Intercept ShortcutOverride events to swallow all application/desktop shortcut accelerators
        (e.g., Ctrl+Q, Ctrl+W, Alt+F4), ensuring they are forwarded as regular keypresses instead
        of escaping or closing the application.
        """
        if event.type() == QEvent.Type.ShortcutOverride:
            event.accept()
            return True
        return super().event(event)

    def _safe_grab_keyboard(self) -> None:
        """Safely grab exclusive keyboard input with diagnostic debug logging."""
        try:
            self.grabKeyboard()
        except Exception as err:
            logger.debug("Keyboard grab/release unhandled: %s", err)

    def _safe_release_keyboard(self) -> None:
        """Safely release keyboard grab with diagnostic debug logging."""
        try:
            self.releaseKeyboard()
        except Exception as err:
            logger.debug("Keyboard grab/release unhandled: %s", err)

    def showEvent(self, event: QShowEvent) -> None:
        """Grab exclusive keyboard focus upon display in default fullscreen mode."""
        super().showEvent(event)
        if not self.is_windowed and not self._exit_authorized:
            self._safe_grab_keyboard()

    def _handover_to_desktop(self, target_match_id: Optional[str] = None) -> None:
        """Release exclusive keyboard grab, minimize JimHa, and hand over control authoritatively."""
        if hasattr(self, "_quick_switch_timer"):
            self._quick_switch_timer.stop()
        if self._exit_authorized:
            return
        self._handover_active = True
        self.alt_tab_is_pressed = False
        self.alt_tab_hold_progress = 0.0
        self.esc_is_pressed = False
        self.esc_hold_progress = 0.0
        self.rekka_nav_active = False
        self.virtual_switcher_active = False
        self._safe_release_keyboard()
        self.showMinimized()
        if not execute_kwin_handover(target_match_id):
            if not activate_window_by_id(target_match_id or "desktop"):
                logger.warning("Handover window activation failed for id: %s", target_match_id)

    def _trigger_quick_switch_handover(self, target_id: Optional[str]) -> None:
        """Trigger visual banner and schedule deferred handover via managed timer."""
        self.virtual_switcher_active = False
        self.rekka_nav_active = False
        self.trigger_key("⚡ QUICK SWITCH ⚡", "Desktop Handover Activated", "⚡", QColor("#FFD600"))
        self._spawn_particle_burst(self.width() / 2.0, self.height() / 2.0, count=30)
        self._pending_handover_target_id = target_id
        if hasattr(self, "_quick_switch_timer"):
            self._quick_switch_timer.stop()
            self._quick_switch_timer.start(150)

    def _on_quick_switch_timeout(self) -> None:
        """Execute deferred handover to target window if window is not destroyed/closed."""
        if not self._exit_authorized:
            self._handover_to_desktop(target_match_id=self._pending_handover_target_id)

    def _trigger_kwin_switch(self, reverse: bool = False) -> bool:
        """Advance forward or backward in window stack via native DBus or local state."""
        action = "Walk Through Windows (Reverse)" if reverse else "Walk Through Windows"
        try:
            from PyQt6.QtDBus import QDBusConnection, QDBusMessage
            bus = QDBusConnection.sessionBus()
            if bus.isConnected():
                msg = QDBusMessage.createMethodCall(
                    "org.kde.kglobalaccel",
                    "/component/kwin",
                    "org.kde.kglobalaccel.Component",
                    "invokeShortcut",
                )
                msg.setArguments([action])
                return bus.send(msg)
        except (ImportError, RuntimeError, Exception) as err:
            logger.debug("KWin shortcut switch failed: %s", err)
            return False
        return False

    def changeEvent(self, event: QEvent) -> None:
        """Aggressively reclaim focus in kiosk mode; yield cleanly during handover; relock upon reactivation."""
        if event.type() == QEvent.Type.ActivationChange:
            if self.isActiveWindow():
                if self._handover_active:
                    logger.debug("JimHa reactivated by user after handover - restoring kiosk mode")
                    self._handover_active = False
                    self.virtual_switcher_active = False
                    if not self.is_windowed and not self._exit_authorized:
                        self.showFullScreen()
                        self._safe_grab_keyboard()
            else:
                # Lost active focus
                if not self._handover_active and not self.is_windowed and not self._exit_authorized:
                    self.activateWindow()
                    self.raise_()
                    self.setFocus()
        super().changeEvent(event)

    def focusOutEvent(self, event: QFocusEvent) -> None:
        """Prevent losing keyboard focus to background tasks in fullscreen mode."""
        if not self._handover_active and not self._exit_authorized and not self.is_windowed:
            self.setFocus()
        super().focusOutEvent(event)

    def closeEvent(self, event: QCloseEvent) -> None:
        """
        Toddler-safe exit invariant:
        Disallow closing from ANY keyboard shortcut (Alt+F4), window manager, or OS signal
        unless the continuous 3.0s ESC hold has been fully satisfied.
        """
        if not self._exit_authorized and not self.is_windowed:
            event.ignore()
            return

        if hasattr(self, "_quick_switch_timer"):
            self._quick_switch_timer.stop()
        if hasattr(self, "timer"):
            self.timer.stop()
        if hasattr(self, "sound_bank") and self.sound_bank:
            self.sound_bank.close()
        super().closeEvent(event)

    def force_close(self) -> None:
        """Programmatic teardown for automated test suites and headless rendering."""
        self._exit_authorized = True
        if hasattr(self, "_quick_switch_timer"):
            self._quick_switch_timer.stop()
        if hasattr(self, "timer"):
            self.timer.stop()
        self._safe_release_keyboard()
        self.close()

    def keyPressEvent(self, event: QKeyEvent) -> None:
        """Handle key presses with toddler-safe ESC hold, Alt+Tab hold gate, and Rekka arcade combos."""
        key_code = event.key()
        is_alt = key_code in (Qt.Key.Key_Alt, Qt.Key.Key_AltGr)
        is_tab = key_code == Qt.Key.Key_Tab
        has_alt_mod = bool(event.modifiers() & Qt.KeyboardModifier.AltModifier)

        if is_alt:
            self.alt_pressed = True
        if is_tab:
            self.tab_pressed = True

        is_alt_tab = (is_tab and (has_alt_mod or self.alt_pressed)) or (is_alt and self.tab_pressed)

        # 1. Option A: Alt+Tab continuous 2.0s hold gate
        if is_alt_tab:
            self.esc_is_pressed = False
            self.esc_hold_progress = 0.0
            self.rekka_nav_active = False
            self.virtual_switcher_active = False
            self.rekka_buffer.clear()
            if not event.isAutoRepeat():
                if not self.alt_tab_is_pressed:
                    self.alt_tab_is_pressed = True
                    self.alt_tab_start_time = time.time()
                    self.alt_tab_hold_progress = 0.0
                # Tapping or mashing Alt+Tab is swallowed and rendered as playful visual sparks
                self._spawn_particle_burst(self.width() / 2.0, self.height() / 2.0, count=15)
                if self.sound_bank:
                    self.sound_bank.play_key("ALT_TAB")
            return

        # Any non-Alt/Tab key press immediately cancels Alt+Tab hold progress
        if not (is_alt or is_tab):
            self.alt_tab_is_pressed = False
            self.alt_tab_hold_progress = 0.0
            self.alt_pressed = False
            self.tab_pressed = False

        # 2. Virtual Switcher active key routing
        if self.virtual_switcher_active:
            if key_code == Qt.Key.Key_Escape:
                self.virtual_switcher_active = False
                self.rekka_buffer.clear()
                self.update()
                return
            elif key_code in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
                if self.virtual_switcher_windows:
                    idx = self.virtual_switcher_index % len(self.virtual_switcher_windows)
                    target = self.virtual_switcher_windows[idx]["id"]
                else:
                    target = None
                self._handover_to_desktop(target_match_id=target)
                self.virtual_switcher_active = False
                return
            elif key_code in (Qt.Key.Key_Right, Qt.Key.Key_Down):
                token = "RIGHT" if key_code == Qt.Key.Key_Right else "DOWN"
                self.rekka_buffer.add(token)

                if self.rekka_buffer.matches(QUICK_SWITCH_SEQUENCE):
                    wins = query_open_windows()
                    target_id = wins[0]["id"] if wins else None
                    self._trigger_quick_switch_handover(target_id)
                    return

                if self.virtual_switcher_windows:
                    self.virtual_switcher_index = (self.virtual_switcher_index + 1) % len(self.virtual_switcher_windows)
                self.virtual_switcher_last_action_time = time.time()
                if self.sound_bank:
                    self.sound_bank.play_key("ALT_TAB")
                self.update()
                return
            elif key_code in (Qt.Key.Key_Left, Qt.Key.Key_Up):
                token = "LEFT" if key_code == Qt.Key.Key_Left else "UP"
                self.rekka_buffer.add(token)
                if self.virtual_switcher_windows:
                    self.virtual_switcher_index = (self.virtual_switcher_index - 1) % len(self.virtual_switcher_windows)
                self.virtual_switcher_last_action_time = time.time()
                if self.sound_bank:
                    self.sound_bank.play_key("ALT_TAB")
                self.update()
                return
            elif key_code in (Qt.Key.Key_B, Qt.Key.Key_A) or event.text().upper() in ("B", "A"):
                token = "B" if (key_code == Qt.Key.Key_B or event.text().upper() == "B") else "A"
                self.rekka_buffer.add(token)
                if self.rekka_buffer.matches(KONAMI_SEQUENCE):
                    if hasattr(self, "_quick_switch_timer"):
                        self._quick_switch_timer.stop()
                    self.virtual_switcher_active = False
                    self.trigger_key("👑 30 LIVES GRANTED! 🚀💖✨", "30 Lives Granted! Konami Handover", "👑", QColor("#FF4081"))
                    self._spawn_particle_burst(self.width() / 2.0, self.height() / 2.0, count=60)
                    self._handover_to_desktop()
                    return
                self.virtual_switcher_last_action_time = time.time()
                self.update()
                return
            else:
                self.virtual_switcher_active = False
                self.rekka_buffer.clear()

        # 3. ESC Hold exit protection (3.0s continuous hold)
        if key_code == Qt.Key.Key_Escape:
            if not event.isAutoRepeat() and not self.esc_is_pressed:
                self.esc_is_pressed = True
                self.esc_press_start_time = time.time()
                self.esc_hold_progress = 0.0
            return

        # Any regular key press interrupts ESC hold
        self.esc_is_pressed = False
        self.esc_hold_progress = 0.0

        # 4. Rekka Arcade Combo Buffer Processing (when not in switcher)
        if key_code == Qt.Key.Key_Up:
            token = "UP"
        elif key_code == Qt.Key.Key_Down:
            token = "DOWN"
        elif key_code == Qt.Key.Key_Left:
            token = "LEFT"
        elif key_code == Qt.Key.Key_Right:
            token = "RIGHT"
        elif key_code == Qt.Key.Key_B or event.text().upper() == "B":
            token = "B"
        elif key_code == Qt.Key.Key_A or event.text().upper() == "A":
            token = "A"
        elif key_code in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            token = "ENTER"
        else:
            token = event.text().strip().upper() if event.text().strip() else f"KEY_{key_code}"

        self.rekka_buffer.add(token)

        if self.rekka_buffer.matches(KONAMI_SEQUENCE):
            if hasattr(self, "_quick_switch_timer"):
                self._quick_switch_timer.stop()
            self.trigger_key("👑 30 LIVES GRANTED! 🚀💖✨", "30 Lives Granted! Konami Handover", "👑", QColor("#FF4081"))
            self._spawn_particle_burst(self.width() / 2.0, self.height() / 2.0, count=60)
            self._handover_to_desktop()
            return
        elif self.rekka_buffer.matches(QUICK_SWITCH_SEQUENCE):
            wins = query_open_windows()
            target_id = wins[0]["id"] if wins else None
            self._trigger_quick_switch_handover(target_id)
            return
        elif self.rekka_buffer.matches(NAVIGATOR_SEQUENCE):
            self.virtual_switcher_active = True
            self.virtual_switcher_windows = query_open_windows()
            self.virtual_switcher_index = 0
            self.virtual_switcher_last_action_time = time.time()
            self.rekka_nav_active = False
            if self.sound_bank:
                self.sound_bank.play_key("ALT_TAB")
            self._spawn_particle_burst(
                self.width() / 2.0,
                self.height() / 2.0,
                count=20,
                colors=[QColor("#00E5FF"), QColor("#FFD600")],
            )
            self.update()
            return

        # 5. Standard Interactive Canvas Display
        text = event.text().strip().upper()

        if text and text in ALPHABET_COMPANIONS:
            emoji, word = ALPHABET_COMPANIONS[text]
            subtitle = f"{text} is for {word} {emoji}"
            self.trigger_key(text, subtitle, emoji)
        elif text and text.isdigit():
            val = int(text)
            stars = "⭐" * max(1, min(val, 10))
            subtitle = f"Number {val}! {stars}"
            self.trigger_key(text, subtitle, "🔢")
        elif key_code == Qt.Key.Key_Space:
            self.trigger_key("SPACE", "🌟 COSMIC SUPERNOVA! 🌟", "✨")
        elif key_code in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            self.trigger_key("ENTER", "🎉 PARTY TIME CELEBRATION! 🎉", "🎈")
        elif key_code == Qt.Key.Key_Backspace:
            self.trigger_key("POP!", "🫧 BUBBLE POP! 🫧", "🫧")
        elif key_code == Qt.Key.Key_Up:
            self.trigger_key("UP ⬆️", "🚀 ROCKETING TO THE STARS!", "🌌")
        elif key_code == Qt.Key.Key_Down:
            self.trigger_key("DOWN ⬇️", "🌊 DIVING DEEP INTO THE OCEAN!", "🐬")
        elif key_code == Qt.Key.Key_Left:
            self.trigger_key("LEFT ⬅️", "🌪️ SWISHING TO THE LEFT!", "💫")
        elif key_code == Qt.Key.Key_Right:
            self.trigger_key("RIGHT ➡️", "⚡ DASHING TO THE RIGHT!", "⚡")
        else:
            key_name = event.text() if event.text() else f"KEY"
            self.trigger_key(key_name.upper(), "💖 YOU ARE AWESOME JIMHA! 💖", "🌟")

    def keyReleaseEvent(self, event: QKeyEvent) -> None:
        """Cancel ESC hold and Alt+Tab hold timers immediately when physical key is released."""
        key_code = event.key()
        if key_code == Qt.Key.Key_Escape:
            if not event.isAutoRepeat():
                self.esc_is_pressed = False
                self.esc_hold_progress = 0.0

        if key_code in (Qt.Key.Key_Alt, Qt.Key.Key_AltGr):
            if not event.isAutoRepeat():
                self.alt_pressed = False
                self.alt_tab_is_pressed = False
                self.alt_tab_hold_progress = 0.0

        if key_code == Qt.Key.Key_Tab:
            if not event.isAutoRepeat():
                self.tab_pressed = False
                self.alt_tab_is_pressed = False
                self.alt_tab_hold_progress = 0.0

    def mousePressEvent(self, event: QMouseEvent) -> None:
        """Spawn sparkling bubbles on mouse clicks or touch taps."""
        pos = event.position()
        self._spawn_bubble(pos.x(), pos.y())
        self._spawn_particle_burst(pos.x(), pos.y(), count=15)
        if self.sound_bank:
            self.sound_bank.play_key("MOUSE")

    def paintEvent(self, event: QPaintEvent) -> None:
        """Render high-contrast visual feast with anti-aliasing."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.TextAntialiasing)

        width = self.width()
        height = self.height()
        center_x = width / 2.0
        center_y = height / 2.0

        # 1. Dynamic Twilight Gradient Background
        bg_col1 = QColor.fromHsv(int(self.background_hue) % 360, 180, 45)
        bg_col2 = QColor.fromHsv(int(self.background_hue + 50) % 360, 220, 20)
        grad = QLinearGradient(0, 0, width, height)
        grad.setColorAt(0.0, bg_col1)
        grad.setColorAt(1.0, bg_col2)
        painter.fillRect(self.rect(), grad)

        # 2. Twinkling Background Stars
        t_sec = time.time()
        painter.setPen(Qt.PenStyle.NoPen)
        for rel_x, rel_y, size, phase in self.bg_stars:
            twinkle = 0.5 + 0.5 * math.sin(t_sec * 2.5 + phase)
            alpha = int(120 * twinkle)
            painter.setBrush(QColor(255, 255, 255, alpha))
            painter.drawEllipse(QPointF(rel_x * width, rel_y * height), size, size)

        # 3. Floating Bubbles
        for b in self.bubbles:
            alpha = int(220 * b.life)
            c = QColor(b.color)
            c.setAlpha(alpha)
            painter.setBrush(c)
            painter.setPen(QPen(QColor(255, 255, 255, alpha), 2))
            painter.drawEllipse(QPointF(b.x, b.y), b.radius, b.radius)
            painter.setBrush(QColor(255, 255, 255, int(180 * b.life)))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(
                QPointF(b.x - b.radius * 0.35, b.y - b.radius * 0.35),
                b.radius * 0.25,
                b.radius * 0.25,
            )

        # 4. Animated Particles (Stars, Hearts, Confetti)
        for p in self.particles:
            painter.save()
            painter.translate(p.x, p.y)
            painter.rotate(p.rotation)
            alpha = max(0, min(255, int(255 * p.life)))
            c = QColor(p.color)
            c.setAlpha(alpha)
            painter.setBrush(c)
            painter.setPen(Qt.PenStyle.NoPen)

            if p.shape == "circle":
                painter.drawEllipse(QPointF(0, 0), p.size / 2, p.size / 2)
            elif p.shape == "confetti":
                painter.drawRect(QRectF(-p.size / 2, -p.size / 4, p.size, p.size / 2))
            elif p.shape == "star":
                self._draw_star(painter, 0, 0, p.size / 2, 5)
            elif p.shape == "heart":
                self._draw_heart(painter, 0, 0, p.size)
            painter.restore()

        # 5. Massive Animated Key Display (Center Stage)
        painter.save()
        painter.translate(center_x, center_y)
        painter.scale(self.card_scale, self.card_scale)

        halo_rad = min(width, height) * 0.45
        radial = QRadialGradient(0, 0, halo_rad)
        glow_color = QColor(self.current_color)
        glow_color.setAlpha(120)
        radial.setColorAt(0.0, glow_color)
        radial.setColorAt(0.7, QColor(glow_color.red(), glow_color.green(), glow_color.blue(), 30))
        radial.setColorAt(1.0, QColor(0, 0, 0, 0))
        painter.setBrush(radial)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(QPointF(0, 0), halo_rad, halo_rad)

        font_size = int(min(width, height) * 0.28)
        font = QFont("Cantarell", font_size, QFont.Weight.Black)
        font.setStyleHint(QFont.StyleHint.SansSerif)
        painter.setFont(font)

        title_text = self.current_key_title
        metrics = QFontMetrics(font)
        text_rect = metrics.boundingRect(title_text)

        painter.setPen(QColor(0, 0, 0, 180))
        painter.drawText(int(-text_rect.width() / 2 + 8), int(text_rect.height() / 4 + 8), title_text)

        painter.setPen(self.current_color)
        painter.drawText(int(-text_rect.width() / 2), int(text_rect.height() / 4), title_text)

        if self.current_subtitle:
            sub_font_size = int(min(width, height) * 0.055)
            sub_font = QFont("Cantarell", max(18, sub_font_size), QFont.Weight.Bold)
            painter.setFont(sub_font)
            sub_metrics = QFontMetrics(sub_font)
            sub_rect = sub_metrics.boundingRect(self.current_subtitle)

            badge_y = text_rect.height() / 4 + 70
            badge_rect = QRectF(
                -sub_rect.width() / 2 - 25,
                badge_y - sub_rect.height() / 2 - 12,
                sub_rect.width() + 50,
                sub_rect.height() + 24,
            )

            painter.setBrush(QColor(0, 0, 0, 140))
            painter.setPen(QPen(QColor(255, 255, 255, 180), 2))
            painter.drawRoundedRect(badge_rect, 20, 20)

            painter.setPen(QColor("#FFFFFF"))
            painter.drawText(
                int(-sub_rect.width() / 2),
                int(badge_y + sub_rect.height() / 3),
                self.current_subtitle,
            )

        painter.restore()

        # 6. Exit Protection HUD (Escape Hold Overlay)
        if self.esc_is_pressed or self.esc_hold_progress > 0:
            self._draw_esc_hold_hud(painter, width, height)

        # 7. Option A Parent Gate HUD (Alt+Tab Hold Overlay)
        if self.alt_tab_is_pressed or self.alt_tab_hold_progress > 0:
            self._draw_gate_hud(painter, width, height)

        # 8. Option C Rekka Navigator HUD (Arcade Status Pill)
        if self.rekka_nav_active:
            self._draw_rekka_hud(painter, width, height)

        # 9. Option C Phase 3: In-Game Virtual Rekka Switcher Carousel
        if self.virtual_switcher_active:
            self._draw_virtual_switcher(painter, width, height)

    def _draw_gate_hud(self, painter: QPainter, width: int, height: int) -> None:
        """Render Option A Parent Gate: Emerald/Gold radial countdown for Alt+Tab hold."""
        hud_center_x = width / 2.0
        hud_center_y = height * 0.22
        radius = 55.0

        painter.save()

        # Dark glassmorphic container with emerald border
        painter.setBrush(QColor(10, 30, 20, 225))
        painter.setPen(QPen(QColor("#00E676"), 2))
        painter.drawRoundedRect(
            QRectF(hud_center_x - 240, hud_center_y - 85, 480, 170),
            24,
            24,
        )

        # Background track circle
        painter.setPen(QPen(QColor(30, 70, 50), 8))
        painter.drawEllipse(QPointF(hud_center_x, hud_center_y), radius, radius)

        # Radial progress arc in gold (#FFD700)
        span_angle = int(-360 * self.alt_tab_hold_progress * 16)
        painter.setPen(QPen(QColor("#FFD700"), 8, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        painter.drawArc(
            QRectF(hud_center_x - radius, hud_center_y - radius, radius * 2, radius * 2),
            90 * 16,
            span_angle,
        )

        remaining = max(0.0, self.alt_tab_hold_required_sec * (1.0 - self.alt_tab_hold_progress))
        time_text = f"{remaining:.1f}s"
        font = QFont("Cantarell", 16, QFont.Weight.Bold)
        painter.setFont(font)
        painter.setPen(QColor("#FFFFFF"))
        metrics = QFontMetrics(font)
        tw = metrics.boundingRect(time_text).width()
        painter.drawText(int(hud_center_x - tw / 2), int(hud_center_y + 6), time_text)

        label_font = QFont("Cantarell", 12, QFont.Weight.Bold)
        painter.setFont(label_font)
        painter.setPen(QColor("#00E676"))
        top_label = f"🎓 PARENT GATE: Unlocking Desktop Switch... ({remaining:.1f}s)"
        tl_w = QFontMetrics(label_font).boundingRect(top_label).width()
        painter.drawText(int(hud_center_x - tl_w / 2), int(hud_center_y - 60), top_label)

        hint_font = QFont("Cantarell", 11, QFont.Weight.Medium)
        painter.setFont(hint_font)
        painter.setPen(QColor("#A7FFEB"))
        bot_label = "Hold Alt+Tab 2.0s to switch • Release to cancel"
        bl_w = QFontMetrics(hint_font).boundingRect(bot_label).width()
        painter.drawText(int(hud_center_x - bl_w / 2), int(hud_center_y + 72), bot_label)

        painter.restore()

    def _draw_rekka_hud(self, painter: QPainter, width: int, height: int) -> None:
        """Render Option C Arcade Rekka Navigator status pill."""
        hud_center_x = width / 2.0
        hud_center_y = height * 0.86
        pill_w = 760.0
        pill_h = 56.0

        painter.save()

        # Dark arcade pill with neon cyan glow & border
        painter.setBrush(QColor(15, 15, 30, 235))
        painter.setPen(QPen(QColor("#00E5FF"), 3))
        pill_rect = QRectF(hud_center_x - pill_w / 2, hud_center_y - pill_h / 2, pill_w, pill_h)
        painter.drawRoundedRect(pill_rect, 28, 28)

        # Arcade status pill text
        idle_rem = max(0.0, self.rekka_nav_idle_timeout - (time.time() - self.rekka_nav_last_action_time))
        pill_text = (
            f"🕹️ REKKA NAVIGATOR: [→ Next App] [← Prev App] [Enter Commit] [Esc Cancel] ({idle_rem:.1f}s)"
        )
        font = QFont("Cantarell", 12, QFont.Weight.Bold)
        painter.setFont(font)
        painter.setPen(QColor("#FFFFFF"))
        tw = QFontMetrics(font).boundingRect(pill_text).width()
        painter.drawText(int(hud_center_x - tw / 2), int(hud_center_y + 5), pill_text)

        painter.restore()

    def _get_app_icon_pixmap(self, icon_name: Optional[str], size: int = 96) -> Optional[QPixmap]:
        """Fetch and cache system application icon pixmap from theme with fallbacks."""
        icon_name = (icon_name or "").strip()
        cache_key = f"{icon_name}_{size}"
        if cache_key in self.virtual_switcher_pixmaps:
            pix = self.virtual_switcher_pixmaps[cache_key]
            return pix if not pix.isNull() else None

        candidates = [icon_name]
        if "." in icon_name:
            candidates.append(icon_name.split(".")[-1])
        candidates.extend(["preferences-system-windows", "window-new", "application-x-executable"])

        for name in candidates:
            if not name:
                continue
            icon = QIcon.fromTheme(name)
            if not icon.isNull():
                pix = icon.pixmap(size, size)
                if not pix.isNull():
                    self.virtual_switcher_pixmaps[cache_key] = pix
                    return pix

        # Store empty sentinel pixmap to avoid thrashing filesystem on repeated misses
        self.virtual_switcher_pixmaps[cache_key] = QPixmap()
        return None

    def _draw_virtual_switcher(self, painter: QPainter, width: int, height: int) -> None:
        """Render arcade glassmorphic in-game virtual window switcher carousel."""
        painter.save()

        # 1. Dimmed backdrop overlay
        painter.fillRect(0, 0, width, height, QColor(0, 0, 0, 185))

        center_x = width / 2.0
        center_y = height / 2.0

        # 2. Top Title
        title_font = QFont("Cantarell", 18, QFont.Weight.Bold)
        painter.setFont(title_font)
        painter.setPen(QColor("#00E5FF"))
        top_title = "🕹️ REKKA VIRTUAL WINDOW SWITCHER 🕹️"
        metrics = QFontMetrics(title_font)
        tw = metrics.boundingRect(top_title).width()
        painter.drawText(int(center_x - tw / 2.0), int(height * 0.14), top_title)

        wins = self.virtual_switcher_windows
        total = len(wins)
        idx = self.virtual_switcher_index % total if total > 0 else 0
        cur_win = wins[idx] if wins else {"id": "desktop", "title": "Desktop / Workspace", "icon": "user-desktop"}

        # 3. Flanking cards for previous and next windows
        active_w = 540.0
        active_h = 320.0
        flank_w = 240.0
        flank_h = 180.0
        flank_gap = 30.0
        flank_y = center_y - flank_h / 2.0
        prev_x = (center_x - active_w / 2.0) - flank_gap - flank_w
        next_x = (center_x + active_w / 2.0) + flank_gap

        if total > 1:
            flank_font = QFont("Cantarell", 11, QFont.Weight.Medium)
            # Previous window card (left)
            prev_win = wins[(idx - 1) % total]
            painter.setBrush(QColor(15, 25, 45, int(240 * 0.45)))
            painter.setPen(QPen(QColor(0, 229, 255, int(255 * 0.45)), 2))
            painter.drawRoundedRect(QRectF(prev_x, flank_y, flank_w, flank_h), 18, 18)

            prev_pix = self._get_app_icon_pixmap(prev_win.get("icon", ""), size=48)
            if prev_pix and not prev_pix.isNull():
                painter.drawPixmap(int(prev_x + flank_w / 2.0 - 24), int(flank_y + 35), prev_pix)
            else:
                painter.setFont(QFont("Cantarell", 28))
                painter.setPen(QColor(255, 255, 255, int(255 * 0.6)))
                painter.drawText(int(prev_x + flank_w / 2.0 - 18), int(flank_y + 65), "🖥️")

            painter.setFont(flank_font)
            painter.setPen(QColor(255, 255, 255, int(255 * 0.65)))
            prev_elided = QFontMetrics(flank_font).elidedText(prev_win.get("title", ""), Qt.TextElideMode.ElideMiddle, int(flank_w - 24))
            ptw = QFontMetrics(flank_font).boundingRect(prev_elided).width()
            painter.drawText(int(prev_x + flank_w / 2.0 - ptw / 2.0), int(flank_y + flank_h - 30), prev_elided)

            # Next window card (right)
            next_win = wins[(idx + 1) % total]
            painter.setBrush(QColor(15, 25, 45, int(240 * 0.45)))
            painter.setPen(QPen(QColor(0, 229, 255, int(255 * 0.45)), 2))
            painter.drawRoundedRect(QRectF(next_x, flank_y, flank_w, flank_h), 18, 18)

            next_pix = self._get_app_icon_pixmap(next_win.get("icon", ""), size=48)
            if next_pix and not next_pix.isNull():
                painter.drawPixmap(int(next_x + flank_w / 2.0 - 24), int(flank_y + 35), next_pix)
            else:
                painter.setFont(QFont("Cantarell", 28))
                painter.setPen(QColor(255, 255, 255, int(255 * 0.6)))
                painter.drawText(int(next_x + flank_w / 2.0 - 18), int(flank_y + 65), "🖥️")

            painter.setFont(flank_font)
            painter.setPen(QColor(255, 255, 255, int(255 * 0.65)))
            next_elided = QFontMetrics(flank_font).elidedText(next_win.get("title", ""), Qt.TextElideMode.ElideMiddle, int(flank_w - 24))
            ntw = QFontMetrics(flank_font).boundingRect(next_elided).width()
            painter.drawText(int(next_x + flank_w / 2.0 - ntw / 2.0), int(flank_y + flank_h - 30), next_elided)

        # 4. Centered Active Window Card
        active_rect = QRectF(center_x - active_w / 2.0, center_y - active_h / 2.0, active_w, active_h)
        painter.setBrush(QColor(15, 25, 45, 240))
        painter.setPen(QPen(QColor("#FFD600"), 3))
        painter.drawRoundedRect(active_rect, 24, 24)

        # Draw Native Application Icon (centered at hud_center_y - 45)
        icon_pix = self._get_app_icon_pixmap(cur_win.get("icon", ""), size=96)
        if icon_pix and not icon_pix.isNull():
            painter.drawPixmap(int(center_x - 48), int(center_y - 45 - 48), icon_pix)
        else:
            badge_font = QFont("Cantarell", 48)
            painter.setFont(badge_font)
            painter.setPen(QColor("#FFFFFF"))
            painter.drawText(int(center_x - 30), int(center_y - 45 + 18), "🖥️")

        # Window Title / Caption (font 15 bold, white, elided)
        cap_font = QFont("Cantarell", 15, QFont.Weight.Bold)
        painter.setFont(cap_font)
        painter.setPen(QColor("#FFFFFF"))
        cap_metrics = QFontMetrics(cap_font)
        caption_elided = cap_metrics.elidedText(cur_win.get("title", "Unknown"), Qt.TextElideMode.ElideMiddle, int(active_w - 60))
        cw = cap_metrics.boundingRect(caption_elided).width()
        painter.drawText(int(center_x - cw / 2.0), int(center_y + 40), caption_elided)

        # Position Pill: Window [ X of Y ] in font 11 bold cyan
        pos_font = QFont("Cantarell", 11, QFont.Weight.Bold)
        painter.setFont(pos_font)
        painter.setPen(QColor("#00E5FF"))
        pos_str = f"Window [ {idx + 1} of {max(1, total)} ]"
        pos_w = QFontMetrics(pos_font).boundingRect(pos_str).width()
        painter.drawText(int(center_x - pos_w / 2.0), int(center_y + 80), pos_str)

        # 5. Instruction Footer at bottom
        footer_str = "[← / ↑ Prev]  •  [→ / ↓ Next]  •  [ENTER: Switch to App]  •  [ESC: Stay in JimHa]"
        footer_font = QFont("Cantarell", 12, QFont.Weight.Bold)
        painter.setFont(footer_font)
        foot_metrics = QFontMetrics(footer_font)
        fw = foot_metrics.boundingRect(footer_str).width()
        footer_y = height * 0.88

        pill_rect = QRectF(center_x - fw / 2.0 - 20, footer_y - 20, fw + 40, 40)
        painter.setBrush(QColor(15, 15, 30, 220))
        painter.setPen(QPen(QColor("#00E5FF"), 1.5))
        painter.drawRoundedRect(pill_rect, 20, 20)

        painter.setPen(QColor("#FFFFFF"))
        painter.drawText(int(center_x - fw / 2.0), int(footer_y + 5), footer_str)

        painter.restore()

    def _draw_star(self, painter: QPainter, cx: float, cy: float, r: float, points: int = 5) -> None:
        path = QPainterPath()
        inner_r = r * 0.45
        for i in range(points * 2):
            rad = r if i % 2 == 0 else inner_r
            angle = i * math.pi / points - math.pi / 2
            x = cx + rad * math.cos(angle)
            y = cy + rad * math.sin(angle)
            if i == 0:
                path.moveTo(x, y)
            else:
                path.lineTo(x, y)
        path.closeSubpath()
        painter.drawPath(path)

    def _draw_heart(self, painter: QPainter, cx: float, cy: float, size: float) -> None:
        path = QPainterPath()
        w = size * 0.8
        h = size * 0.8
        path.moveTo(cx, cy + h * 0.4)
        path.cubicTo(cx - w * 0.6, cy - h * 0.4, cx - w * 0.6, cy - h * 0.8, cx, cy - h * 0.3)
        path.cubicTo(cx + w * 0.6, cy - h * 0.8, cx + w * 0.6, cy - h * 0.4, cx, cy + h * 0.4)
        painter.drawPath(path)

    def _draw_esc_hold_hud(self, painter: QPainter, width: int, height: int) -> None:
        hud_center_x = width / 2.0
        hud_center_y = height * 0.22
        radius = 55.0

        painter.setBrush(QColor(10, 10, 20, 210))
        painter.setPen(QPen(QColor(255, 255, 255, 80), 2))
        painter.drawRoundedRect(
            QRectF(hud_center_x - 220, hud_center_y - 85, 440, 170),
            24,
            24,
        )

        painter.setPen(QPen(QColor(80, 80, 100), 8))
        painter.drawEllipse(QPointF(hud_center_x, hud_center_y), radius, radius)

        span_angle = int(-360 * self.esc_hold_progress * 16)
        painter.setPen(QPen(QColor("#FF1744"), 8, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        painter.drawArc(
            QRectF(hud_center_x - radius, hud_center_y - radius, radius * 2, radius * 2),
            90 * 16,
            span_angle,
        )

        remaining = max(0.0, self.esc_hold_required_sec * (1.0 - self.esc_hold_progress))
        time_text = f"{remaining:.1f}s"
        font = QFont("Cantarell", 16, QFont.Weight.Bold)
        painter.setFont(font)
        painter.setPen(QColor("#FFFFFF"))
        metrics = QFontMetrics(font)
        tw = metrics.boundingRect(time_text).width()
        painter.drawText(int(hud_center_x - tw / 2), int(hud_center_y + 6), time_text)

        label_font = QFont("Cantarell", 12, QFont.Weight.Bold)
        painter.setFont(label_font)
        painter.setPen(QColor("#FF8A80"))
        top_label = "HOLDING ESC TO EXIT..."
        tl_w = QFontMetrics(label_font).boundingRect(top_label).width()
        painter.drawText(int(hud_center_x - tl_w / 2), int(hud_center_y - 60), top_label)

        hint_font = QFont("Cantarell", 11, QFont.Weight.Medium)
        painter.setFont(hint_font)
        painter.setPen(QColor("#B0BEC5"))
        bot_label = "Release ESC to keep playing"
        bl_w = QFontMetrics(hint_font).boundingRect(bot_label).width()
        painter.drawText(int(hud_center_x - bl_w / 2), int(hud_center_y + 72), bot_label)


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("jimha")
    app.setDesktopFileName("jimha")
    game = JimHaGame()
    game.showFullScreen()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
