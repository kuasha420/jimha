# Packaging & Distribution Guide for Jimha

<!-- SPDX-License-Identifier: MIT -->
<!-- Copyright (c) 2026 Arafat Zahan (@kuasha420) -->

This guide covers building, testing, packaging, and installing **Jimha** across desktop Linux, SteamOS, and containerized distribution formats.

```
┌────────────────────────────────────────────────────────────────────────┐
│                   DISTRIBUTION PACKAGING TARGETS                       │
├────────────────────────────────────────────────────────────────────────┤
│ 1. Arch Linux / SteamOS ── Native PKGBUILD (makepkg -si)               │
│ 2. Universal Linux     ── Sandboxed Flatpak (flatpak-builder)          │
│ 3. Sovereign Desktop   ── Local User Tree (~/.local/bin)               │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 1. System Build Prerequisites

Building Jimha natively from source requires the following toolchain dependencies:

### Core Runtimes & Compilers

- **Node.js**: $\ge 20.x$
- **pnpm**: $\ge 9.x$ (`corepack enable pnpm` or `npm install -g pnpm`)
- **Rust & Cargo**: $\ge 1.78$ (`rustup default stable`)

### Native System Libraries (Debian / Ubuntu / Fedora / Arch)

| Distribution               | Install Command                                                                                                                |
| :------------------------- | :----------------------------------------------------------------------------------------------------------------------------- |
| **Arch Linux / SteamOS**   | `sudo pacman -S --needed base-devel webkit2gtk-4.1 gtk3 pnpm rust nodejs`                                                      |
| **Debian / Ubuntu 22.04+** | `sudo apt-get install -y libgtk-3-dev libwebkit2gtk-4.1-dev libsoup-3.0-dev libjavascriptcoregtk-4.1-dev build-essential curl` |
| **Fedora 39+**             | `sudo dnf install -y gtk3-devel webkit2gtk4.1-devel libsoup3-devel javascriptcoregtk4.1-devel`                                 |

---

## 2. Target A: Arch Linux & SteamOS Native Package (`PKGBUILD`)

Jimha includes an official production-grade `PKGBUILD` in the repository root for Arch Linux, Manjaro, EndeavourOS, and the Steam Deck (SteamOS Desktop Mode).

### Local Build & Installation

To build and install the package locally:

```bash
# 1. Clone repository
git clone https://github.com/kuasha420/jimha.git
cd jimha

# 2. Compile and install package with dependency resolution
makepkg -si
```

### What `PKGBUILD` Installs:

- Binary: `/usr/bin/jimha`
- Desktop Launcher: `/usr/share/applications/org.purrfect.jimha.desktop`
- AppStream Metadata: `/usr/share/metainfo/org.purrfect.jimha.metainfo.xml`
- Vector & Raster Icons:
  - `/usr/share/icons/hicolor/scalable/apps/org.purrfect.jimha.svg`
  - `/usr/share/icons/hicolor/512x512/apps/org.purrfect.jimha.png`
  - `/usr/share/icons/hicolor/128x128/apps/org.purrfect.jimha.png`
  - `/usr/share/icons/hicolor/32x32/apps/org.purrfect.jimha.png`
- License: `/usr/share/licenses/jimha/LICENSE`

### Updating or Uninstalling

```bash
# Remove native package
sudo pacman -R jimha
```

---

## 3. Target B: Universal Sandboxed Flatpak (`org.purrfect.jimha`)

Flatpak provides an isolated, immutable runtime that runs identically across every Linux distribution (Fedora Silverblue, Ubuntu, openSUSE, Debian, Arch).

The Flatpak manifest is maintained under [`packaging/flatpak/org.purrfect.jimha.yml`](../packaging/flatpak/org.purrfect.jimha.yml).

### Flatpak Manifest Specification

```yaml
app-id: org.purrfect.jimha
runtime: org.gnome.Platform
runtime-version: '47'
sdk: org.gnome.Sdk
sdk-extensions:
  - org.freedesktop.Sdk.Extension.rust-stable
  - org.freedesktop.Sdk.Extension.node20
command: jimha

finish-args:
  # Wayland & X11 display server access
  - --socket=wayland
  - --socket=fallback-x11
  # Hardware accelerated graphics
  - --device=all
  # Low-latency PipeWire / PulseAudio access
  - --socket=pulseaudio
  # Inter-process communication
  - --share=ipc
  # KWin kiosk shortcut inhibition and window handover via D-Bus
  - --talk-name=org.kde.KWin
  - --talk-name=org.freedesktop.ScreenSaver
```

### Building the Flatpak Locally

1. **Install Flatpak and Builder**:

   ```bash
   sudo pacman -S flatpak flatpak-builder  # Arch
   sudo apt install flatpak flatpak-builder # Ubuntu/Debian
   ```

2. **Install GNOME 47 Runtime and Extensions**:

   ```bash
   flatpak install flathub \
     org.gnome.Platform//47 \
     org.gnome.Sdk//47 \
     org.freedesktop.Sdk.Extension.rust-stable//24.08 \
     org.freedesktop.Sdk.Extension.node20//24.08
   ```

3. **Compile and Install into User Repository**:

   ```bash
   # From repository root
   flatpak-builder --user --install --force-clean build-flatpak packaging/flatpak/org.purrfect.jimha.yml
   ```

4. **Run the Flatpak**:
   ```bash
   flatpak run org.purrfect.jimha
   ```

---

## 4. Target C: Direct Sovereign User-Space Install (`~/.local/bin`)

For developers or air-gapped workstations without root (`sudo`) access, Jimha can be built and installed completely into the user's home directory.

### Build and Copy Script

```bash
# 1. Build frontend assets
pnpm install --frozen-lockfile
pnpm build

