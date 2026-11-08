<div align="center">

<img src="assets/jimha.png" width="160" height="160" alt="Jimha Logo" />

# Jimha 👑💖✨

**Next-Gen Sovereign Sensory Playground for Toddlers**  
_Smash any button, paint the universe!_

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Tauri v2](https://img.shields.io/badge/Tauri-v2-FFC131.svg?logo=tauri)](https://tauri.app)
[![Svelte 5 Runes](https://img.shields.io/badge/Svelte-5_Runes-FF3E00.svg?logo=svelte)](https://svelte.dev)
[![Pixi.js v8](https://img.shields.io/badge/Pixi.js-v8-E72264.svg?logo=pixijs)](https://pixijs.com)
[![PipeWire Native Audio](https://img.shields.io/badge/Audio-PipeWire_Native-26A69A.svg)](docs/ARCHITECTURE.md#3-double-barreled-audio-engine)
[![Local-First Sovereign](https://img.shields.io/badge/Architecture-100%25_Sovereign-4CAF50.svg)](docs/ARCHITECTURE.md#1-architectural-philosophy--the-sovereign-product-guarantee)
[![Platform: Multiplatform](https://img.shields.io/badge/Platform-Linux_|_SteamOS_|_Android-2A3439.svg)](docs/PACKAGING.md)

[**Documentation Hub**](docs/) • [**Architecture**](docs/ARCHITECTURE.md) • [**Dad-Mode Invariants**](docs/DAD_MODE_INVARIANTS.md) • [**Universe Lore**](docs/LORE.md) • [**Roadmap**](docs/ROADMAP.md) • [**Packaging**](docs/PACKAGING.md)

</div>

---

## 🎮 Steam-Style Product Showcase

<table>
<tr>
<td width="65%" valign="top">

<!-- Steam Hero Animated Trailer / Banner -->
<img src="assets/demo_preview.gif" alt="Jimha Animated Gameplay Trailer" width="100%" />

<p align="center">
  🎬 <b>Live Gameplay Trailer:</b> <i>Bouncing letters, particle fireworks, pentatonic chimes & 2.5s hold-to-exit HUD</i>
  <br>
  <a href="assets/demo_trailer.mp4"><b>▶ Download / Watch Full HD Video Trailer (assets/demo_trailer.mp4)</b></a>
</p>

</td>
<td width="35%" valign="top">

### 🕹️ Game Overview

_Smash any button, paint the universe!_ A gentle, toddler-proof sensory wonderland crafted with love for Jimha.

- **User Reviews**: ⭐⭐⭐⭐⭐ _Overwhelmingly Positive_ (100% Toddler & Baby Approved 💖)
- **Engine**: Tauri v2 + Pixi.js v8 + Svelte 5 (Runes) + Rust
- **Developer**: Arafat Zahan _(with Jimha & AI Agent)_
- **Audio Engine**: Double-Barreled PipeWire Native + Zero-GC Web Audio
- **Display Target**: Wayland / X11 / SteamOS Fullscreen 60–120 FPS
- **Safety Rating**: Certified Dad-Mode (7 Child-Safety Invariants)
- **Network Footprint**: 100% Air-Gapped / Zero External Sockets
- **Tags**: `Casual` • `Sensory` • `Toddler-Safe` • `Music-Box` • `Sovereign` • `Open-Source`

</td>
</tr>
</table>

### 📸 Gameplay Screenshots

<table>
<tr>
<td width="50%">
  <img src="assets/screenshot_2_jimha_crown.png" alt="J is for Jimha!" width="100%" />
  <p align="center"><b>👑 J is for Queen Jimha!</b><br><i>Spring bounce with royal crown, electric confetti, and fanfare chimes</i></p>
</td>
<td width="50%">
  <img src="assets/screenshot_3_easter_egg.png" alt="Jim Heart Easter Egg" width="100%" />
  <p align="center"><b>💖 Jim Heart Easter Egg</b><br><i>The cosmic alter ego born from the original voice-dictation spark</i></p>
</td>
</tr>
<tr>
<td width="50%">
  <img src="assets/screenshot_4_supernova.png" alt="Cosmic Supernova" width="100%" />
  <p align="center"><b>🌟 Cosmic Supernova</b><br><i>Spacebar triggers a dazzling starburst of 120 FPS rainbow particles</i></p>
</td>
<td width="50%">
  <img src="assets/screenshot_5_exit_hud.png" alt="Toddler-Safe Exit HUD" width="100%" />
  <p align="center"><b>🛡️ Toddler-Safe Exit HUD</b><br><i>Hold Shift + Esc for 2.5s to exit; forearm slaps and brief taps never quit</i></p>
</td>
</tr>
</table>

---

## 📖 The Origin Story: The Steam Deck Voice Prompt

Jimha was born during an autumn evening pairing session across the living room.

Sitting on a sofa with an Arch Linux handheld Steam Deck, Jimha's father watched her slap joyously at the illuminated mechanical keys of his desktop workstation across the room. Every errant swipe risked closing windows or killing terminal sessions. What she needed was not a locked screen—she needed a **living sensory universe** where every touch was answered with boundless joy.

Activating the Steam Deck's microphone, her father dictated a prompt in his native Bengali:

> _"ডিয়ার এজেন্ট, জিমহার জন্য এমন একটা ম্যাজিকাল প্লেগ্রাউন্ড বানাও—যেখানে ও যেকোনো কিবোর্ড বাটন চাপলেই বিশাল এনিমেশন, বাবল, তারা আর মিষ্টি পেন্টাটোনিক সুর বেজে উঠবে..."_  
> _(Dear agent, build a magical playground for Jimha—where whenever she hits any keyboard button, giant animations, floating bubbles, glittering stars, and sweet pentatonic melodies ring out...)_

The speech-to-text model hesitated over the Bengali phonology of _"জিমহা"_ (_Jimha_), matching it to the closest English phrase: **`"Jim Heart"`**.

Across the room, the monitor erupted into starlight. The letter **`J`** was crowned **`👑 Jimha!`**, but honoring the acoustic spark of that prompt, **`H`** was forever inscribed as **`💖 Jim Heart!`**.

Thus, the twin identities were born: **Queen Jimha** (the laughing toddler monarch of her tactile playground) and **Jim Heart** (her cosmic superhero alter ego). Read the full mythological backstory in [**The Official Lorebook (`docs/LORE.md`)**](docs/LORE.md).

---

## 🛡️ The 7 Dad-Mode Invariants

Children do not interact with software like adults. An 18-month-old toddler explores by leaning elbows, slapping ten fingers at once, and tapping every pixel. Jimha is governed by **7 Child-Safety Invariants**:

|   #   | Invariant                        | Threat Vector                            | Technical Safeguard                                                                                                               |
| :---: | :------------------------------- | :--------------------------------------- | :-------------------------------------------------------------------------------------------------------------------------------- |
| **1** | **The Exit Fortress**            | Accidental game closing & forearm slaps  | Compound `Shift + Esc` 2.5s hold + elbow rejection (`pressedKeys.size > 2`). Lone `Escape` triggers playful `🚀 BLAST OFF!` card. |
| **2** | **Pediatric Hearing Protection** | Acoustic summing & speaker pops          | 0.8 safe volume clamp across native and web audio + 4-voice process stealing pool.                                                |
| **3** | **Bubble Lagoon Ceiling**        | Unbounded memory growth & visual noise   | Strict 25-bubble FIFO ceiling with auto-popping of oldest bubbles.                                                                |
| **4** | **Dynamic Cadence Budget**       | Visual sensory overload & GPU spikes     | Rolling 500ms cadence window throttles particle bursts from 28 to 8 when $\ge 4$ keys/500ms.                                      |
| **5** | **20-Second Attract Drift**      | OLED burn-in & unattended screen battery | Inactivity for 20s transitions the canvas into a soft, breathing starlight lullaby.                                               |
| **6** | **Toddler Gesture Gate**         | Trapped in modal dialogs                 | 450ms hold or upward swipe to open Sticker Book; any keypress or backdrop touch escapes.                                          |
| **7** | **100% Pentatonic Consonance**   | Musical dissonance & cacophony           | All keys map to an 11-tone C4–C6 major pentatonic scale; any random smash produces sweet harmony.                                 |

👉 _For full mathematical, acoustic, and behavioral explanations, read [**The 7 Dad-Mode Invariants Guide (`docs/DAD_MODE_INVARIANTS.md`)**](docs/DAD_MODE_INVARIANTS.md)._

---

## 🎮 Interactive Controls & Cheats

### Playful Toddler Exploration

- **`A`–`Z`**: Massive spring-bounced typography with radiant halos and companion emojis (e.g. `A` for 🍎 Apple, `B` for 🦋 Butterfly).
- **`J`**: 👑 **Queen Jimha** royal crown fanfare!
- **`H`**: 💖 **Jim Heart** cosmic alter ego easter egg!
- **`0`–`9`**: Giant numerals accompanied by exact constellations of glittering stars.
- **`Space`**: 🌟 Cosmic supernova explosion with rainbow fireworks!
- **`Enter`**: 🎉 Party celebration with floating balloons and confetti showers!
- **`Backspace`**: 🫧 Bubble pop flurry!
- **`Escape` (Quick Tap)**: 🚀 Blast off rocket companion card!
- **Mouse / Touch Drag**: Spawns floating, translucent soap bubbles that rise and pop on touch.

### Engineering Parent Controls

- **Exit Game**: Hold **`Shift + Escape`** continuously for 2.5 seconds (radial countdown HUD displays progress).
- **Parent Virtual Switcher**: Press **`Up, Up`** rapidly or tap the top-right indicator to open the KWin D-Bus window switcher and seamlessly hand over focus without closing Jimha.
- **Parent Gate**: 450ms long-press or upward swipe opens the **Sticker Book** to inspect unlocked badges.

### Arcade Cheats

- **The Konami Sequence**:
  $$\uparrow \quad \uparrow \quad \downarrow \quad \downarrow \quad \leftarrow \quad \rightarrow \quad \leftarrow \quad \rightarrow \quad \text{B} \quad \text{A}$$
  Unleashes **Rainbow God Mode**: full-screen multi-layer fireworks, continuous celestial chimes, and unlocks the coveted `konami_champion` badge.

---

## 🗺️ The 5 Concurrent Capability Tracks

Jimha is built on non-linear parallel evolution across 5 tracks:

```
┌────────────────────────────────────────────────────────────────────────┐
│ Track A: Sensory Foundations & Toddler Invariants (Active Baseline)    │
│ Track B: Dynamic Progression & Adaptive Growth Tiers (Explorer ➔ 4yr)  │
│ Track C: Polyglot Multiverse & Phonics Engine (English + বাংলা)         │
│ Track D: Multiplatform Fleet & Knot Mesh Swarm (Steam Deck + Tablets)  │
│ Track E: Evergreen SWE, Cleanroom Verification & Packaging (Flatpak)   │
└────────────────────────────────────────────────────────────────────────┘
```

👉 _Explore the complete architectural roadmap in [**Macro Roadmap (`docs/ROADMAP.md`)**](docs/ROADMAP.md)._

---

## 📚 Complete Documentation Suite

| Document                                                     | Purpose                                                                                                                        |
| :----------------------------------------------------------- | :----------------------------------------------------------------------------------------------------------------------------- |
| [**Architecture & Deep-Dive**](docs/ARCHITECTURE.md)         | The Self-Contained Product Invariant, PipeWire audio engine, KWin D-Bus ECMAScript injection, and PixiJS v8 particle pipeline. |
| [**The 7 Dad-Mode Invariants**](docs/DAD_MODE_INVARIANTS.md) | Engineering parent perspective on why 18-month-old software requires specialized safety laws.                                  |
| [**Universe Lorebook**](docs/LORE.md)                        | The Steam Deck voice prompt, Queen Jimha vs Jim Heart, and the 7 Badges of Honor.                                              |
| [**Macro Product Roadmap**](docs/ROADMAP.md)                 | The 5 Concurrent Capability Tracks, Adaptive Growth Tiers, and Polyglot Phonics.                                               |
| [**Packaging & Distribution**](docs/PACKAGING.md)            | Arch Linux `PKGBUILD`, Flatpak `org.purrfect.jimha`, and user-space deployment.                                                |

---

## 🚀 Developer Quickstart & Hermetic Verification

### Prerequisites

- **Node.js**: $\ge 20.x$, **pnpm**: $\ge 9.x$
- **Rust & Cargo**: $\ge 1.78$
- Linux system libraries: `webkit2gtk-4.1`, `gtk3`

### Setup & Run

```bash
# 1. Clone repository
git clone https://github.com/kuasha420/jimha.git
cd jimha

# 2. Install dependencies & build frontend
pnpm install --frozen-lockfile
pnpm build

# 3. Run development web server
pnpm dev

# 4. Run native desktop application (Tauri v2)
pnpm tauri dev
```

### Hermetic Verification & Multi-Tier Quality Gates

In adherence to **PSL-INV-001** and **PSL-INV-002**, Jimha enforces a zero-tolerance multi-tier verification standard with sub-second test benchmarks:

```bash
# 1. Turnkey composite verification gate (svelte-check, eslint, clippy, cargo fmt, vitest, cargo test, vite build)
pnpm verify

# 2. RFC-051 Diff-aware affected testing (sub-second fast-path, <200ms)
pnpm test:diff

# 3. Full Vitest frontend test suite (13 test suites, 78 tests, <1.0s)
pnpm test

# 4. Full Rust native backend test suite (20 tests, <0.03s)
pnpm test:rust
# or: cargo test --manifest-path src-tauri/Cargo.toml

# 5. Multi-tier linting, clippy & formatting
pnpm lint          # ESLint 10 Flat Config (complexity <= 15, max-depth <= 4)
pnpm clippy        # Rust Cargo lints table (-D warnings, unsafe_code = forbid)
pnpm format        # Prettier formatting across entire repository
pnpm format:check  # Assert 100% Prettier compliance

# 6. Evergreen dependency hygiene audit
pnpm audit:deps
```

### Pre-Commit Staged Automation

Jimha configures zero-friction local git hooks powered by `simple-git-hooks` and `lint-staged`:

- Staged TypeScript, Svelte, and JavaScript files automatically run `eslint --fix` and `prettier --write`.
- Staged Rust files automatically run `cargo fmt`.
- Non-code assets (JSON, Markdown, CSS, HTML) automatically run `prettier --write`.

---

## 📦 Packaging & Installation

Jimha can be installed via **Arch Linux PKGBUILD**, **Flatpak**, or local user-space install:

```bash
# Arch Linux / SteamOS Desktop
makepkg -si

# Flatpak
flatpak-builder --user --install --force-clean build-flatpak packaging/flatpak/org.purrfect.jimha.yml
```

👉 _See [**Packaging & Distribution Guide (`docs/PACKAGING.md`)**](docs/PACKAGING.md) for full instructions._

---

## 📄 License & Dedication

Released under the [MIT License](LICENSE).  
Dedicated with unconditional love to **Jimha** (Queen Jimha & Jim Heart) 💖👑
