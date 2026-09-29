#!/usr/bin/env python3
"""
Automated unit tests for JimHa standalone game.
"""

import os
import subprocess
import sys
import time
import unittest
from pathlib import Path
from unittest.mock import MagicMock, call, patch

# Enforce offscreen Qt platform
os.environ["QT_QPA_PLATFORM"] = "offscreen"

# Ensure repo root is on sys.path
THIS_DIR = Path(__file__).resolve().parent
REPO_ROOT = THIS_DIR.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from PyQt6.QtCore import QEvent, Qt
from PyQt6.QtGui import QCloseEvent, QColor, QFocusEvent, QKeyEvent
from PyQt6.QtWidgets import QApplication

from jimha.sound_synth import SoundBank, generate_chime_wav
from jimha.main import (
    JimHaGame,
    ALPHABET_COMPANIONS,
    RekkaBuffer,
    ensure_kwin_shortcut_inhibition,
    query_open_windows,
    activate_window_by_id,
)


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
        """Verify Option C: [↑, ↑, ↓, ↓] triggers instant Quick-Switch banner and showMinimized via singleShot."""
        game = JimHaGame(enable_audio=False, is_windowed=False)
        game.resize(800, 600)
        game.show()

        mock_windows = [{"id": "win_quick_1", "title": "Quick App", "icon": "quick-app"}]
        with patch("jimha.main.query_open_windows", return_value=mock_windows), \
             patch("jimha.main.activate_window_by_id") as mock_act:
            # Send [UP, UP, DOWN, DOWN]
            for key in [Qt.Key.Key_Up, Qt.Key.Key_Up, Qt.Key.Key_Down, Qt.Key.Key_Down]:
                ev = QKeyEvent(QEvent.Type.KeyPress, key, Qt.KeyboardModifier.NoModifier)
                game.keyPressEvent(ev)

            self.assertEqual(game.current_key_title, "⚡ QUICK SWITCH ⚡")
            self.assertEqual(game.current_subtitle, "Desktop Handover Activated")
            self.assertFalse(game.isMinimized(), "Quick-Switch must render visual feedback before minimizing")

            # Allow singleShot 150ms delay to elapse and trigger handover
            time.sleep(0.2)
            QApplication.processEvents()
            self.assertTrue(game.isMinimized(), "Quick-Switch must minimize the window after 150ms delay")
            self.assertTrue(game._handover_active, "Handover flag must be set upon minimization")
            mock_act.assert_called_once_with("win_quick_1")

        game.force_close()

    def test_13_rekka_timeout_decay(self):
        """Verify Option C: RekkaBuffer decays after timeout so delayed inputs do not trigger combos."""
        game = JimHaGame(enable_audio=False, is_windowed=False)
        game.rekka_buffer.decay_timeout = 0.1  # Fast test duration
        game.resize(800, 600)
        game.show()

        mock_windows = [{"id": "win_decay_1", "title": "Decay App", "icon": "decay-app"}]
        with patch("jimha.main.query_open_windows", return_value=mock_windows), \
             patch("jimha.main.activate_window_by_id"):
            # Press [UP, UP] -> enters Virtual Switcher mode
            for _ in range(2):
                ev = QKeyEvent(QEvent.Type.KeyPress, Qt.Key.Key_Up, Qt.KeyboardModifier.NoModifier)
                game.keyPressEvent(ev)
            self.assertTrue(game.virtual_switcher_active, "Double UP must enter Virtual Switcher mode")

            # Test Escape abort in Virtual Switcher mode
            ev_esc = QKeyEvent(QEvent.Type.KeyPress, Qt.Key.Key_Escape, Qt.KeyboardModifier.NoModifier)
            game.keyPressEvent(ev_esc)
            self.assertFalse(game.virtual_switcher_active, "Escape must abort Virtual Switcher mode")
            self.assertFalse(game.isMinimized(), "Aborting Virtual Switcher mode must not minimize")

            # Re-enter Virtual Switcher with [UP, UP]
            for _ in range(2):
                ev = QKeyEvent(QEvent.Type.KeyPress, Qt.Key.Key_Up, Qt.KeyboardModifier.NoModifier)
                game.keyPressEvent(ev)
            self.assertTrue(game.virtual_switcher_active)

            # Wait past decay timeout (0.15s > 0.1s)
            time.sleep(0.15)
            game._on_tick()

            # Send [DOWN, DOWN]
            for _ in range(2):
                ev = QKeyEvent(QEvent.Type.KeyPress, Qt.Key.Key_Down, Qt.KeyboardModifier.NoModifier)
                game.keyPressEvent(ev)

            # Because timeout decayed the buffer, it must NOT trigger Quick-Switch
            self.assertNotEqual(game.current_key_title, "⚡ QUICK SWITCH ⚡")

            # Re-enter Virtual Switcher organically with [UP, UP] and commit via Enter
            for _ in range(2):
                ev = QKeyEvent(QEvent.Type.KeyPress, Qt.Key.Key_Up, Qt.KeyboardModifier.NoModifier)
                game.keyPressEvent(ev)
            self.assertTrue(game.virtual_switcher_active)

            ev_enter = QKeyEvent(QEvent.Type.KeyPress, Qt.Key.Key_Return, Qt.KeyboardModifier.NoModifier)
            game.keyPressEvent(ev_enter)
            self.assertFalse(game.virtual_switcher_active)
            self.assertTrue(game.isMinimized(), "Enter in Virtual Switcher mode must commit handover and minimize")

        game.force_close()

    def test_14_full_konami_code(self):
        """Verify Option C: [↑, ↑, ↓, ↓, ←, →, ←, →, B, A] triggers 60-particle Konami explosion and banner."""
        game = JimHaGame(enable_audio=False, is_windowed=False)
        game.resize(800, 600)
        game.show()

        mock_windows = [{"id": "win_konami_1", "title": "Konami App", "icon": "konami-app"}]
        with patch("jimha.main.query_open_windows", return_value=mock_windows), \
             patch("jimha.main.activate_window_by_id"):
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
        self.assertTrue(game._handover_active, "Handover flag must be active while minimized")

        # Restore window (simulating user clicking taskbar or OS restore with activation)
        game.activateWindow()
        game.showNormal()
        QApplication.processEvents()
        self.assertFalse(game.isMinimized(), "Window should no longer be minimized")
        self.assertTrue(game.isFullScreen(), "Window restore must auto-relock fullscreen kiosk mode")
        self.assertFalse(game._handover_active, "Window restoration must clear _handover_active")

        game.force_close()

    def test_16_rekka_navigator_idle_timeout(self):
        """Verify Virtual Switcher 15.0s idle timeout gently returns to canvas without minimizing."""
        game = JimHaGame(enable_audio=False, is_windowed=False)
        game.resize(800, 600)
        game.show()

        # Organically enter Virtual Switcher via [UP, UP]
        for _ in range(2):
            ev = QKeyEvent(QEvent.Type.KeyPress, Qt.Key.Key_Up, Qt.KeyboardModifier.NoModifier)
            game.keyPressEvent(ev)
        self.assertTrue(game.virtual_switcher_active, "Double UP must enter Virtual Switcher mode")

        # Simulate 15.0s idle timeout passing
        game.virtual_switcher_last_action_time = time.time() - 16.0
        game._on_tick()

        self.assertFalse(game.virtual_switcher_active, "Idle timeout must exit Virtual Switcher mode")
        self.assertFalse(game.isMinimized(), "Virtual Switcher idle timeout must gently return to canvas without minimizing")
        game.force_close()

    def test_17_rekka_navigator_stack_walking(self):
        """Verify Virtual Switcher arrow keys step index with wrapping and refresh activity time."""
        game = JimHaGame(enable_audio=False, is_windowed=False)
        game.resize(800, 600)
        game.show()

        mock_windows = [
            {"id": "win1", "title": "App 1", "icon": "app1"},
            {"id": "win2", "title": "App 2", "icon": "app2"},
            {"id": "win3", "title": "App 3", "icon": "app3"},
        ]

        with patch("jimha.main.query_open_windows", return_value=mock_windows):
            # Organically enter Virtual Switcher via [UP, UP]
            for _ in range(2):
                ev = QKeyEvent(QEvent.Type.KeyPress, Qt.Key.Key_Up, Qt.KeyboardModifier.NoModifier)
                game.keyPressEvent(ev)

            self.assertTrue(game.virtual_switcher_active)
            self.assertEqual(game.virtual_switcher_index, 0)
            self.assertEqual(len(game.virtual_switcher_windows), 3)
            t_init = game.virtual_switcher_last_action_time

            # Paint HUD organically in Virtual Switcher mode
            game.repaint()

            # Press DOWN: advance forward organically
            time.sleep(0.01)
            ev_down = QKeyEvent(QEvent.Type.KeyPress, Qt.Key.Key_Down, Qt.KeyboardModifier.NoModifier)
            game.keyPressEvent(ev_down)
            self.assertEqual(game.virtual_switcher_index, 1, "Down arrow must advance stack index forward")
            self.assertGreaterEqual(game.virtual_switcher_last_action_time, t_init)

            # Press RIGHT (→): advance forward
            t_prev = game.virtual_switcher_last_action_time
            time.sleep(0.01)
            ev_right = QKeyEvent(QEvent.Type.KeyPress, Qt.Key.Key_Right, Qt.KeyboardModifier.NoModifier)
            game.keyPressEvent(ev_right)
            self.assertEqual(game.virtual_switcher_index, 2, "Right arrow must advance stack index forward")
            self.assertGreaterEqual(game.virtual_switcher_last_action_time, t_prev)

            # Press LEFT (←): advance backward
            t_prev2 = game.virtual_switcher_last_action_time
            time.sleep(0.01)
            ev_left = QKeyEvent(QEvent.Type.KeyPress, Qt.Key.Key_Left, Qt.KeyboardModifier.NoModifier)
            game.keyPressEvent(ev_left)
            self.assertEqual(game.virtual_switcher_index, 1, "Left arrow must advance stack index backward")
            self.assertGreaterEqual(game.virtual_switcher_last_action_time, t_prev2)

            # Press UP (↑): advance backward
            ev_up = QKeyEvent(QEvent.Type.KeyPress, Qt.Key.Key_Up, Qt.KeyboardModifier.NoModifier)
            game.keyPressEvent(ev_up)
            self.assertEqual(game.virtual_switcher_index, 0)

            # Press UP (↑): advance backward with wraparound (0 -> 2)
            game.keyPressEvent(ev_up)
            self.assertEqual(game.virtual_switcher_index, 2, "Up arrow in virtual switcher must wrap backward to last window")

            # Press Escape: aborts switcher cleanly
            ev_esc = QKeyEvent(QEvent.Type.KeyPress, Qt.Key.Key_Escape, Qt.KeyboardModifier.NoModifier)
            game.keyPressEvent(ev_esc)
            self.assertFalse(game.virtual_switcher_active, "Escape must abort Virtual Switcher mode")
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

    def test_19_handover_active_prevents_focus_hijacking(self):
        """Verify _handover_active prevents changeEvent and focusOutEvent from hijacking focus."""
        game = JimHaGame(enable_audio=False, is_windowed=False)
        game.resize(800, 600)
        game.showFullScreen()

        # Engage desktop handover
        game._handover_to_desktop()
        self.assertTrue(game._handover_active)
        self.assertTrue(game.isMinimized())

        # 1. ActivationChange during handover must NOT activate, raise, or steal focus
        with patch.object(game, "activateWindow") as mock_act, \
             patch.object(game, "raise_") as mock_raise, \
             patch.object(game, "setFocus") as mock_focus:
            ev_act = QEvent(QEvent.Type.ActivationChange)
            game.changeEvent(ev_act)
            mock_act.assert_not_called()
            mock_raise.assert_not_called()
            mock_focus.assert_not_called()

        # 2. FocusOut during handover must NOT steal back focus
        with patch.object(game, "setFocus") as mock_focus:
            ev_focus_out = QFocusEvent(QEvent.Type.FocusOut)
            game.focusOutEvent(ev_focus_out)
            mock_focus.assert_not_called()

        # 3. WindowStateChange while still minimized must NOT call showFullScreen
        with patch.object(game, "showFullScreen") as mock_fs:
            ev_state = QEvent(QEvent.Type.WindowStateChange)
            game.changeEvent(ev_state)
            mock_fs.assert_not_called()

        game.force_close()

    def test_20_window_restoration_clears_handover_active_and_relocks(self):
        """Verify that genuine user restoration resets handover flag and relocks fullscreen kiosk."""
        game = JimHaGame(enable_audio=False, is_windowed=False)
        game.resize(800, 600)
        game.showFullScreen()

        game._handover_to_desktop()
        self.assertTrue(game._handover_active)

        # Restore window by un-minimizing
        game.showNormal()
        QApplication.processEvents()

        self.assertFalse(game._handover_active, "Handover flag must be cleared on window restore")
        self.assertTrue(game.isFullScreen(), "Window must auto-relock fullscreen")
        self.assertFalse(game.isMinimized())

        game.force_close()

    def test_21_ensure_kwin_shortcut_inhibition(self):
        """Verify ensure_kwin_shortcut_inhibition sets kwin rules and handles errors transparently."""
        # 1. Missing binaries returns False without error
        with patch("shutil.which", return_value=None):
            self.assertFalse(ensure_kwin_shortcut_inhibition())

        # 2. SubprocessError returns False transparently and logs warning
        with patch("shutil.which", side_effect=lambda cmd: f"/usr/bin/{cmd}"), \
             patch("subprocess.run", side_effect=subprocess.SubprocessError("kreadconfig failure")), \
             self.assertLogs("jimha", level="WARNING") as cm:
            self.assertFalse(ensure_kwin_shortcut_inhibition())
            self.assertTrue(any("kreadconfig failure" in log_msg for log_msg in cm.output))

        # 3. FileNotFoundError returns False transparently and logs warning
        with patch("shutil.which", side_effect=lambda cmd: f"/usr/bin/{cmd}"), \
             patch("subprocess.run", side_effect=FileNotFoundError("binary not found")), \
             self.assertLogs("jimha", level="WARNING") as cm:
            self.assertFalse(ensure_kwin_shortcut_inhibition())
            self.assertTrue(any("binary not found" in log_msg for log_msg in cm.output))

        # 4. Fresh setup where kreadconfig6 returns returncode 1 (empty rules)
        with patch("shutil.which", side_effect=lambda cmd: f"/usr/bin/{cmd}"), \
             patch("subprocess.run") as mock_run:
            mock_read_res = MagicMock()
            mock_read_res.returncode = 1
            mock_read_res.stdout = ""
            mock_run.return_value = mock_read_res

            res = ensure_kwin_shortcut_inhibition()
            self.assertTrue(res)

            # Check that kwriteconfig6 was called to update rules and write properties
            cmd_lines = [" ".join(call_item.args[0]) for call_item in mock_run.call_args_list]
            self.assertTrue(any("jimha_lockdown" in line and "rules" in line for line in cmd_lines))
            self.assertTrue(any("disableglobalshortcuts" in line for line in cmd_lines))
            self.assertTrue(any("reconfigure" in line for line in cmd_lines))

        # 5. Rule not present with other existing rules: writes jimha_lockdown rules and notifies KWin
        with patch("shutil.which", side_effect=lambda cmd: f"/usr/bin/{cmd}"), \
             patch("subprocess.run") as mock_run:
            mock_read_res = MagicMock()
            mock_read_res.returncode = 0
            mock_read_res.stdout = "other_rule1,other_rule2\n"
            mock_run.return_value = mock_read_res

            res = ensure_kwin_shortcut_inhibition()
            self.assertTrue(res)

            cmd_lines = [" ".join(call_item.args[0]) for call_item in mock_run.call_args_list]
            self.assertTrue(any("other_rule1,other_rule2,jimha_lockdown" in line and "rules" in line for line in cmd_lines))
            self.assertTrue(any("disableglobalshortcuts" in line for line in cmd_lines))
            self.assertTrue(any("reconfigure" in line for line in cmd_lines))

        # 6. Rule already present: returns True without running write or reconfigure commands
        with patch("shutil.which", side_effect=lambda cmd: f"/usr/bin/{cmd}"), \
             patch("subprocess.run") as mock_run:
            mock_read_res = MagicMock()
            mock_read_res.returncode = 0
            mock_read_res.stdout = "other_rule1,jimha_lockdown\n"
            mock_run.return_value = mock_read_res

            res = ensure_kwin_shortcut_inhibition()
            self.assertTrue(res)
            # Only the initial read was performed
            self.assertEqual(mock_run.call_count, 1)

    def test_22_navigator_sequence_visual_takeover(self):
        """Verify [UP, UP] triggers Virtual Switcher activation."""
        game = JimHaGame(enable_audio=False, is_windowed=False)
        game.resize(800, 600)
        game.show()

        mock_windows = [{"id": "win_nav_1", "title": "Nav App", "icon": "nav-app"}]
        with patch("jimha.main.query_open_windows", return_value=mock_windows):
            # Send [UP, UP]
            for _ in range(2):
                ev = QKeyEvent(QEvent.Type.KeyPress, Qt.Key.Key_Up, Qt.KeyboardModifier.NoModifier)
                game.keyPressEvent(ev)

            self.assertTrue(game.virtual_switcher_active, "Double UP must activate Virtual Switcher")
            self.assertGreaterEqual(len(game.particles), 20, "Virtual Switcher activation must spawn at least 20 particles")

        game.force_close()

    def test_23_query_open_windows_parser(self):
        """Verify query_open_windows parses qdbus output, filters JimHa/empty titles, and deduplicates."""
        sample_qdbus_output = (
            '[Argument: a(sssuda{sv}) {'
            '[Argument: (sssida{sv}) "0_{uuid1}", "jimha — Dolphin", "org.kde.dolphin", 30, 0.5, [Argument: a{sv} {}]], '
            '[Argument: (sssida{sv}) "0_{uuid2}", "JimHa\'s Magical Key Smash Game", "jimha", 30, 0.5, [Argument: a{sv} {}]], '
            '[Argument: (sssida{sv}) "0_{uuid3}", "", "empty-icon", 30, 0.5, [Argument: a{sv} {}]], '
            '[Argument: (sssida{sv}) "0_{uuid1}", "Duplicate Dolphin", "org.kde.dolphin", 30, 0.5, [Argument: a{sv} {}]], '
            '[Argument: (sssida{sv}) "0_{uuid4}", "Mozilla Firefox", "firefox", 30, 0.5, [Argument: a{sv} {}]]'
            '}]'
        )

        with patch("subprocess.run") as mock_run:
            mock_res = MagicMock()
            mock_res.returncode = 0
            mock_res.stdout = sample_qdbus_output
            mock_run.return_value = mock_res

            wins = query_open_windows()

            self.assertEqual(len(wins), 2)
            self.assertEqual(wins[0]["id"], "0_{uuid1}")
            self.assertEqual(wins[0]["title"], "jimha — Dolphin")
            self.assertEqual(wins[0]["icon"], "org.kde.dolphin")

            self.assertEqual(wins[1]["id"], "0_{uuid4}")
            self.assertEqual(wins[1]["title"], "Mozilla Firefox")
            self.assertEqual(wins[1]["icon"], "firefox")

        # Fallback when empty output or no windows found
        with patch("subprocess.run") as mock_run:
            mock_res = MagicMock()
            mock_res.returncode = 0
            mock_res.stdout = "[]"
            mock_run.return_value = mock_res

            fallback_wins = query_open_windows()
            self.assertEqual(fallback_wins, [{"id": "desktop", "title": "Desktop / Workspace", "icon": "user-desktop"}])

        # Fallback when subprocess raises exception
        with patch("subprocess.run", side_effect=subprocess.SubprocessError("DBus timeout")):
            err_wins = query_open_windows()
            self.assertEqual(err_wins, [{"id": "desktop", "title": "Desktop / Workspace", "icon": "user-desktop"}])

    def test_24_activate_window_by_id_dbus(self):
        """Verify activate_window_by_id calls /WindowsRunner Run or /KWin showDesktop."""
        with patch("subprocess.run") as mock_run, patch("shutil.which", return_value="/usr/bin/qdbus"):
            mock_res = MagicMock()
            mock_res.returncode = 0
            mock_run.return_value = mock_res

            # Desktop target
            res_desk = activate_window_by_id("desktop")
            self.assertTrue(res_desk)
            mock_run.assert_called_with(
                ["/usr/bin/qdbus", "org.kde.KWin", "/KWin", "showDesktop", "true"],
                capture_output=True,
                text=True,
                timeout=2.0,
                check=False,
            )

            # Application window target
            res_win = activate_window_by_id("0_{target_win_id}")
            self.assertTrue(res_win)
            mock_run.assert_called_with(
                ["/usr/bin/qdbus", "org.kde.KWin", "/WindowsRunner", "org.kde.krunner1.Run", "0_{target_win_id}", ""],
                capture_output=True,
                text=True,
                timeout=2.0,
                check=False,
            )

        # Exception handling returns False
        with patch("subprocess.run", side_effect=Exception("D-Bus failure")):
            res_fail = activate_window_by_id("0_{target_win_id}")
            self.assertFalse(res_fail)

    def test_25_virtual_switcher_navigation_and_wraparound(self):
        """Verify Virtual Switcher carousel navigation, wraparound, Escape cancel, and Enter commit."""
        game = JimHaGame(enable_audio=False, is_windowed=False)
        game.resize(800, 600)
        game.show()

        mock_windows = [
            {"id": "win1", "title": "App 1", "icon": "app1"},
            {"id": "win2", "title": "App 2", "icon": "app2"},
            {"id": "win3", "title": "App 3", "icon": "app3"},
        ]

        with patch("jimha.main.query_open_windows", return_value=mock_windows):
            # Organically send [UP, UP]
            for _ in range(2):
                ev = QKeyEvent(QEvent.Type.KeyPress, Qt.Key.Key_Up, Qt.KeyboardModifier.NoModifier)
                game.keyPressEvent(ev)

            self.assertTrue(game.virtual_switcher_active)
            self.assertEqual(game.virtual_switcher_index, 0)
            self.assertEqual(len(game.virtual_switcher_windows), 3)

            # Paint offscreen to verify _draw_virtual_switcher executes cleanly
            game.repaint()

            # DOWN immediately after [UP, UP] -> advances from 0 to 1
            ev_d = QKeyEvent(QEvent.Type.KeyPress, Qt.Key.Key_Down, Qt.KeyboardModifier.NoModifier)
            game.keyPressEvent(ev_d)
            self.assertEqual(game.virtual_switcher_index, 1, "Down arrow immediately after entering switcher must advance index to 1")

            # RIGHT -> advances from 1 to 2
            ev_r = QKeyEvent(QEvent.Type.KeyPress, Qt.Key.Key_Right, Qt.KeyboardModifier.NoModifier)
            game.keyPressEvent(ev_r)
            self.assertEqual(game.virtual_switcher_index, 2)

            # DOWN -> wraps from 2 to 0
            game.keyPressEvent(ev_d)
            self.assertEqual(game.virtual_switcher_index, 0)

            # LEFT -> wraps from 0 to 2
            ev_l = QKeyEvent(QEvent.Type.KeyPress, Qt.Key.Key_Left, Qt.KeyboardModifier.NoModifier)
            game.keyPressEvent(ev_l)
            self.assertEqual(game.virtual_switcher_index, 2)

            # UP -> steps backward from 2 to 1
            ev_u = QKeyEvent(QEvent.Type.KeyPress, Qt.Key.Key_Up, Qt.KeyboardModifier.NoModifier)
            game.keyPressEvent(ev_u)
            self.assertEqual(game.virtual_switcher_index, 1)

            # UP -> steps backward from 1 to 0
            game.keyPressEvent(ev_u)
            self.assertEqual(game.virtual_switcher_index, 0)

            # Escape -> cancels switcher without minimizing
            ev_esc = QKeyEvent(QEvent.Type.KeyPress, Qt.Key.Key_Escape, Qt.KeyboardModifier.NoModifier)
            game.keyPressEvent(ev_esc)
            self.assertFalse(game.virtual_switcher_active)
            self.assertFalse(game.isMinimized())

            # Re-enter via [UP, UP]
            for _ in range(2):
                game.keyPressEvent(ev_u)
            self.assertTrue(game.virtual_switcher_active)
            self.assertEqual(game.virtual_switcher_index, 0)

            # Step to index 1 (win2)
            game.keyPressEvent(ev_r)
            self.assertEqual(game.virtual_switcher_index, 1)

            # Enter -> commits handover to win2
            with patch("jimha.main.activate_window_by_id") as mock_act:
                ev_enter = QKeyEvent(QEvent.Type.KeyPress, Qt.Key.Key_Return, Qt.KeyboardModifier.NoModifier)
                game.keyPressEvent(ev_enter)

                self.assertFalse(game.virtual_switcher_active)
                self.assertTrue(game.isMinimized())
                self.assertTrue(game._handover_active)
                mock_act.assert_called_once_with("win2")

        game.force_close()

    def test_26_quick_switch_definite_handover(self):
        """Verify Quick Switch queries windows, calls _handover_to_desktop with target ID, and strips stays-on-top."""
        game = JimHaGame(enable_audio=False, is_windowed=False)
        game.resize(800, 600)
        game.show()

        mock_windows = [{"id": "target_win_99", "title": "Editor", "icon": "kate"}]

        with patch("jimha.main.query_open_windows", return_value=mock_windows), \
             patch("jimha.main.activate_window_by_id") as mock_act:

            # Send [UP, UP, DOWN, DOWN]
            for key in [Qt.Key.Key_Up, Qt.Key.Key_Up, Qt.Key.Key_Down, Qt.Key.Key_Down]:
                ev = QKeyEvent(QEvent.Type.KeyPress, key, Qt.KeyboardModifier.NoModifier)
                game.keyPressEvent(ev)

            self.assertEqual(game.current_key_title, "⚡ QUICK SWITCH ⚡")
            self.assertEqual(game.current_subtitle, "Desktop Handover Activated")
            self.assertFalse(game.isMinimized())

            # Allow 150ms singleShot delay to elapse
            time.sleep(0.2)
            QApplication.processEvents()

            self.assertTrue(game.isMinimized(), "Quick Switch must minimize JimHa")
            self.assertTrue(game._handover_active, "Handover flag must be set")
            # Verify WindowStaysOnTopHint stripped
            self.assertFalse(
                bool(game.windowFlags() & Qt.WindowType.WindowStaysOnTopHint),
                "WindowStaysOnTopHint must be stripped on handover",
            )
            mock_act.assert_called_once_with("target_win_99")

        game.force_close()

    def test_27_get_app_icon_pixmap_none_and_negative_cache(self):
        """Verify _get_app_icon_pixmap safely handles None/empty strings and caches misses."""
        game = JimHaGame(enable_audio=False)

        # None icon name must not raise TypeError
        res_none = game._get_app_icon_pixmap(None, size=96)
        self.assertIsNone(res_none)
        self.assertIn("_96", game.virtual_switcher_pixmaps)
        self.assertTrue(game.virtual_switcher_pixmaps["_96"].isNull())

        # Second lookup should hit cache in O(1) without touching QIcon
        with patch("PyQt6.QtGui.QIcon.fromTheme") as mock_from_theme:
            res_cached = game._get_app_icon_pixmap(None, size=96)
            self.assertIsNone(res_cached)
            mock_from_theme.assert_not_called()

        game.force_close()

    def test_28_query_open_windows_warning_logging(self):
        """Verify query_open_windows logs warning on non-zero exit code or exception."""
        # Non-zero return code
        with patch("subprocess.run") as mock_run, self.assertLogs("jimha", level="WARNING") as cm:
            mock_res = MagicMock()
            mock_res.returncode = 1
            mock_res.stderr = "org.freedesktop.DBus.Error.ServiceUnknown"
            mock_run.return_value = mock_res

            wins = query_open_windows()
            self.assertEqual(wins, [{"id": "desktop", "title": "Desktop / Workspace", "icon": "user-desktop"}])
            self.assertTrue(any("ServiceUnknown" in msg for msg in cm.output))

        # Subprocess exception
        with patch("subprocess.run", side_effect=subprocess.SubprocessError("DBus timeout")), \
             self.assertLogs("jimha", level="WARNING") as cm:
            err_wins = query_open_windows()
            self.assertEqual(err_wins, [{"id": "desktop", "title": "Desktop / Workspace", "icon": "user-desktop"}])
            self.assertTrue(any("DBus timeout" in msg for msg in cm.output))

    def test_29_activate_window_by_id_warning_logging(self):
        """Verify activate_window_by_id logs warning on non-zero exit code or exception."""
        # Non-zero return code
        with patch("subprocess.run") as mock_run, self.assertLogs("jimha", level="WARNING") as cm:
            mock_res = MagicMock()
            mock_res.returncode = 1
            mock_res.stderr = "Invalid window handle"
            mock_run.return_value = mock_res

            res = activate_window_by_id("invalid_win")
            self.assertFalse(res)
            self.assertTrue(any("Invalid window handle" in msg for msg in cm.output))

        # Subprocess exception
        with patch("subprocess.run", side_effect=Exception("Connection lost")), \
             self.assertLogs("jimha", level="WARNING") as cm:
            res_ex = activate_window_by_id("invalid_win")
            self.assertFalse(res_ex)
            self.assertTrue(any("Connection lost" in msg for msg in cm.output))

    def test_30_handover_window_activation_failure_logging(self):
        """Verify _handover_to_desktop logs warning when window activation returns False."""
        game = JimHaGame(enable_audio=False, is_windowed=False)
        with patch("jimha.main.activate_window_by_id", return_value=False), \
             self.assertLogs("jimha", level="WARNING") as cm:
            game._handover_to_desktop(target_match_id="win_fail")
            self.assertTrue(any("Handover window activation failed" in msg for msg in cm.output))
        game.force_close()


if __name__ == "__main__":
    unittest.main()

