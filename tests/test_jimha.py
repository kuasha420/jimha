#!/usr/bin/env python3
"""
Automated unit tests for JimHa standalone game.
"""

import os
import sys
import time
import unittest
from pathlib import Path

# Enforce offscreen Qt platform
os.environ["QT_QPA_PLATFORM"] = "offscreen"

# Ensure repo root is on sys.path
THIS_DIR = Path(__file__).resolve().parent
REPO_ROOT = THIS_DIR.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from PyQt6.QtCore import QEvent, Qt
from PyQt6.QtGui import QCloseEvent, QKeyEvent
from PyQt6.QtWidgets import QApplication

from jimha.sound_synth import SoundBank, generate_chime_wav
from jimha.main import JimHaGame, ALPHABET_COMPANIONS, RekkaBuffer


class TestRekkaBuffer(unittest.TestCase):
    """Isolated unit tests for RekkaBuffer combo tracking and decay logic."""

    def test_add(self):
        buf = RekkaBuffer(decay_timeout=0.8)
        buf.add("UP")
        buf.add("DOWN")
        self.assertEqual(buf.buffer, ["UP", "DOWN"])

    def test_check_decay(self):
        buf = RekkaBuffer(decay_timeout=0.05)
        buf.add("UP")
        time.sleep(0.08)
        self.assertTrue(buf.check_decay())
        self.assertEqual(buf.buffer, [])

    def test_buffer_max_cap(self):
        buf = RekkaBuffer(decay_timeout=10.0)
        for i in range(40):
            buf.add(f"K{i}")
        self.assertEqual(len(buf.buffer), 30)
        self.assertEqual(buf.buffer[-1], "K39")

    def test_matches_and_ends_with(self):
        buf = RekkaBuffer(decay_timeout=10.0)
        for k in ["UP", "UP", "DOWN", "DOWN"]:
            buf.add(k)
        self.assertTrue(buf.matches(["UP", "UP", "DOWN", "DOWN"]))
        self.assertTrue(buf.matches(["DOWN", "DOWN"]))
        self.assertFalse(buf.matches(["UP", "DOWN"]))
        self.assertTrue(buf.ends_with(["DOWN", "DOWN"]))


