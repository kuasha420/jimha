#!/usr/bin/env bash
# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Arafat Zahan (@kuasha420)
#
# scripts/package_release.sh - Deterministic Multi-Target Release Packager
# Produces:
#  1. jimha-v${VERSION}-steamdeck-linux-x86_64.tar.gz
#  2. jimha-${ARCH_PKGVER}-1-x86_64.pkg.tar.zst (if makepkg or docker available)
#  3. SHA256SUMS.txt

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"

BUILD_ID="${1:-${BUILD_ID:-$(git rev-parse --short HEAD 2>/dev/null || echo "release")}}"
VERSION="${VERSION:-2.0.0-${BUILD_ID}}"
ARCH_PKGVER="$(echo "${VERSION}" | tr '-' '.')"

RELEASE_DIR="${ROOT_DIR}/release_artifacts"
STAGING_DIR="${RELEASE_DIR}/.staging-steamdeck"

echo "=== Packaging Jimha Release: v${VERSION} (Arch: ${ARCH_PKGVER}) ==="

mkdir -p "${RELEASE_DIR}"
rm -rf "${STAGING_DIR}"
mkdir -p "${STAGING_DIR}"

# 1. Locate and strip binary
BIN_SRC=""
if [ -f "${ROOT_DIR}/target/release/jimha" ]; then
    BIN_SRC="${ROOT_DIR}/target/release/jimha"
elif [ -f "${ROOT_DIR}/src-tauri/target/release/jimha" ]; then
    BIN_SRC="${ROOT_DIR}/src-tauri/target/release/jimha"
else
    echo "Release binary not found! Building release binary now..."
    (cd "${ROOT_DIR}" && pnpm build && cargo build --manifest-path src-tauri/Cargo.toml --release)
    if [ -f "${ROOT_DIR}/target/release/jimha" ]; then
        BIN_SRC="${ROOT_DIR}/target/release/jimha"
    else
        BIN_SRC="${ROOT_DIR}/src-tauri/target/release/jimha"
    fi
fi

echo "Using binary: ${BIN_SRC}"

# Copy binary to staging and strip
cp "${BIN_SRC}" "${STAGING_DIR}/jimha"
if command -v strip >/dev/null 2>&1; then
    strip --strip-unneeded "${STAGING_DIR}/jimha" 2>/dev/null || strip "${STAGING_DIR}/jimha" 2>/dev/null || true
fi
chmod 755 "${STAGING_DIR}/jimha"

# Copy metadata and assets
cp "${ROOT_DIR}/org.purrfect.jimha.desktop" "${STAGING_DIR}/"
cp "${ROOT_DIR}/org.purrfect.jimha.metainfo.xml" "${STAGING_DIR}/"
cp "${ROOT_DIR}/LICENSE" "${STAGING_DIR}/"

mkdir -p "${STAGING_DIR}/assets"
cp "${ROOT_DIR}/assets/jimha.svg" "${STAGING_DIR}/assets/"
cp "${ROOT_DIR}/assets/jimha.png" "${STAGING_DIR}/assets/"

mkdir -p "${STAGING_DIR}/src-tauri/icons"
cp "${ROOT_DIR}/src-tauri/icons/128x128.png" "${STAGING_DIR}/src-tauri/icons/"
cp "${ROOT_DIR}/src-tauri/icons/32x32.png" "${STAGING_DIR}/src-tauri/icons/"

# Create install.sh
cat << 'EOF' > "${STAGING_DIR}/install.sh"
#!/usr/bin/env bash
# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Arafat Zahan (@kuasha420)
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
echo "=== Installing Jimha to Sovereign User-Space (~/.local) ==="

BIN_DIR="${HOME}/.local/bin"
APP_DIR="${HOME}/.local/share/applications"
META_DIR="${HOME}/.local/share/metainfo"
ICON_DIR="${HOME}/.local/share/icons/hicolor"

mkdir -p "${BIN_DIR}" "${APP_DIR}" "${META_DIR}"
mkdir -p "${ICON_DIR}/scalable/apps" "${ICON_DIR}/512x512/apps"
mkdir -p "${ICON_DIR}/128x128/apps" "${ICON_DIR}/32x32/apps"

