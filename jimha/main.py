#!/usr/bin/env python3
"""
JimHa's Magical Key Smash Game
A fullscreen, kid-friendly interactive wonderland for JimHa.
Keys pop up in giant, vibrant animations with companion words, emojis, particle bursts, and soothing chimes.
Exit protection: Press and hold ESC continuously for 3.0 seconds to quit.
"""

import math
import random
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Tuple

from PyQt6.QtCore import QEvent, QPointF, QRectF, Qt, QTimer
from PyQt6.QtGui import (
    QCloseEvent,
    QColor,
    QFocusEvent,
    QFont,
    QFontMetrics,
    QKeyEvent,
    QLinearGradient,
    QMouseEvent,
    QPainter,
    QPainterPath,
    QPaintEvent,
    QPen,
    QRadialGradient,
    QShowEvent,
)
from PyQt6.QtWidgets import QApplication, QWidget

# Import sound bank
try:
    from jimha.sound_synth import SoundBank
except ImportError:
    from sound_synth import SoundBank

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


class JimHaGame(QWidget):
    """Fullscreen interactive visual playground with long-hold ESC exit protection."""

    def __init__(self, parent=None, enable_audio=True, is_windowed=False):
        super().__init__(parent)
        self.setWindowTitle("JimHa's Magical Key Smash Game")
        self.is_windowed = is_windowed
        self._exit_authorized = False

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
        self.rekka_nav_idle_timeout = 1.5
        self.rekka_nav_index = 0

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

    def _spawn_particle_burst(self, x: float, y: float, count: int = 35) -> None:
        """Create a vibrant shower of multi-shaped confetti, stars, and hearts."""
        shapes = ["star", "circle", "heart", "confetti"]
        for _ in range(count):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(150.0, 750.0)
            vx = math.cos(angle) * speed
            vy = math.sin(angle) * speed - random.uniform(50.0, 200.0)
            size = random.uniform(8.0, 24.0)
            color = random.choice(PALETTE)
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
                    try:
                        self.releaseKeyboard()
                    except Exception as err:
                        # Safe fallback: Wayland compositors or headless QPA plugins (e.g. offscreen)
                        # may restrict or not support explicit keyboard releasing.
                        pass
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

    def showEvent(self, event: QShowEvent) -> None:
        """Grab exclusive keyboard focus upon display in default fullscreen mode."""
        super().showEvent(event)
        if not self.is_windowed and not self._exit_authorized:
            try:
                self.grabKeyboard()
            except Exception as err:
                # Safe fallback: Wayland compositors or headless QPA plugins (e.g. offscreen)
                # may restrict or not support explicit keyboard grabbing.
                pass

    def _handover_to_desktop(self) -> None:
        """Release exclusive keyboard grab and minimize JimHa to hand over control to desktop."""
        self.alt_tab_is_pressed = False
        self.alt_tab_hold_progress = 0.0
        self.esc_is_pressed = False
        self.esc_hold_progress = 0.0
        self.rekka_nav_active = False
        if not self.is_windowed:
            try:
                self.releaseKeyboard()
            except Exception as err:
                # Safe fallback: Wayland compositors or headless QPA plugins (e.g. offscreen)
                # may restrict or not support explicit keyboard releasing.
                pass
        self.showMinimized()

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
            # DBus KWin shortcut invocation is a best-effort desktop enhancement.
            # Non-KDE Plasma desktop environments, headless tests (offscreen), or systems
            # without a running session bus gracefully fallback to local state handling.
            return False
        return False

    def changeEvent(self, event: QEvent) -> None:
        """Aggressively reclaim focus and auto-relock fullscreen on window restore."""
        if event.type() == QEvent.Type.WindowStateChange:
            if not self.isMinimized() and not self._exit_authorized and not self.is_windowed:
                if not self.isFullScreen():
                    self.showFullScreen()
                try:
                    self.grabKeyboard()
                except Exception as err:
                    # Safe fallback: Wayland compositors or headless QPA plugins (e.g. offscreen)
                    # may restrict or not support explicit keyboard grabbing.
                    pass
        elif event.type() == QEvent.Type.ActivationChange:
            if not self.isMinimized() and not self.isActiveWindow() and not self._exit_authorized and not self.is_windowed:
                self.activateWindow()
                self.raise_()
                self.setFocus()
        super().changeEvent(event)

    def focusOutEvent(self, event: QFocusEvent) -> None:
        """Prevent losing keyboard focus to background tasks in fullscreen mode."""
        if not self._exit_authorized and not self.is_windowed and not self.isMinimized():
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

        if hasattr(self, "sound_bank") and self.sound_bank:
            self.sound_bank.close()
        super().closeEvent(event)

    def force_close(self) -> None:
        """Programmatic teardown for automated test suites and headless rendering."""
        self._exit_authorized = True
        if hasattr(self, "releaseKeyboard"):
            try:
                self.releaseKeyboard()
            except Exception as err:
                # Safe fallback: Wayland compositors or headless QPA plugins (e.g. offscreen)
                # may restrict or not support explicit keyboard releasing.
                pass
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

        # 2. Rekka Navigator mode active key routing
        if self.rekka_nav_active:
            if key_code == Qt.Key.Key_Escape:
                # Escape: aborts Rekka mode and returns immediately to JimHa canvas
                self.rekka_nav_active = False
                self.rekka_buffer.clear()
                self.update()
                return
            elif key_code in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
                # Enter: commits handover, releases grab, and minimizes
                self._handover_to_desktop()
                return
            elif key_code in (Qt.Key.Key_Right, Qt.Key.Key_Down):
                # Add token to RekkaBuffer first to evaluate combo formation
                token = "RIGHT" if key_code == Qt.Key.Key_Right else "DOWN"
                self.rekka_buffer.add(token)

                # 1. Complete combos trigger instant handover without firing Navigator switch
                if self.rekka_buffer.matches(KONAMI_SEQUENCE):
                    self.rekka_nav_active = False
                    self.trigger_key("👑 30 LIVES GRANTED! 🚀💖✨", "30 Lives Granted! Konami Handover", "👑", QColor("#FF4081"))
                    self._spawn_particle_burst(self.width() / 2.0, self.height() / 2.0, count=60)
                    self._handover_to_desktop()
                    return
                elif self.rekka_buffer.matches(QUICK_SWITCH_SEQUENCE):
                    self.rekka_nav_active = False
                    self.trigger_key("⚡ QUICK SWITCH (REKKA) ⚡", "Quick Switch Handover", "⚡", QColor("#FFD600"))
                    self._handover_to_desktop()
                    return

                # 2. Check if the buffer is forming the Quick Switch sequence [UP, UP, DOWN].
                # If so, do not fire a stray KWin window switch while the combo is being executed.
                if self.rekka_buffer.ends_with(["UP", "UP", "DOWN"]):
                    self.rekka_nav_last_action_time = time.time()
                    self.update()
                    return

                # 3. Legitimate stack navigation forward
                self.rekka_nav_index += 1
                self.rekka_nav_last_action_time = time.time()
                self._trigger_kwin_switch(reverse=False)
                self.update()
                return
            elif key_code in (Qt.Key.Key_Left, Qt.Key.Key_Up):
                # ← / ↑: advances backward in window stack
                self.rekka_nav_index -= 1
                self.rekka_nav_last_action_time = time.time()
                self._trigger_kwin_switch(reverse=True)
                token = "LEFT" if key_code == Qt.Key.Key_Left else "UP"
                self.rekka_buffer.add(token)
                self.update()
                return
            elif key_code in (Qt.Key.Key_B, Qt.Key.Key_A) or event.text().upper() in ("B", "A"):
                token = "B" if (key_code == Qt.Key.Key_B or event.text().upper() == "B") else "A"
                self.rekka_nav_last_action_time = time.time()
                self.rekka_buffer.add(token)
                if self.rekka_buffer.matches(KONAMI_SEQUENCE):
                    self.trigger_key("👑 30 LIVES GRANTED! 🚀💖✨", "30 Lives Granted! Konami Handover", "👑", QColor("#FF4081"))
                    self._spawn_particle_burst(self.width() / 2.0, self.height() / 2.0, count=60)
                    self._handover_to_desktop()
                    return
                self.update()
                return
            else:
                self.rekka_nav_active = False
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

        # 4. Rekka Arcade Combo Buffer Processing (when not in navigator)
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
            self.trigger_key("👑 30 LIVES GRANTED! 🚀💖✨", "30 Lives Granted! Konami Handover", "👑", QColor("#FF4081"))
            self._spawn_particle_burst(self.width() / 2.0, self.height() / 2.0, count=60)
            self._handover_to_desktop()
            return
        elif self.rekka_buffer.matches(QUICK_SWITCH_SEQUENCE):
            self.trigger_key("⚡ QUICK SWITCH (REKKA) ⚡", "Quick Switch Handover", "⚡", QColor("#FFD600"))
            self._handover_to_desktop()
            return
        elif self.rekka_buffer.matches(NAVIGATOR_SEQUENCE):
            self.rekka_nav_active = True
            self.rekka_nav_last_action_time = time.time()
            self.rekka_nav_index = 0

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
    game = JimHaGame()
    game.showFullScreen()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
