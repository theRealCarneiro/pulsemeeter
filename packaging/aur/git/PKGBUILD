# Maintainer: Carneiro <gabriel dot chaves dot carneiro at gmail dot com>
pkgname=pulsemeeter-git
_pkgname=pulsemeeter
pkgver=0
pkgrel=1
epoch=1
pkgdesc="A pulseaudio and pipewire audio routing application"
url="https://github.com/theRealCarneiro/pulsemeeter"
arch=('x86_64')
license=('MIT')
depends=('pipewire-pulse' 'gtk3' 'libayatana-appindicator' 'python' 'python-gobject' 'python-pydantic' 'python-pulsectl' 'python-pulsectl-asyncio')
makedepends=('git' 'python-build' 'python-setuptools' 'python-installer' 'python-wheel' 'python-babel')
optdepends=('easyeffects')
provides=('pulsemeeter')
conflicts=('pulsemeeter')
source=("${_pkgname}::git+${url}.git")
md5sums=('SKIP')

pkgver() {
	cd "$_pkgname"
	printf "r%s.g%s" "$(git rev-list --count HEAD)" "$(git rev-parse --short=7 HEAD)"
}

build() {
	cd "$_pkgname"
	python -m build --wheel --no-isolation
}

package() {
	cd "$_pkgname"
	python -m installer --destdir="$pkgdir" dist/*.whl
}