install -m755 "${SCRIPT_DIR}/jimha" "${BIN_DIR}/jimha"
install -m644 "${SCRIPT_DIR}/org.purrfect.jimha.desktop" "${APP_DIR}/org.purrfect.jimha.desktop"
install -m644 "${SCRIPT_DIR}/org.purrfect.jimha.metainfo.xml" "${META_DIR}/org.purrfect.jimha.metainfo.xml"

if [ -f "${SCRIPT_DIR}/assets/jimha.svg" ]; then
    install -m644 "${SCRIPT_DIR}/assets/jimha.svg" "${ICON_DIR}/scalable/apps/org.purrfect.jimha.svg"
fi
if [ -f "${SCRIPT_DIR}/assets/jimha.png" ]; then
    install -m644 "${SCRIPT_DIR}/assets/jimha.png" "${ICON_DIR}/512x512/apps/org.purrfect.jimha.png"
fi
if [ -f "${SCRIPT_DIR}/src-tauri/icons/128x128.png" ]; then
    install -m644 "${SCRIPT_DIR}/src-tauri/icons/128x128.png" "${ICON_DIR}/128x128/apps/org.purrfect.jimha.png"
fi
if [ -f "${SCRIPT_DIR}/src-tauri/icons/32x32.png" ]; then
    install -m644 "${SCRIPT_DIR}/src-tauri/icons/32x32.png" "${ICON_DIR}/32x32/apps/org.purrfect.jimha.png"
fi

if command -v update-desktop-database >/dev/null 2>&1; then
    update-desktop-database "${APP_DIR}" 2>/dev/null || true
fi
if command -v gtk-update-icon-cache >/dev/null 2>&1; then
    gtk-update-icon-cache -f -t "${ICON_DIR}" 2>/dev/null || true
fi

echo "Jimha installed successfully to ${BIN_DIR}/jimha"
echo "See README-STEAMDECK.md for 3-step setup to add Jimha to Steam Gaming Mode."
EOF
chmod +x "${STAGING_DIR}/install.sh"

# Create uninstall.sh
cat << 'EOF' > "${STAGING_DIR}/uninstall.sh"
#!/usr/bin/env bash
# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Arafat Zahan (@kuasha420)
set -euo pipefail

echo "=== Uninstalling Jimha from Sovereign User-Space (~/.local) ==="

rm -f "${HOME}/.local/bin/jimha"
rm -f "${HOME}/.local/share/applications/org.purrfect.jimha.desktop"
rm -f "${HOME}/.local/share/metainfo/org.purrfect.jimha.metainfo.xml"
rm -f "${HOME}/.local/share/icons/hicolor/scalable/apps/org.purrfect.jimha.svg"
rm -f "${HOME}/.local/share/icons/hicolor/512x512/apps/org.purrfect.jimha.png"
rm -f "${HOME}/.local/share/icons/hicolor/128x128/apps/org.purrfect.jimha.png"
rm -f "${HOME}/.local/share/icons/hicolor/32x32/apps/org.purrfect.jimha.png"

if command -v update-desktop-database >/dev/null 2>&1; then
    update-desktop-database "${HOME}/.local/share/applications" 2>/dev/null || true
fi
if command -v gtk-update-icon-cache >/dev/null 2>&1; then
    gtk-update-icon-cache -f -t "${HOME}/.local/share/icons/hicolor" 2>/dev/null || true
fi

echo "Jimha uninstalled cleanly."
EOF
chmod +x "${STAGING_DIR}/uninstall.sh"

# Create README-STEAMDECK.md
cat << 'EOF' > "${STAGING_DIR}/README-STEAMDECK.md"
# Jimha on Steam Deck: Quick Start Guide

Jimha is a toddler-safe fullscreen sensory playground. On SteamOS (Steam Deck), it runs directly in user-space without modifying the immutable root filesystem.

## 3-Step Setup for Steam Gaming Mode

### Step 1: Install to User-Space
Open terminal or Konsole in Desktop Mode, navigate to the extracted folder, and run:
```bash
./install.sh
```
This installs the `jimha` binary into `~/.local/bin/jimha` and registers the desktop launcher and icons.

