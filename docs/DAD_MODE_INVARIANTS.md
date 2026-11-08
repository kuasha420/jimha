# The 7 Dad-Mode Invariants

<!-- SPDX-License-Identifier: MIT -->
<!-- Copyright (c) 2026 Arafat Zahan (@kuasha420) -->

> _"When writing software for adults, an unexpected key combination produces an error dialog. When writing software for an eighteen-month-old toddler, an unexpected key combination is an entire elbow flattening twenty-four keys simultaneously while singing."_

Most software design assumes an adult user: deliberate keypresses, intentional mouse tracking, and respect for modal dialogs. Toddler interaction is fundamentally different. It is energetic, tactile, rapid, chaotic, and joyous.

To build an application that an engineering parent can safely launch on their workstation without anxiety, Jimha is governed by **The 7 Dad-Mode Invariants**. These are not mere aesthetic preferences; they are formal engineering constraints verified across hundreds of hours of real-world toddler play.

---

## The Invariants Matrix

|   #   | Invariant                        | Threat Vector                               | Technical Implementation                                                                                                 |
| :---: | :------------------------------- | :------------------------------------------ | :----------------------------------------------------------------------------------------------------------------------- |
| **1** | **The Exit Fortress**            | Accidental termination & accidental escapes | Compound `Shift + Esc` 2.5s hold + elbow rejection (`pressedKeys.size > 2`). Lone `Escape` triggers playful rocket card. |
| **2** | **Pediatric Hearing Protection** | Destructive acoustic summing & ear fatigue  | 0.8 hard master gain clamp + max 4-voice stealing process pool.                                                          |
| **3** | **Bubble Lagoon Ceiling**        | Unbounded memory growth & visual noise      | Strict 25-bubble FIFO ceiling with auto-popping oldest bubble.                                                           |
| **4** | **Dynamic Sensory Cadence**      | Visual overstimulation & GPU lag spikes     | Rolling 500ms cadence window: burst throttles from 28 to 8 particles when $\ge 4$ keys/500ms.                            |
| **5** | **20-Second Attract Drift**      | Unattended screen burn-in & sensory fatigue | Idle timer transitions into breathing starlight drift after 20s of inactivity.                                           |
| **6** | **Toddler Gesture Gate**         | Accidental UI modal traps & stuck screens   | 450ms hold or deliberate upward swipe to open Sticker Book; any keypress or touch dismisses.                             |
| **7** | **100% Pentatonic Consonance**   | Atonal dissonance & musical cacophony       | Strict C4–C6 pentatonic tuning (11 frequencies); every combination forms sweet harmony.                                  |

---

## 1. Invariant 1: The Exit Fortress

### The Problem

Children love the `Escape` key. It sits isolated on the top-left corner of the keyboard, tempting little fingers. In traditional games or desktop applications, pressing `Escape` exits fullscreen or closes the process. When an 18-month-old accidentally terminates their favorite game, tears follow immediately.

Conversely, a child leaning their forearm or elbow against the keyboard frequently depresses twenty keys at once, potentially triggering standard hotkeys like `Alt + F4`, `Ctrl + Q`, or `Super + D`.

### The Engineering Solution

1. **Elbow & Forearm Rejection**:
   ```typescript
   // Check active keys in InputMultiplexer
   if (pressedKeys.size > 2) {
     // An elbow or palm is resting on the keyboard. Reject exit hold increment!
     abortExitHold();
   }
   ```
   If more than 2 keys are simultaneously depressed, the exit hold is aborted immediately. Forearms cannot trigger application shutdown.
2. **Compound 2.5-Second Hold**:
   To exit Jimha, a parent must hold **both `Shift` and `Escape`** continuously for 2.5 seconds. A radial countdown HUD animates across the center of the display. Releasing either key even 100 milliseconds early resets the progress to zero.
3. **Lone Escape as Companion Card**:
   Pressing `Escape` alone is deliberately treated as regular playful input. It spawns the **`🚀 BLAST OFF!`** companion card with cosmic chime harmonics and a rocket starburst. Children can tap `Escape` a hundred times without ever closing the window.

