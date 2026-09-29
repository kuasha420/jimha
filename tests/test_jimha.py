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
from PyQt6.QtGui import QKeyEvent
from PyQt6.QtWidgets import QApplication

from jimha.sound_synth import SoundBank, generate_chime_wav
from jimha.main import JimHaGame, ALPHABET_COMPANIONS


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


if __name__ == "__main__":

    unittest.main()