### Step 2: Add to Steam Desktop Client
1. Open the **Steam** desktop client in Desktop Mode.
2. Click **Games** (in top bar) -> **Add a Non-Steam Game to My Library...**
3. Select **Jimha** from the list (or browse to `~/.local/bin/jimha`).
4. Click **Add Selected Programs**.

### Step 3: Recommended Launch Options
1. In your Steam Library, right-click **Jimha** -> **Properties**.
2. Under **General** -> **Launch Options**, set:
   ```bash
   MESA_VK_WSI_PRESENT_MODE=immediate %command%
   ```
   *(Ensures low-latency 90Hz/120Hz frame pacing on Steam Deck LCD & OLED)*
3. Return to **Gaming Mode** (`Return to Gaming Mode` icon on desktop).

## Toddler Sensory Controls
- **Touch / Multi-Touch**: Tap, drum, or slap the screen to pop bubbles and trigger particle cascades.
- **D-Pad & Face Buttons**: Harmonious pentatonic chimes with velocity springs.
- **Bumpers & Triggers**: Spawn directional bubble jets.
- **Adult Exit Gate**: Hold **Escape** (or mapped Steam exit button) continuously for 3.0 seconds to reveal the exit ring and close Jimha. Toddler key smashes cannot close the game.

## Clean Removal
To completely remove Jimha from user-space, run:
```bash
./uninstall.sh
```
EOF

# Package tar.gz
TARBALL_NAME="jimha-v${VERSION}-steamdeck-linux-x86_64.tar.gz"
echo "Creating Steam Deck bundle: ${RELEASE_DIR}/${TARBALL_NAME}..."
tar -czf "${RELEASE_DIR}/${TARBALL_NAME}" -C "${STAGING_DIR}" .
rm -rf "${STAGING_DIR}"

# 2. Arch Linux package
if command -v makepkg >/dev/null 2>&1; then
    echo "Building Arch Linux package with makepkg..."
    ARCH_TMP=$(mktemp -d)
    cat << EOF > "${ARCH_TMP}/PKGBUILD"
pkgname=jimha
pkgver=${ARCH_PKGVER}
pkgrel=1
pkgdesc="A toddler-safe fullscreen interactive sensory key smash wonderland for Jimha"
arch=('x86_64')
url="https://github.com/kuasha420/jimha"
license=('MIT')
depends=('gtk3' 'webkit2gtk-4.1' 'hicolor-icon-theme')