# 2. Build native release binary
cargo build --manifest-path src-tauri/Cargo.toml --release

# 3. Create XDG directory hierarchy
mkdir -p ~/.local/bin
mkdir -p ~/.local/share/applications
mkdir -p ~/.local/share/metainfo
mkdir -p ~/.local/share/icons/hicolor/scalable/apps
mkdir -p ~/.local/share/icons/hicolor/512x512/apps

# 4. Copy binary
install -m755 src-tauri/target/release/jimha ~/.local/bin/jimha

# 5. Install desktop launcher and icons
install -m644 org.purrfect.jimha.desktop ~/.local/share/applications/org.purrfect.jimha.desktop
install -m644 org.purrfect.jimha.metainfo.xml ~/.local/share/metainfo/org.purrfect.jimha.metainfo.xml
install -m644 assets/jimha.svg ~/.local/share/icons/hicolor/scalable/apps/org.purrfect.jimha.svg
install -m644 assets/jimha.png ~/.local/share/icons/hicolor/512x512/apps/org.purrfect.jimha.png

# 6. Update desktop application database
update-desktop-database ~/.local/share/applications
gtk-update-icon-cache -f -t ~/.local/share/icons/hicolor
```

Once installed, Jimha appears in the desktop application menu (GNOME Shell, KDE Plasma Kickoff, SteamOS desktop).

---

## 5. Adding Jimha to Steam Deck Gaming Mode

To add Jimha as a handheld non-Steam game on the Steam Deck:

1. Switch to **Desktop Mode** on the Steam Deck (`Power` $\rightarrow$ `Switch to Desktop`).
2. Open the Steam client on the desktop.
3. Click **Games** in the top menu $\rightarrow$ **Add a Non-Steam Game to My Library...**
4. Check **Jimha** from the application list and click **Add Selected Programs**.
5. _(Optional)_ Right-click Jimha in your Steam Library $\rightarrow$ **Properties**:
   - In **Launch Options**, set:
     ```
     MESA_VK_WSI_PRESENT_MODE=immediate %command%
     ```
6. Return to **Gaming Mode**. Jimha will now launch in native fullscreen with gamepad controls and gyro support enabled.

---

## 6. Multi-Target Release Packaging & CI/CD Automation

Jimha includes automated multi-target packaging and continuous verification via GitHub Actions and local release tooling.

### Idempotent Local & CI Packager (`scripts/package_release.sh`)

The release packager builds sovereign distribution bundles into `release_artifacts/`:

```bash
# Package release using active git short-sha or custom build id
bash scripts/package_release.sh [BUILD_ID]
```

#### Generated Artifacts:

1. **Steam Deck Sovereign User-Space Bundle**:
   - `release_artifacts/jimha-v<version>-steamdeck-linux-x86_64.tar.gz`
   - Stripped executable binary + standalone `install.sh` and `uninstall.sh`.
   - Immutable root safe: installs to `~/.local/bin` and `~/.local/share` without `sudo`.
   - Includes `README-STEAMDECK.md` with 3-step Steam Gaming Mode setup and launch options.
2. **Arch Linux Native Package**:
   - `release_artifacts/jimha-<arch_pkgver>-1-x86_64.pkg.tar.zst`
   - Built via local `makepkg` (or containerized `archlinux:base-devel` when running on non-Arch hosts).
3. **Cryptographic Checksums**:
   - `release_artifacts/SHA256SUMS.txt` computed deterministically across all output artifacts.

### GitHub Actions Workflows

- **`.github/workflows/ci.yml`**:
  - Triggers on `push` and `pull_request` targeting `main`.
  - Runs full verification gate: `pnpm verify` (Svelte diagnostics, ESLint 10, Cargo Clippy `-D warnings`, Cargo formatting check, 86 Vitest unit tests, 22 Cargo backend tests, and Vite production bundle).
- **`.github/workflows/release.yml`**:
  - Triggers automatically on tag push (`v*`).
  - Runs CI verification gate.
  - Generates `.deb` and `.AppImage` via `pnpm tauri build`.
  - Executes `scripts/package_release.sh` to package Steam Deck bundle, Arch package, and `SHA256SUMS.txt`.
  - Distributes release assets and release notes to GitHub Releases via `softprops/action-gh-release@v2` (flagging pre-releases if tag contains hyphens).

---

## 7. Packaging Verification Checklist

Prior to publishing any release archive or package build, verify:

- [ ] `pnpm test` passes 100% of unit tests with sub-second execution.
- [ ] `cargo test --manifest-path src-tauri/Cargo.toml` passes 100% of backend tests.
- [ ] `org.purrfect.jimha.desktop` passes validation: `desktop-file-validate org.purrfect.jimha.desktop`.
- [ ] `org.purrfect.jimha.metainfo.xml` passes validation: `appstreamcli validate org.purrfect.jimha.metainfo.xml`.
- [ ] Cold boot time into full interactive canvas is under 350ms.
