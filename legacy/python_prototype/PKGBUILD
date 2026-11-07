# Maintainer: Arafat Zahan <kuasha420@gmail.com>
pkgname=jimha
pkgver=1.0.1
pkgrel=1
pkgdesc="A toddler-safe fullscreen interactive key smash wonderland for JimHa"
arch=('any')
url="https://github.com/kuasha420/jimha"
license=('MIT')
depends=('python' 'python-pyqt6' 'hicolor-icon-theme')
makedepends=('python-setuptools')
source=("$pkgname-$pkgver.tar.gz::$url/archive/refs/tags/v$pkgver.tar.gz")
sha256sums=('SKIP')

build() {
  if [ -d "$srcdir/$pkgname-$pkgver" ]; then
    cd "$srcdir/$pkgname-$pkgver"
  else
    cd "$startdir"
  fi
  /usr/bin/python setup.py build
}

package() {
  if [ -d "$srcdir/$pkgname-$pkgver" ]; then
    cd "$srcdir/$pkgname-$pkgver"
  else
    cd "$startdir"
  fi
  /usr/bin/python setup.py install --root="$pkgdir" --optimize=1 --skip-build

  install -Dm644 jimha.desktop "$pkgdir/usr/share/applications/jimha.desktop"
  install -Dm644 assets/jimha.svg "$pkgdir/usr/share/icons/hicolor/scalable/apps/jimha.svg"
  install -Dm644 assets/jimha.png "$pkgdir/usr/share/icons/hicolor/512x512/apps/jimha.png"
  install -Dm644 LICENSE "$pkgdir/usr/share/licenses/$pkgname/LICENSE"
}