package() {
  install -Dm755 "${BIN_SRC}" "\$pkgdir/usr/bin/jimha"
  install -Dm644 "${ROOT_DIR}/org.purrfect.jimha.desktop" "\$pkgdir/usr/share/applications/org.purrfect.jimha.desktop"
  install -Dm644 "${ROOT_DIR}/org.purrfect.jimha.metainfo.xml" "\$pkgdir/usr/share/metainfo/org.purrfect.jimha.metainfo.xml"
  install -Dm644 "${ROOT_DIR}/assets/jimha.svg" "\$pkgdir/usr/share/icons/hicolor/scalable/apps/org.purrfect.jimha.svg"
  install -Dm644 "${ROOT_DIR}/assets/jimha.png" "\$pkgdir/usr/share/icons/hicolor/512x512/apps/org.purrfect.jimha.png"
  install -Dm644 "${ROOT_DIR}/src-tauri/icons/128x128.png" "\$pkgdir/usr/share/icons/hicolor/128x128/apps/org.purrfect.jimha.png"
  install -Dm644 "${ROOT_DIR}/src-tauri/icons/32x32.png" "\$pkgdir/usr/share/icons/hicolor/32x32/apps/org.purrfect.jimha.png"
  install -Dm644 "${ROOT_DIR}/LICENSE" "\$pkgdir/usr/share/licenses/jimha/LICENSE"
}
EOF
    (cd "${ARCH_TMP}" && makepkg --nodeps --cleanbuild -f >/dev/null 2>&1)
    cp "${ARCH_TMP}"/*.pkg.tar.zst "${RELEASE_DIR}/"
    rm -rf "${ARCH_TMP}"
    echo "Arch Linux package created in ${RELEASE_DIR}/"
elif command -v docker >/dev/null 2>&1; then
    echo "makepkg not found on host. Attempting Arch Linux packaging via Docker..."
    docker run --rm -v "${ROOT_DIR}:/work" -w /work archlinux:base-devel bash -c "
        useradd -m builder && \
        su builder -c '
            cd /tmp && \
            cat << \"EOF\" > PKGBUILD
pkgname=jimha
pkgver=${ARCH_PKGVER}
pkgrel=1
pkgdesc=\"A toddler-safe fullscreen interactive sensory key smash wonderland for Jimha\"
arch=(\"x86_64\")
url=\"https://github.com/kuasha420/jimha\"
license=(\"MIT\")
depends=(\"gtk3\" \"webkit2gtk-4.1\" \"hicolor-icon-theme\")
package() {
  install -Dm755 \"/work/target/release/jimha\" \"\\\$pkgdir/usr/bin/jimha\"
  install -Dm644 \"/work/org.purrfect.jimha.desktop\" \"\\\$pkgdir/usr/share/applications/org.purrfect.jimha.desktop\"
  install -Dm644 \"/work/org.purrfect.jimha.metainfo.xml\" \"\\\$pkgdir/usr/share/metainfo/org.purrfect.jimha.metainfo.xml\"
  install -Dm644 \"/work/assets/jimha.svg\" \"\\\$pkgdir/usr/share/icons/hicolor/scalable/apps/org.purrfect.jimha.svg\"
  install -Dm644 \"/work/assets/jimha.png\" \"\\\$pkgdir/usr/share/icons/hicolor/512x512/apps/org.purrfect.jimha.png\"
  install -Dm644 \"/work/src-tauri/icons/128x128.png\" \"\\\$pkgdir/usr/share/icons/hicolor/128x128/apps/org.purrfect.jimha.png\"
  install -Dm644 \"/work/src-tauri/icons/32x32.png\" \"\\\$pkgdir/usr/share/icons/hicolor/32x32/apps/org.purrfect.jimha.png\"
  install -Dm644 \"/work/LICENSE\" \"\\\$pkgdir/usr/share/licenses/jimha/LICENSE\"
}
EOF
            makepkg --nodeps --cleanbuild -f && \
            cp *.pkg.tar.zst /work/release_artifacts/
        '
    " || echo "Warning: Arch packaging container build failed. Skipping Arch package."
else
    echo "Notice: Neither makepkg nor docker found. Skipping Arch Linux .pkg.tar.zst packaging."
fi

# 3. Collect Debian and AppImage bundles if available
if compgen -G "${ROOT_DIR}/target/release/bundle/deb/*.deb" >/dev/null 2>&1; then
    echo "Collecting Debian bundle..."
    cp "${ROOT_DIR}"/target/release/bundle/deb/*.deb "${RELEASE_DIR}/"
elif compgen -G "${ROOT_DIR}/src-tauri/target/release/bundle/deb/*.deb" >/dev/null 2>&1; then
    echo "Collecting Debian bundle..."
    cp "${ROOT_DIR}"/src-tauri/target/release/bundle/deb/*.deb "${RELEASE_DIR}/"
fi

if compgen -G "${ROOT_DIR}/target/release/bundle/appimage/*.AppImage" >/dev/null 2>&1; then
    echo "Collecting AppImage bundle..."
    cp "${ROOT_DIR}"/target/release/bundle/appimage/*.AppImage "${RELEASE_DIR}/"
elif compgen -G "${ROOT_DIR}/src-tauri/target/release/bundle/appimage/*.AppImage" >/dev/null 2>&1; then
    echo "Collecting AppImage bundle..."
    cp "${ROOT_DIR}"/src-tauri/target/release/bundle/appimage/*.AppImage "${RELEASE_DIR}/"
fi

# 4. Generate SHA256SUMS.txt
echo "Generating SHA256SUMS.txt in ${RELEASE_DIR}..."
(
    cd "${RELEASE_DIR}"
    rm -f SHA256SUMS.txt
    sha256sum * > SHA256SUMS.txt
)

echo "=== Release Packaging Complete ==="
ls -lh "${RELEASE_DIR}"
cat "${RELEASE_DIR}/SHA256SUMS.txt"
