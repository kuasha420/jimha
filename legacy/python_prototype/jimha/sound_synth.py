"""
Sound synthesis module for JimHa's Key Smash Game.
Generates and caches soothing pentatonic chimes using standard Python wave and math libraries.
Prioritizes native game-role audio streams (pw-play / paplay) to prevent system notification muting.
Zero external audio generation dependencies.
"""

import math
import os
import shutil
import struct
import subprocess
import sys
import wave
from pathlib import Path
from typing import List, Optional

# Soothing pentatonic frequencies (Hz) across octaves 4, 5, and 6
PENTATONIC_FREQUENCIES: List[float] = [
    261.63,  # C4
    293.66,  # D4
    329.63,  # E4
    392.00,  # G4
    440.00,  # A4
    523.25,  # C5
    587.33,  # D5
    659.25,  # E5
    783.99,  # G5
    880.00,  # A5
    1046.50, # C6
]


def generate_chime_wav(
    filepath: Path,
    frequency: float,
    sample_rate: int = 44100,
    duration: float = 0.85,
) -> None:
    """
    Synthesize a celestial music-box chime with harmonic overtones,
    stereo spread, warm body, and normalized volume.
    """
    filepath.parent.mkdir(parents=True, exist_ok=True)
    n_samples = int(sample_rate * duration)
    samples_l: List[float] = []
    samples_r: List[float] = []

    # Subtle stereo phase offset between left and right channels
    phase_offset = math.pi * 0.08

    for i in range(n_samples):
        t = i / sample_rate
        # 4ms attack envelope to prevent clicks
        attack = min(1.0, t / 0.004)

        # Dual decay: fast shimmer decay + long fundamental sustain
        decay_body = math.exp(-2.5 * t)
        decay_shimmer = math.exp(-5.5 * t)

        # Harmonic spectrum (celesta / crystal bell / marimba)
        # Left channel
        s1_l = math.sin(2.0 * math.pi * frequency * t) * decay_body
        s2_l = 0.35 * math.sin(2.0 * math.pi * (2.0 * frequency) * t) * decay_body
        s3_l = 0.18 * math.sin(2.0 * math.pi * (3.0 * frequency) * t + phase_offset) * decay_shimmer
        s4_l = 0.10 * math.sin(2.0 * math.pi * (4.2 * frequency) * t) * decay_shimmer
        s5_l = 0.05 * math.sin(2.0 * math.pi * (5.4 * frequency) * t) * decay_shimmer

        # Right channel (subtle harmonic stereo spread)
        s1_r = math.sin(2.0 * math.pi * frequency * t + phase_offset * 0.5) * decay_body
        s2_r = 0.35 * math.sin(2.0 * math.pi * (2.0 * frequency) * t) * decay_body
        s3_r = 0.18 * math.sin(2.0 * math.pi * (3.0 * frequency) * t) * decay_shimmer
        s4_r = 0.10 * math.sin(2.0 * math.pi * (4.2 * frequency) * t + phase_offset) * decay_shimmer
        s5_r = 0.05 * math.sin(2.0 * math.pi * (5.4 * frequency) * t) * decay_shimmer

        val_l = attack * (s1_l + s2_l + s3_l + s4_l + s5_l)
        val_r = attack * (s1_r + s2_r + s3_r + s4_r + s5_r)
        samples_l.append(val_l)
        samples_r.append(val_r)

    # Normalize to 92% full scale (-0.7 dB) to prevent clipping while maximizing clarity
    max_peak = max(max(abs(s) for s in samples_l), max(abs(s) for s in samples_r), 1e-6)
    scale = 30000.0 / max_peak

    data = bytearray()
    for l, r in zip(samples_l, samples_r):
        il = int(max(-32767, min(32767, l * scale)))
        ir = int(max(-32767, min(32767, r * scale)))
        data.extend(struct.pack("<hh", il, ir))

    with wave.open(str(filepath), "wb") as wav_file:
        wav_file.setnchannels(2)
        wav_file.setsampwidth(2)
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(data)