class TestJimHa(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance()
        if cls.app is None:
            cls.app = QApplication(sys.argv)

    def test_01_sound_synth_wav_generation(self):
        """Verify that chime synthesis produces a valid non-empty WAV file."""
        test_wav = Path("/tmp/test_jimha_chime.wav")
        if test_wav.exists():
            test_wav.unlink()

        generate_chime_wav(test_wav, frequency=523.25, duration=0.1)
        self.assertTrue(test_wav.exists(), "WAV file was not generated")
        self.assertGreater(test_wav.stat().st_size, 100, "WAV file is too small or empty")
        test_wav.unlink()

    def test_02_sound_bank_initialization(self):
        """Verify sound bank creates the pentatonic scale cache."""
        cache_dir = Path("/tmp/test_jimha_sounds")
        bank = SoundBank(cache_dir=cache_dir)
        self.assertGreaterEqual(len(bank.sound_paths), 11, "Pentatonic sound bank incomplete")
        for p in bank.sound_paths:
            self.assertTrue(p.exists(), f"Expected sound file {p} does not exist")

    def test_03_game_initialization_and_paint(self):
        """Verify widget initializes and paints offscreen without crash."""
        game = JimHaGame(enable_audio=False)
        game.resize(1024, 768)
        game.show()

        game.repaint()
        self.assertEqual(game.current_key_title, "JIMHA")

    def test_04_alphabet_key_press_events(self):
        """Verify pressing letters triggers companion words and particle bursts."""
        game = JimHaGame(enable_audio=False)
        game.resize(800, 600)

        # Simulate pressing 'A'
        press_a = QKeyEvent(QEvent.Type.KeyPress, Qt.Key.Key_A, Qt.KeyboardModifier.NoModifier, "a")
        game.keyPressEvent(press_a)

        self.assertEqual(game.current_key_title, "A")
        self.assertIn("Apple", game.current_subtitle)
        self.assertEqual(game.current_emoji, "🍎")
        self.assertGreater(len(game.particles), 0, "Particles should spawn on key press")

        # Simulate pressing 'J' (JimHa star)
        press_j = QKeyEvent(QEvent.Type.KeyPress, Qt.Key.Key_J, Qt.KeyboardModifier.NoModifier, "j")
        game.keyPressEvent(press_j)
        self.assertEqual(game.current_key_title, "J")
        self.assertIn("JimHa", game.current_subtitle)

        # Simulate pressing 'H' (Jim Heart Easter Egg)
        press_h = QKeyEvent(QEvent.Type.KeyPress, Qt.Key.Key_H, Qt.KeyboardModifier.NoModifier, "h")
        game.keyPressEvent(press_h)
        self.assertEqual(game.current_key_title, "H")
        self.assertIn("Jim Heart", game.current_subtitle)

    def test_05_escape_hold_exit_protection(self):
        """Verify quick ESC tap does NOT quit and cancels hold timer."""
        game = JimHaGame(enable_audio=False)
        game.resize(800, 600)

        # Physical ESC press
        esc_down = QKeyEvent(QEvent.Type.KeyPress, Qt.Key.Key_Escape, Qt.KeyboardModifier.NoModifier)
        game.keyPressEvent(esc_down)
        self.assertTrue(game.esc_is_pressed, "ESC press should initiate hold tracking")

        # Quick ESC release
        esc_up = QKeyEvent(QEvent.Type.KeyRelease, Qt.Key.Key_Escape, Qt.KeyboardModifier.NoModifier)
        game.keyReleaseEvent(esc_up)
        self.assertFalse(game.esc_is_pressed, "Quick ESC release must cancel hold state")
        self.assertEqual(game.esc_hold_progress, 0.0, "Progress should reset to zero")

    def test_06_escape_continuous_hold_reaches_full_progress(self):
        """Verify that holding ESC for the required duration reaches 100% progress."""
        game = JimHaGame(enable_audio=False)
        game.esc_hold_required_sec = 0.15  # Fast test duration
        game.resize(800, 600)

        esc_down = QKeyEvent(QEvent.Type.KeyPress, Qt.Key.Key_Escape, Qt.KeyboardModifier.NoModifier)
        game.keyPressEvent(esc_down)

        time.sleep(0.2)
        game._on_tick()

        self.assertGreaterEqual(game.esc_hold_progress, 1.0, "ESC hold progress should reach 1.0")

    def test_07_sound_bank_play_key_cycling(self):
        """Verify SoundBank note index cycling and robust player dispatch."""
        cache_dir = Path("/tmp/test_jimha_sounds_cycle")
        bank = SoundBank(cache_dir=cache_dir)
        init_idx = bank._note_index
        bank.play_key("A")
        self.assertNotEqual(bank._note_index, init_idx, "Note index must advance on play_key")
        bank.play_key("SPACE")
        self.assertTrue(len(bank.sound_paths) > 0)
        bank.close()

    def test_08_close_event_ignored_when_unauthorized(self):
        """Verify that QCloseEvent is rejected (event.ignore()) unless exit is authorized."""
        game = JimHaGame(enable_audio=False, is_windowed=False)
        close_ev = QCloseEvent()
        game.closeEvent(close_ev)
        self.assertFalse(close_ev.isAccepted(), "CloseEvent must be ignored when unauthorized")
        self.assertFalse(game._exit_authorized)

        # Authorize exit and verify closeEvent is accepted
        game.force_close()
        self.assertTrue(game._exit_authorized, "force_close must authorize exit")

    def test_09_shortcut_override_swallowed(self):
        """Verify ShortcutOverride events for Alt+F4, Ctrl+Q, Ctrl+W are swallowed."""
        game = JimHaGame(enable_audio=False, is_windowed=False)

        # Alt + F4
        ev_alt_f4 = QKeyEvent(QEvent.Type.ShortcutOverride, Qt.Key.Key_F4, Qt.KeyboardModifier.AltModifier)
        self.assertTrue(game.event(ev_alt_f4), "Alt+F4 ShortcutOverride must be consumed")
        self.assertTrue(ev_alt_f4.isAccepted())

        # Ctrl + Q
        ev_ctrl_q = QKeyEvent(QEvent.Type.ShortcutOverride, Qt.Key.Key_Q, Qt.KeyboardModifier.ControlModifier)
        self.assertTrue(game.event(ev_ctrl_q), "Ctrl+Q ShortcutOverride must be consumed")
        self.assertTrue(ev_ctrl_q.isAccepted())

        # Ctrl + W
        ev_ctrl_w = QKeyEvent(QEvent.Type.ShortcutOverride, Qt.Key.Key_W, Qt.KeyboardModifier.ControlModifier)
        self.assertTrue(game.event(ev_ctrl_w), "Ctrl+W ShortcutOverride must be consumed")
        self.assertTrue(ev_ctrl_w.isAccepted())

        self.assertFalse(game._exit_authorized)
        game.force_close()

    def test_10_interrupted_esc_never_authorizes_exit(self):
        """Verify that interrupting ESC hold with another key resets progress and never authorizes exit."""
        game = JimHaGame(enable_audio=False, is_windowed=False)
        game.esc_hold_required_sec = 0.5

        # Press ESC
        esc_down = QKeyEvent(QEvent.Type.KeyPress, Qt.Key.Key_Escape, Qt.KeyboardModifier.NoModifier)
        game.keyPressEvent(esc_down)
        time.sleep(0.1)
        game._on_tick()
        self.assertGreater(game.esc_hold_progress, 0.0)
        self.assertFalse(game._exit_authorized)

        # Interrupt by smashing another key
        space_down = QKeyEvent(QEvent.Type.KeyPress, Qt.Key.Key_Space, Qt.KeyboardModifier.NoModifier, " ")
        game.keyPressEvent(space_down)
        self.assertFalse(game.esc_is_pressed)
        self.assertEqual(game.esc_hold_progress, 0.0)
        self.assertFalse(game._exit_authorized)

        game.force_close()

    def test_11_alt_tab_hold_triggers_minimize(self):
        """Verify Option A: continuous Alt+Tab hold triggers minimize, while tap/mash or interrupt cancels."""
        game = JimHaGame(enable_audio=False, is_windowed=False)
        game.alt_tab_hold_required_sec = 0.15  # Fast test duration
        game.resize(800, 600)
        game.show()

        # 1. Tap Alt+Tab (quick press & release)
        ev_tab_press = QKeyEvent(QEvent.Type.KeyPress, Qt.Key.Key_Tab, Qt.KeyboardModifier.AltModifier)
        game.keyPressEvent(ev_tab_press)
        self.assertTrue(game.alt_tab_is_pressed, "Alt+Tab press should initiate hold tracking")
        self.assertGreater(len(game.particles), 0, "Sparks should spawn on Alt+Tab press")

        # Early release must cancel progress
        ev_tab_release = QKeyEvent(QEvent.Type.KeyRelease, Qt.Key.Key_Tab, Qt.KeyboardModifier.AltModifier)
        game.keyReleaseEvent(ev_tab_release)
        self.assertFalse(game.alt_tab_is_pressed, "Releasing Tab must cancel hold state")
        self.assertEqual(game.alt_tab_hold_progress, 0.0, "Progress should reset to zero")
        self.assertFalse(game.isMinimized(), "Early release must not trigger minimize")

        # 2. Interruption by third key press
        game.keyPressEvent(ev_tab_press)
        self.assertTrue(game.alt_tab_is_pressed)
        ev_third_key = QKeyEvent(QEvent.Type.KeyPress, Qt.Key.Key_Space, Qt.KeyboardModifier.NoModifier, " ")
        game.keyPressEvent(ev_third_key)
        self.assertFalse(game.alt_tab_is_pressed, "Third key press must instantly cancel Alt+Tab hold")
        self.assertEqual(game.alt_tab_hold_progress, 0.0)
        self.assertFalse(game.isMinimized())

        # 3. Organic HUD repaint check during active hold
        game.keyPressEvent(ev_tab_press)
        time.sleep(0.06)
        game._on_tick()
        self.assertTrue(game.alt_tab_is_pressed)
        self.assertGreater(game.alt_tab_hold_progress, 0.0)
        game.repaint()  # Paints _draw_gate_hud under genuine organic state
        game.keyReleaseEvent(ev_tab_release)
        self.assertFalse(game.alt_tab_is_pressed)

        # 4. Continuous hold reaches 100% -> minimizes window and resets progress
        game.keyPressEvent(ev_tab_press)
        time.sleep(0.2)
        game._on_tick()
        self.assertTrue(game.isMinimized(), "Continuous 100% hold must minimize window")
        self.assertFalse(game.alt_tab_is_pressed)
        self.assertEqual(game.alt_tab_hold_progress, 0.0)

        game.force_close()

    def test_12_rekka_quick_switch(self):
        """Verify Option C: [↑, ↑, ↓, ↓] triggers instant Quick-Switch banner and showMinimized."""
        game = JimHaGame(enable_audio=False, is_windowed=False)
        game.resize(800, 600)
        game.show()

        # Send [UP, UP, DOWN, DOWN]
        for key in [Qt.Key.Key_Up, Qt.Key.Key_Up, Qt.Key.Key_Down, Qt.Key.Key_Down]:
            ev = QKeyEvent(QEvent.Type.KeyPress, key, Qt.KeyboardModifier.NoModifier)
            game.keyPressEvent(ev)

        self.assertEqual(game.current_key_title, "⚡ QUICK SWITCH (REKKA) ⚡")
        self.assertTrue(game.isMinimized(), "Quick-Switch must minimize the window")
        game.force_close()

    def test_13_rekka_timeout_decay(self):
        """Verify Option C: RekkaBuffer decays after timeout so delayed inputs do not trigger combos."""
        game = JimHaGame(enable_audio=False, is_windowed=False)
        game.rekka_buffer.decay_timeout = 0.1  # Fast test duration
        game.resize(800, 600)
        game.show()

        # Press [UP, UP] -> enters Rekka Navigator mode
        for _ in range(2):
            ev = QKeyEvent(QEvent.Type.KeyPress, Qt.Key.Key_Up, Qt.KeyboardModifier.NoModifier)
            game.keyPressEvent(ev)
        self.assertTrue(game.rekka_nav_active, "Double UP must enter Rekka Navigator mode")

        # Test Escape abort in Navigator mode
        ev_esc = QKeyEvent(QEvent.Type.KeyPress, Qt.Key.Key_Escape, Qt.KeyboardModifier.NoModifier)
        game.keyPressEvent(ev_esc)
        self.assertFalse(game.rekka_nav_active, "Escape must abort Rekka Navigator mode")
        self.assertFalse(game.isMinimized(), "Aborting Rekka mode must not minimize")

        # Re-enter Navigator with [UP, UP]
        for _ in range(2):
            ev = QKeyEvent(QEvent.Type.KeyPress, Qt.Key.Key_Up, Qt.KeyboardModifier.NoModifier)
            game.keyPressEvent(ev)
        self.assertTrue(game.rekka_nav_active)

        # Wait past decay timeout (0.15s > 0.1s)
        time.sleep(0.15)
        game._on_tick()

        # Send [DOWN, DOWN]
        for _ in range(2):
            ev = QKeyEvent(QEvent.Type.KeyPress, Qt.Key.Key_Down, Qt.KeyboardModifier.NoModifier)
            game.keyPressEvent(ev)

        # Because timeout decayed the buffer, it must NOT trigger Quick-Switch
        self.assertNotEqual(game.current_key_title, "⚡ QUICK SWITCH (REKKA) ⚡")

        # Re-enter Navigator organically with [UP, UP] and commit via Enter
        for _ in range(2):
            ev = QKeyEvent(QEvent.Type.KeyPress, Qt.Key.Key_Up, Qt.KeyboardModifier.NoModifier)
            game.keyPressEvent(ev)
        self.assertTrue(game.rekka_nav_active)

        ev_enter = QKeyEvent(QEvent.Type.KeyPress, Qt.Key.Key_Return, Qt.KeyboardModifier.NoModifier)
        game.keyPressEvent(ev_enter)
        self.assertFalse(game.rekka_nav_active)
        self.assertTrue(game.isMinimized(), "Enter in Navigator mode must commit handover and minimize")

        game.force_close()

    def test_14_full_konami_code(self):
        """Verify Option C: [↑, ↑, ↓, ↓, ←, →, ←, →, B, A] triggers 60-particle Konami explosion and banner."""
        game = JimHaGame(enable_audio=False, is_windowed=False)
        game.resize(800, 600)
        game.show()

        konami_keys = [
            (Qt.Key.Key_Up, ""),
            (Qt.Key.Key_Up, ""),
            (Qt.Key.Key_Down, ""),
            (Qt.Key.Key_Down, ""),
            (Qt.Key.Key_Left, ""),
            (Qt.Key.Key_Right, ""),
            (Qt.Key.Key_Left, ""),
            (Qt.Key.Key_Right, ""),
            (Qt.Key.Key_B, "b"),
            (Qt.Key.Key_A, "a"),
        ]

        # Feed first 9 keys
        for key, text in konami_keys[:-1]:
            ev = QKeyEvent(QEvent.Type.KeyPress, key, Qt.KeyboardModifier.NoModifier, text)
            game.keyPressEvent(ev)

        # Clear particles right before final 'A' key to strictly measure Konami burst
        game.particles.clear()
        final_key, final_text = konami_keys[-1]
        ev_final = QKeyEvent(QEvent.Type.KeyPress, final_key, Qt.KeyboardModifier.NoModifier, final_text)
        game.keyPressEvent(ev_final)

        self.assertEqual(game.current_key_title, "👑 30 LIVES GRANTED! 🚀💖✨")
        self.assertTrue(game.isMinimized(), "Konami code must handover and minimize")
        self.assertGreaterEqual(len(game.particles), 60, "Konami explosion must spawn at least 60 particles")

        game.force_close()

    def test_15_restore_relocks_fullscreen(self):
        """Verify window restore from minimized state re-enforces fullscreen mode and grabs keyboard."""
        game = JimHaGame(enable_audio=False, is_windowed=False)
        game.resize(800, 600)
        game.showFullScreen()
        self.assertTrue(game.isFullScreen(), "Window should initially be in fullscreen mode")

        # Minimize the window (simulating desktop handover)
        game._handover_to_desktop()
        self.assertTrue(game.isMinimized(), "Window must be minimized after handover")

        # Restore window (simulating user clicking taskbar or OS restore)
        game.showNormal()
        self.assertFalse(game.isMinimized(), "Window should no longer be minimized")
        self.assertTrue(game.isFullScreen(), "Window restore must auto-relock fullscreen kiosk mode")

        game.force_close()

    def test_16_rekka_navigator_idle_timeout(self):
        """Verify Rekka Navigator idle timeout organically commits handover and minimizes."""
        game = JimHaGame(enable_audio=False, is_windowed=False)
        game.rekka_nav_idle_timeout = 0.1  # Fast test duration
        game.resize(800, 600)
        game.show()

        # Organically enter Navigator via [UP, UP]
        for _ in range(2):
            ev = QKeyEvent(QEvent.Type.KeyPress, Qt.Key.Key_Up, Qt.KeyboardModifier.NoModifier)
            game.keyPressEvent(ev)
        self.assertTrue(game.rekka_nav_active, "Double UP must enter Rekka Navigator mode")

        # Wait past idle timeout
        time.sleep(0.15)
        game._on_tick()

        self.assertFalse(game.rekka_nav_active, "Idle timeout must exit Navigator mode")
        self.assertTrue(game.isMinimized(), "Idle timeout must commit handover and minimize")
        game.force_close()

    def test_17_rekka_navigator_stack_walking(self):
        """Verify Rekka Navigator arrow keys walk stack (→, ↓, ←, ↑) and refresh activity time."""
        game = JimHaGame(enable_audio=False, is_windowed=False)
        game.resize(800, 600)
        game.show()

        # Organically enter Navigator via [UP, UP]
        for _ in range(2):
            ev = QKeyEvent(QEvent.Type.KeyPress, Qt.Key.Key_Up, Qt.KeyboardModifier.NoModifier)
            game.keyPressEvent(ev)
        self.assertTrue(game.rekka_nav_active)
        self.assertEqual(game.rekka_nav_index, 0)
        t_init = game.rekka_nav_last_action_time

        # Paint HUD organically in Navigator mode
        game.repaint()

        # Press RIGHT (→): advance forward
        time.sleep(0.01)
        ev_right = QKeyEvent(QEvent.Type.KeyPress, Qt.Key.Key_Right, Qt.KeyboardModifier.NoModifier)
        game.keyPressEvent(ev_right)
        self.assertEqual(game.rekka_nav_index, 1, "Right arrow must advance stack index forward")
        self.assertGreaterEqual(game.rekka_nav_last_action_time, t_init)

        # Press LEFT (←): advance backward
        t_prev = game.rekka_nav_last_action_time
        time.sleep(0.01)
        ev_left = QKeyEvent(QEvent.Type.KeyPress, Qt.Key.Key_Left, Qt.KeyboardModifier.NoModifier)
        game.keyPressEvent(ev_left)
        self.assertEqual(game.rekka_nav_index, 0, "Left arrow must advance stack index backward")
        self.assertGreaterEqual(game.rekka_nav_last_action_time, t_prev)

        # Press UP (↑): advance backward
        ev_up = QKeyEvent(QEvent.Type.KeyPress, Qt.Key.Key_Up, Qt.KeyboardModifier.NoModifier)
        game.keyPressEvent(ev_up)
        self.assertEqual(game.rekka_nav_index, -1, "Up arrow in navigator must advance backward")

        # Press Escape: aborts navigator cleanly
        ev_esc = QKeyEvent(QEvent.Type.KeyPress, Qt.Key.Key_Escape, Qt.KeyboardModifier.NoModifier)
        game.keyPressEvent(ev_esc)
        self.assertFalse(game.rekka_nav_active, "Escape must abort Navigator mode")
        self.assertFalse(game.isMinimized(), "Escape abort must not minimize")

        game.force_close()

    def test_18_kwin_dbus_shortcut_invocation(self):
        """Verify _trigger_kwin_switch creates and sends exact D-Bus method call and arguments."""
        from unittest.mock import MagicMock, patch

        game = JimHaGame(enable_audio=False, is_windowed=False)

        with patch("PyQt6.QtDBus.QDBusConnection.sessionBus") as mock_bus_factory, \
             patch("PyQt6.QtDBus.QDBusMessage.createMethodCall") as mock_create_call:

            mock_bus = MagicMock()
            mock_bus.isConnected.return_value = True
            mock_bus.send.return_value = True
            mock_bus_factory.return_value = mock_bus

            mock_msg_fwd = MagicMock()
            mock_msg_rev = MagicMock()
            mock_create_call.side_effect = [mock_msg_fwd, mock_msg_rev]

            # Forward switch
            res_fwd = game._trigger_kwin_switch(reverse=False)
            self.assertTrue(res_fwd)
            mock_create_call.assert_called_with(
                "org.kde.kglobalaccel",
                "/component/kwin",
                "org.kde.kglobalaccel.Component",
                "invokeShortcut",
            )
            mock_msg_fwd.setArguments.assert_called_once_with(["Walk Through Windows"])
            mock_bus.send.assert_called_with(mock_msg_fwd)

            # Reverse switch
            res_rev = game._trigger_kwin_switch(reverse=True)
            self.assertTrue(res_rev)
            mock_msg_rev.setArguments.assert_called_once_with(["Walk Through Windows (Reverse)"])
            mock_bus.send.assert_called_with(mock_msg_rev)

        # Verify safe transparent fallback when DBus raises RuntimeError
        with patch("PyQt6.QtDBus.QDBusConnection.sessionBus", side_effect=RuntimeError("DBus socket error")):
            res_fallback = game._trigger_kwin_switch(reverse=False)
            self.assertFalse(res_fallback, "DBus errors must be handled gracefully returning False")

        game.force_close()


if __name__ == "__main__":
    unittest.main()