---

## 2. Invariant 2: Pediatric Hearing Protection

### The Problem

When a toddler discovers the keyboard, they do not play a Chopin nocturne. They slap both palms onto the keyboard five times a second. In naive Web Audio or native synthesizer setups, twenty polyphonic voices trigger simultaneously. In phase alignment, twenty audio streams constructively sum their amplitudes:
$$\text{Peak Amplitude} = \sum_{k=1}^{N} A_k \gg 1.0$$
This results in digital clipping, speaker distortion, and dangerously loud acoustic bursts that can frighten or damage young developing ears.

### The Engineering Solution

1. **0.8 Safe Volume Clamp**:
   Both the Linux PipeWire backend (`pw-play --volume=0.8`) and the Web Audio fallback clamp master gain to `0.80` maximum. Even at maximum system volume, sound levels remain gentle.
2. **Hard 4-Voice Stealing Pool**:
   The native audio engine maintains an internal pool bounded to **at most 4 concurrent processes**:
   ```rust
   // src-tauri/src/audio.rs
   if let Ok(mut pool) = self.proc_pool.lock() {
       pool.retain_mut(|p| p.try_wait().map(|s| s.is_none()).unwrap_or(false));
       while pool.len() >= 4 {
           if let Some(mut oldest) = pool.drain(..1).next() {
               let _ = oldest.kill(); // Terminate oldest voice cleanly
           }
       }
   }
   ```
   Rapid key smashing steals the oldest voice rather than adding a fifth voice. The acoustic energy remains bounded, warm, and melodious.
3. **Dynamic BGM Smoothing & Treble Lead Muting**:
   During active toddler typing (`elapsed < 3.0s`), the ambient BGM engine completely mutes high treble lead notes (`0.0`), preventing frequency clashing with interactive key chimes. A warm pedal bass note hums softly at `0.02`. Once key interaction ceases, the melody returns via a smooth parabolic quadratic ramp ($0.06 \times \text{progress}^2$) between 3.0s and 6.0s.
4. **Acoustic Low-Pass Muffling**:
   During active gameplay (`mode === 'playing'`), the ambient audio filter cutoff drops to **650 Hz** for a warm, muffled acoustic drone. In idle attract mode, it opens to **3000 Hz**, and in UI modal mode, it settles at **750 Hz**.
5. **Polyphonic Chord Volume Normalization**:
   When multi-tone chords sound on Space or Enter, per-voice gain is mathematically normalized by $1/\sqrt{N}$ ($V_{\text{per-voice}} = V_{\text{clamped}} / \sqrt{N}$), ensuring a 3-note major chord never overpowers single notes or distorts speakers.

---

## 3. Invariant 3: Bubble Lagoon Ceiling

### The Problem

Toddlers love dragging their fingers across touchscreens and clicking trackpads to generate floating bubbles. If a child vigorously rubs their palms across a multi-touch screen, an unconstrained particle engine can allocate hundreds of bubble objects in seconds. This leads to frame drops, garbage collection pauses, and visual confusion.

### The Engineering Solution

1. **The 25-Bubble Maximum**:
   The bubble lagoon enforces an immutable ceiling of **25 active bubbles**.
2. **Smooth FIFO Popping**:
   When bubble #26 is generated, the engine does not silently reject the new touch. Instead, it extracts the oldest bubble in the FIFO queue, immediately triggers its popping animation (a soft chime + radial soap-mist particle burst), and replaces it with the newly spawned bubble.
3. **Gentle Natural Drift**:
   Bubbles float upward with slight horizontal sinewave wobble ($x(t) = A \sin(\omega t + \phi)$) and pop automatically when drifting off the top of the viewport.

---

## 4. Invariant 4: Dynamic Sensory Cadence Budgeting

### The Problem

Sensory overload is a real risk for toddlers. Continuous high-density particle explosions, flashing neon bursts, and rapid visual shifts cause agitation rather than joyful focus. Furthermore, emitting 100 particles for each of 20 rapid keystrokes will overwhelm low-power mobile or handheld GPUs (such as the Steam Deck on battery).

