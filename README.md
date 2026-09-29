<div align="center">

<img src="assets/jimha.png" width="160" height="160" alt="JimHa's Key Smash Logo" />

# JimHa's Magical Key Smash Game 👑💖✨

**A toddler-safe, fullscreen interactive wonderland designed for tactile exploration.**

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Arch Linux](https://img.shields.io/badge/Arch_Linux-PKGBUILD_Ready-1793d1.svg?logo=arch-linux)](PKGBUILD)
[![Platform: Linux / Wayland](https://img.shields.io/badge/Platform-Linux%20%2F%20Wayland-2A3439.svg?logo=linux)](https://github.com/kuasha420/jimha)
[![Knot Mesh Compatible](https://img.shields.io/badge/Knot_Mesh-Integrated-FF4081.svg)](https://github.com/kuasha420/knot-mesh)

</div>

---

## 🎮 Steam-Style Product Showcase

<table>
<tr>
<td width="65%" valign="top">

<!-- Steam Hero Animated Trailer / Banner -->
<img src="assets/demo_preview.gif" alt="JimHa Animated Gameplay Trailer" width="100%" />

<p align="center">
  🎬 <b>Live Gameplay Trailer:</b> <i>Bouncing letters, particle fireworks, pentatonic chimes & 3s hold-to-exit HUD</i>
  <br>
  <a href="assets/demo_trailer.mp4"><b>▶ Download / Watch Full HD Video Trailer (assets/demo_trailer.mp4)</b></a>
</p>

</td>
<td width="35%" valign="top">

### 🕹️ Game Overview
*Smash any button, paint the universe!* A gentle, toddler-proof sensory playground crafted with love for JimHa.

- **Reviews**: ⭐⭐⭐⭐⭐ *Overwhelmingly Positive* (100% Toddler & Baby Approved 💖)
- **Release Date**: Sep 29, 2026
- **Developer**: Arafat Zahan *(with JimHa & AI Agent)*
- **Publisher**: Purrfect Universe
- **Audio Engine**: Zero-Dependency Pentatonic Chimes
- **Display Target**: Wayland / X11 Fullscreen 60 FPS
- **Tags**: `Casual` • `Kids` • `Tactile` • `Sensory` • `Toddler-Safe` • `Music-Box`

</td>
</tr>
</table>

### 📸 Gameplay Screenshots

<table>
<tr>
<td width="50%">
  <img src="assets/screenshot_2_jimha_crown.png" alt="J is for JimHa!" width="100%" />
  <p align="center"><b>👑 J is for JimHa!</b><br><i>Spring bounce with royal crown & electric confetti</i></p>
</td>
<td width="50%">
  <img src="assets/screenshot_3_easter_egg.png" alt="Jim Heart Easter Egg" width="100%" />
  <p align="center"><b>💖 Jim Heart Easter Egg</b><br><i>The legendary Easter egg honoring the session's first spark</i></p>
</td>
</tr>
<tr>
<td width="50%">
  <img src="assets/screenshot_4_supernova.png" alt="Cosmic Supernova" width="100%" />
  <p align="center"><b>🌟 Cosmic Supernova</b><br><i>Pressing Space explodes rainbow starburst particles</i></p>
</td>
<td width="50%">
  <img src="assets/screenshot_5_exit_hud.png" alt="Toddler-Safe Exit HUD" width="100%" />
  <p align="center"><b>🛡️ Toddler-Safe Exit HUD</b><br><i>Hold ESC for 3.0s continuously to close; quick taps never exit</i></p>
</td>
</tr>
</table>

---

## 📖 The Origin Story

**JimHa's Key Smash Game** was born during JimHa's very first **agentic pair programming session**. 

Sitting with a Steam Deck handheld running Arch Linux, her father gave a simple, loving challenge to an autonomous AI agent: create a magical visual playground for JimHa that reacts to any random keyboard smash with giant bouncing characters, colorful companion emojis, and soothing sounds — without letting curious little hands accidentally close the game.

Because the command originated from a handheld device, the entire prototype was orchestrated across the [**Knot Mesh**](https://github.com/kuasha420/knot-mesh) — projecting and running live in fullscreen on the Desktop PC monitor across the room in real time.

Today, **JimHa** is packaged as a standalone, production-ready desktop game for all Linux users, while proudly preserving its Knot Mesh multi-device origin.

---

## ✨ Features

- **🎮 Giant Responsive Key Animations**: Every key press triggers massive typography scaling with elastic spring physics, radiant glowing halos, and vibrant pastel-neon palettes.
- **🦄 Alphabet & Companion Emojis**:
  - **`J`**: 👑 **JimHa!** ✨
  - **`H`**: 💖 **Jim Heart (Easter Egg!)** 💖
  - **`A`–`Z`**: 🍎 Apple, 🦋 Butterfly, 🐱 Cat, 🐶 Dog, 🐘 Elephant, 🌸 Flower, 🎸 Guitar...
  - **`0`–`9`**: Huge digits accompanied by that exact number of glittering stars.
  - **`Space`**: 🌟 Cosmic supernova fireworks!
  - **`Enter`**: 🎉 Party celebration balloons and confetti!
  - **`Backspace`**: 🫧 Bubble pop flurry!
  - **`Arrow Keys`**: 🚀 Directional zoom and dive effects!
- **🫧 Touch & Mouse Interaction**: Tapping the screen or clicking spawns floating, translucent bubbles that rise and can be popped.
- **🎵 Soothing Pentatonic Chimes**: Built-in sound synthesis engine (using Python standard library `wave` and `math` with zero external audio dependencies). Plays celestial celesta/bell notes across an 11-tone pentatonic scale (C4–C6). Rapid smashing sounds like a melodious wind chime, never dissonant.
- **🛡️ Toddler-Safe Exit Protection (3-Second ESC Hold)**: Accidental hits on `Escape` will **not** close the game. To exit, a parent must hold `Escape` continuously for 3.0 seconds. A circular HUD countdown overlay displays progress and immediately cancels if released early.
- **⚡ Wayland & Hardware Accelerated**: Built on PyQt6 with native Wayland support (`QT_QPA_PLATFORM=wayland`) and intelligent idle framerate scaling (60 FPS active, 30 FPS resting) to preserve battery and GPU cycles.

---

## 📦 Installation

### Arch Linux / SteamOS (Desktop Mode)

You can build and install using the included `PKGBUILD`:

```bash
# Clone the repository
git clone https://github.com/kuasha420/jimha.git
cd jimha

# Build and install package
makepkg -si
```

This installs:
- Binary: `/usr/bin/jimha`
- Desktop Entry: `/usr/share/applications/jimha.desktop` (visible in KDE/GNOME/Steam application menus)
- App Icon: `/usr/share/icons/hicolor/scalable/apps/jimha.svg` and `512x512/apps/jimha.png`

### Standard Python / Manual Installation

```bash
# Clone the repository
git clone https://github.com/kuasha420/jimha.git
cd jimha

# Install dependencies
pip install PyQt6

# Install locally
pip install .
```

---

## 🚀 Usage

### Run from App Menu
Look for **JimHa's Key Smash** in your desktop application launcher under **Games**.

### Run from Terminal

```bash
# Launch in Fullscreen (Default)
jimha

# Launch in Windowed mode (for debugging)
jimha --windowed

# Launch with sound muted
jimha --no-audio
```

### 🪢 Knot Mesh Remote Launch

If you run the [Knot Mesh](https://github.com/kuasha420/knot-mesh) multi-device fabric across your home:

```bash
# Launch remotely on Desktop PC from Steam Deck or Laptop
jimha --mesh-target desktop
```

---

## 🧪 Testing

Run the automated test suite in headless mode:

```bash
QT_QPA_PLATFORM=offscreen python3 -m unittest discover -s tests
```

---

## 📄 License

Released under the [MIT License](LICENSE). Dedicated with love to JimHa. 💖
