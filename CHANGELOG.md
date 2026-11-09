# Changelog

All notable changes to Jimha will be documented in this file.
The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [2.0.0-a62efdb] - 2026-11-09

### 🚀 Consolidated Milestone Prerelease

This release delivers complete sovereign in-process audio, handheld controller optimization, kiosk containment, and toddler-proof input filtering.

---

### 🎵 1. Sovereign In-Process Audio Engine (`rodio v0.23`)

- **Zero OS Process Spawning**: Completely eliminated the external shellout anti-pattern (`pw-play` / `paplay` CLI child processes). Audio is now mixed and synthesized entirely in-process using `rodio 0.23` and `cpal`.
- **Elimination of `pw-cat` Churn**: Zero OS process table churn, zero pipewire IPC bottlenecks, and zero ephemeral `pw-cat` streams during high-velocity toddler drumming.
- **Single-Sink Audio Routing**: Eliminated dual-firing bug where Tauri IPC and Web Audio API played concurrently. In desktop/kiosk mode, audio routes exclusively to the native in-process engine; Web Audio remains strictly a clean fallback for standalone web browsers.
- **Multi-Instrument Timbre Library**: Synchronized 4 pediatric sound profiles across both Rust PCM synthesizer and frontend Web Audio DSP:
  - ✨ _Celesta_ (crystalline bell chimes with harmonic shimmer)
  - 🪵 _Wooden Marimba_ (fast organic wooden bar strikes)
  - 🔔 _Gentle Kalimba_ (soothing metallic thumb piano tines)
  - 🎶 _Music Box_ (bright mechanical cylinder ring)
- **Steam Deck & Handheld Speaker Tuning**:
  - Embedded 90 Hz high-pass DC-blocking filter ($R \approx 0.987$) to protect small handheld speaker cones (Steam Deck, ROG Ally, laptop) from low-frequency intermodulation distortion and driver rattle.
- **Pediatric Hearing Safety Invariants**:
  - Hard master gain clamp $\le 0.80$ ($< -1.9\text{ dBFS}$).
  - $1/\sqrt{N}$ polyphonic chord normalization on Spacebar and Enter.
  - 4ms click-free attack envelopes.

---

### 🎶 2. Continuous Dynamic BGM & Real-Time Muffling Filter

- **Continuous 3-Layer Soundscape**:
  - Sub-Bass Warm Pad Drone ($C_3$ sine) anchoring the harmonic center.
  - Cascading Pentatonic Arpeggios ($C_4$–$C_5$).
  - Generative Music Box Lead Melody ($C_5$–$C_6$).
- **Dynamic Acoustic Muffling**:
  - During active toddler play (`notifyInput()`): Real-time low-pass filter cutoff sweeps down from $2500\text{ Hz} \rightarrow 450\text{ Hz}$ over $0.2\text{ s}$ and BGM volume ducks to $0.05$. BGM recedes into a warm, muffled hum behind interactive chimes.
  - Idle Auto-Recovery: After $3.5\text{ s}$ of inactivity, the filter smoothly re-opens from $450\text{ Hz} \rightarrow 2500\text{ Hz}$ over $1.5\text{ s}$ and volume returns to $0.14$, bringing back glistening music box melodies.

---

### 🎮 3. Steam Deck & Handheld Controller Integration

- **Input Shadow Filter (`InputShadowFilter`)**:
  - Developed a deterministic shadow filter to eliminate "double button press syndrome" caused by Steam Desktop controller configurations emitting both native Gamepad API events and synthetic keyboard/mouse events.
  - Suppresses synthetic duplicate keystrokes (`Enter`, `Escape`, `Space`) when hardware face buttons (`A`, `B`, `X`, `Y`) are pressed.
- **Controller Exit & Switcher Gates**:
  - _Controller Exit_: Hold `SELECT + START` continuously for $2.5\text{ s}$ with radial countdown HUD.
  - _Controller Window Switcher_: Hold `L3 + R3` for $1.5\text{ s}$ to access the virtual window switcher.

---

### 🛡️ 4. Multi-Touch Kiosk Containment & Anti-Breakout Hardening

- **Multi-Touch Pinch-to-Zoom Lock**:
  - Locked viewport in `index.html` (`user-scalable=no, maximum-scale=1.0, minimum-scale=1.0`).
  - Intercepted and neutralized WebKitGTK gesture events (`gesturestart`, `gesturechange`, `gestureend`) and `ctrl + wheel` events, preventing toddlers from accidentally shrinking or scaling the canvas.
- **Kiosk Window Focus Retention**:
  - Added autonomous refocus watchdog that detects unexpected focus loss (e.g. Steam button breakout or system overlay notifications) and re-claims fullscreen focus within 50ms.
- **Parent Lock Button UX Refinement**:
  - Removed accidental quick-tap (<0.6s) trigger on the top-right "Parent Lock" button that previously opened the adult window switcher on accidental toddler screen taps.
  - Single taps now do **nothing** adult-facing. Only a deliberate $2.5\text{ s}$ continuous hold triggers the radial Exit Gate.

---

### 📐 5. Fluid Typography & Responsive Handheld Viewport Engine

- **Mathematical Viewport Bounds**:
  - Replaced fixed CSS units with dynamic clamped fluid sizing (`clamp(...)`), ensuring text and companion cards never clip offscreen on 800p handheld displays (1280x800) or 4K workstations.

---

### 📦 6. Packaging, Distribution & Local Binary Hygiene

- **Local Binary Shadowing Resolution**:
  - Resolved issue where `~/.local/bin/jimha` shadowed `/usr/bin/jimha` by establishing canonical symlinks across all deployment targets.
- **Multi-Target Release Artifacts**:
  - Arch Linux package (`.pkg.tar.zst`)
  - Steam Deck zero-sudo user-space tarball (`.tar.gz`)
  - Debian package (`.deb`)
  - Cryptographic checksums (`SHA256SUMS.txt`)