### The Engineering Solution

Jimha implements dynamic cadence window throttling:

- **Rolling Window**: Tracks keypress timestamps over a sliding 500ms window.
- **Normal Cadence** ($< 4$ keys in 500ms):
  - Emits 28 high-velocity rainbow particles with gravity and sparkling trails.
- **High-Velocity Smashing Cadence** ($\ge 4$ keys in 500ms):
  - Throttles emission down to 8 compact glowing sparks.
  - Dampens screen shake to zero.
  - Concentrates color saturation to soothing pastels.

As soon as the toddler pauses or slows down, normal full bursts resume seamlessly.

---

## 5. Invariant 5: 20-Second Attract Drift

### The Problem

Toddlers have fluid attention spans. One moment they are deeply engaged at the keyboard; the next moment they have sprinted across the room to inspect a toy block. Traditional games remain frozen on high-intensity screens, wasting battery, causing display burn-in on OLED screens, and blasting sound when nudged.

### The Engineering Solution

1. **Attract Drift Timer**:
   An inactivity timer monitors pointer, touch, and keyboard interactions. If no input occurs for **20 seconds**, Jimha glides into **Attract Drift Mode**:
   - The central character smoothly scales down and dissolves.
   - The ambient starfield dims by 40% and enters a slow celestial orbit.
   - Floating bubbles continue their gentle buoyant drift with softened lighting.
   - Generative background music enters `idle` mode: soft starlit music box tones at `0.15` volume.
2. **Instant Re-engagement**:
   The instant any key is pressed or the screen is touched, the attract mode instantly dissolves without lag, popping into a brand-new vibrant companion card.

---

## 6. Invariant 6: Toddler Gesture Gate & Universal Modal Escape

### The Problem

Children love tapping everything they see. If an interface contains buttons that open modals (like a settings screen or sticker catalog), toddlers will tap them within three seconds. Once inside a modal, children cannot read the "X" button or the "Close" dialog. They get stuck, feel frustrated, and cry.

### The Engineering Solution

1. **Deliberate Gesture Gate**:
   Opening the **Sticker Book** (which houses 10 collectible achievement badges across sensory, secret, and musical categories) requires either:
   - A sustained **450-millisecond press-and-hold** on the sticker book icon, or
   - A deliberate **upward swipe gesture** of $\ge 80$ pixels from the bottom edge.
     Accidental brief taps simply produce a playful wiggle animation without opening the sheet.
2. **Universal Modal Escape**:
   Once any modal is open, **any normal interaction escapes back to play**:
   - Smashing _any_ key on the keyboard immediately closes the modal and spawns that key.
   - Tapping anywhere on the blurred background backdrop dismisses the modal.
   - Pressing the gamepad B button or Escape dismisses the modal.

There are zero dead-ends. A toddler can never get stuck in a menu.

---

## 7. Invariant 7: 100% Pentatonic Consonance

### The Problem

Standard keyboards map 26 letters and 10 numbers. If mapped to a traditional chromatic or diatonic scale (C Major or D Minor), random key smashes will inevitably play minor second intervals (like C and C#) or tritones (like C and F#). These dissonant clusters sound harsh, stressful, and chaotic to an infant ear.

### The Engineering Solution

Every key in Jimha is mathematically bound to an **11-tone Pentatonic Scale** across two octaves (C4 to C6):

```
C4 (261.63 Hz) ── D4 (293.66 Hz) ── E4 (329.63 Hz) ── G4 (392.00 Hz) ── A4 (440.00 Hz)
C5 (523.25 Hz) ── D5 (587.33 Hz) ── E5 (659.25 Hz) ── G5 (783.99 Hz) ── A5 (880.00 Hz)
C6 (1046.50 Hz)
```

### Why Pentatonic?

In music theory, the major pentatonic scale contains **zero semitone intervals (minor seconds)** and **zero tritones**. No matter which keys are pressed together—whether three letters, five numbers, or an entire palm—the resulting chord is acoustically consonant.

Key drumming sounds like a celestial wind chime or an enchanted gamelan, creating an auditory environment that parents find relaxing rather than grating.
