# Maintainer: Arafat Zahan <kuasha420@gmail.com>
pkgname=jimha
pkgver=2.0.0
pkgrel=1
pkgdesc="A toddler-safe fullscreen interactive sensory key smash wonderland for Jimha"
arch=('x86_64' 'aarch64')
url="https://github.com/kuasha420/jimha"
license=('MIT')
depends=('gtk3' 'webkit2gtk-4.1' 'hicolor-icon-theme')
makedepends=('cargo' 'nodejs' 'pnpm' 'rust')
source=("$pkgname-$pkgver.tar.gz::$url/archive/refs/tags/v$pkgver.tar.gz")
sha256sums=('SKIP')

build() {
  if [ -d "$srcdir/$pkgname-$pkgver" ]; then
    cd "$srcdir/$pkgname-$pkgver"
  else
    cd "$startdir"
  fi

  pnpm install --frozen-lockfile
  pnpm build
  cargo build --manifest-path src-tauri/Cargo.toml --release
}

package() {
  if [ -d "$srcdir/$pkgname-$pkgver" ]; then
    cd "$srcdir/$pkgname-$pkgver"
  else
    cd "$startdir"
  fi

  # Binary installation
  install -Dm755 src-tauri/target/release/jimha "$pkgdir/usr/bin/jimha"

  # Desktop & Metainfo integration
  install -Dm644 org.purrfect.jimha.desktop "$pkgdir/usr/share/applications/org.purrfect.jimha.desktop"
  install -Dm644 org.purrfect.jimha.metainfo.xml "$pkgdir/usr/share/metainfo/org.purrfect.jimha.metainfo.xml"

  # High-resolution icons
  install -Dm644 assets/jimha.svg "$pkgdir/usr/share/icons/hicolor/scalable/apps/org.purrfect.jimha.svg"
  install -Dm644 assets/jimha.png "$pkgdir/usr/share/icons/hicolor/512x512/apps/org.purrfect.jimha.png"
  install -Dm644 src-tauri/icons/128x128.png "$pkgdir/usr/share/icons/hicolor/128x128/apps/org.purrfect.jimha.png"
  install -Dm644 src-tauri/icons/32x32.png "$pkgdir/usr/share/icons/hicolor/32x32/apps/org.purrfect.jimha.png"

  # License
  install -Dm644 LICENSE "$pkgdir/usr/share/licenses/$pkgname/LICENSE"
}