class SoundBank:
    """
    Manages the bank of generated sound files and plays them smoothly.
    Prioritizes low-latency game-role audio backends to prevent accidental
    system notification muting on Linux desktops.
    """

    def __init__(self, cache_dir: Optional[Path] = None):
        if cache_dir is None:
            cache_dir = Path.home() / ".cache" / "jimha" / "sounds_v2"
        self.cache_dir = cache_dir
        self.sound_paths: List[Path] = []
        self._qsound_effects: List = []
        self._player_bin: Optional[str] = None
        self._player_type: Optional[str] = None
        self._proc_pool: List[subprocess.Popen] = []
        self._note_index: int = 0
        self._detect_player()
        self.ensure_sounds()

    def _detect_player(self) -> None:
        """Find the optimal system audio player command with game media role."""
        if shutil.which("pw-play"):
            self._player_bin = shutil.which("pw-play")
            self._player_type = "pw-play"
        elif shutil.which("paplay"):
            self._player_bin = shutil.which("paplay")
            self._player_type = "paplay"
        elif shutil.which("aplay"):
            self._player_bin = shutil.which("aplay")
            self._player_type = "aplay"
        else:
            self._player_bin = None
            self._player_type = "qt"

    def ensure_sounds(self) -> None:
        """Ensure all pentatonic chimes are synthesized and available on disk."""
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.sound_paths = []
        for idx, freq in enumerate(PENTATONIC_FREQUENCIES):
            wav_path = self.cache_dir / f"chime_{idx}_{int(freq)}hz.wav"
            if not wav_path.exists() or wav_path.stat().st_size == 0:
                generate_chime_wav(wav_path, freq)
            self.sound_paths.append(wav_path)

    def init_qt_effects(self) -> None:
        """Qt fallback initialization for systems without pw-play / paplay."""
        # If we already have a native low-latency player (pw-play / paplay / aplay),
        # we bypass QSoundEffect because QSoundEffect is hardcoded to 'media.role=event'
        # which Linux desktop environments frequently mute.
        if self._player_type in ("pw-play", "paplay", "aplay"):
            return

        try:
            from PyQt6.QtCore import QUrl
            from PyQt6.QtMultimedia import QSoundEffect

            self._qsound_effects = []
            for path in self.sound_paths:
                effect = QSoundEffect()
                effect.setSource(QUrl.fromLocalFile(str(path)))
                effect.setVolume(1.0)
                effect.setMuted(False)
                self._qsound_effects.append(effect)
        except Exception as err:
            sys.stderr.write(f"Warning: Qt audio initialization failed: {err}\n")
            self._qsound_effects = []

    def close(self) -> None:
        """Wait for or terminate active background audio processes."""
        for p in self._proc_pool:
            if p.poll() is None:
                try:
                    p.wait(timeout=0.1)
                except subprocess.TimeoutExpired:
                    p.terminate()
                    try:
                        p.wait(timeout=0.5)
                    except subprocess.TimeoutExpired:
                        pass
        self._proc_pool = []

    def __del__(self) -> None:
        try:
            self.close()
        except Exception:
            pass

    def _spawn_player(self, cmd: List[str]) -> None:
        """Spawn background audio player process and track in pool."""
        # Prune dead child processes to prevent zombies and ResourceWarnings
        self._proc_pool = [p for p in self._proc_pool if p.poll() is None]
        try:
            proc = subprocess.Popen(
                cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            self._proc_pool.append(proc)
        except OSError as err:
            sys.stderr.write(f"Warning: Audio player execution failed: {err}\n")

    def play_key(self, key_text: str = "") -> None:
        """
        Play a harmonious chime corresponding to the key pressed.
        Cycles musically through the pentatonic scale.
        """
        if not self.sound_paths:
            return

        if key_text:
            idx = (ord(key_text[0]) + self._note_index) % len(self.sound_paths)
        else:
            idx = self._note_index % len(self.sound_paths)
        self._note_index = (self._note_index + 1) % len(self.sound_paths)
        wav_file = self.sound_paths[idx]

        # 1. Native low-latency system player with Game media role
        if self._player_type == "pw-play" and self._player_bin:
            self._spawn_player([self._player_bin, "--media-role=Game", "--volume=1.0", str(wav_file)])
            return

        if self._player_type == "paplay" and self._player_bin:
            self._spawn_player([self._player_bin, "--property=media.role=game", "--volume=65536", str(wav_file)])
            return

        if self._player_type == "aplay" and self._player_bin:
            self._spawn_player([self._player_bin, "-q", str(wav_file)])
            return

        # 2. In-process Qt fallback
        if self._qsound_effects and idx < len(self._qsound_effects):
            effect = self._qsound_effects[idx]
            effect.setMuted(False)
            effect.play()
            return
