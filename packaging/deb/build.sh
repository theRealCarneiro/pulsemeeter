#!/usr/bin/env bash
# Build the pulsemeeter .deb from the current working tree.
#
#   packaging/deb/build.sh [OUTPUT_DIR]        (default: dist/deb)
#
# Build dependencies (Debian/Ubuntu):
#   sudo apt install build-essential git debhelper dh-python pybuild-plugin-pyproject \
#     python3-all python3-babel python3-setuptools python3-wheel python3-pip
#
# Environment:
#   DEB_REVISION         Debian revision appended to the version (default: 1)
#   DEB_VERSION_SUFFIX   Appended after the revision, e.g. "~r776.g8a9ac3f"
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$HERE/../.." && pwd)"
OUT_DIR="$(realpath -m "${1:-$ROOT/dist/deb}")"

# Version is single-sourced from pulsemeeter.settings.VERSION
VERSION="$(sed -n "s/^VERSION = ['\"]\([^'\"]*\)['\"].*/\1/p" "$ROOT/src/pulsemeeter/settings.py")"
if [ -z "$VERSION" ]; then
    echo "VERSION not found in src/pulsemeeter/settings.py" >&2
    exit 1
fi
DEB_VERSION="$VERSION-${DEB_REVISION:-1}${DEB_VERSION_SUFFIX:-}"

WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT
# dpkg-buildpackage writes the .deb next to the source dir, so build one level down
SRC="$WORK/pulsemeeter-$VERSION"
mkdir "$SRC"

echo "Staging source for pulsemeeter $DEB_VERSION"
if git -C "$ROOT" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    # Tracked and untracked-but-not-ignored files: local edits are built, venvs and build output are not
    git -C "$ROOT" ls-files -z --cached --others --exclude-standard \
        | tar -C "$ROOT" --null --files-from=- --ignore-failed-read -cf - \
        | tar -C "$SRC" -xf -
else
    tar -C "$ROOT" --exclude=./.git --exclude=./dist --exclude=./build --exclude=./buildzip \
        --exclude=./.venv --exclude=./venv -cf - . | tar -C "$SRC" -xf -
fi

cp -r "$HERE/debian" "$SRC/debian"
sed -i "1s/([^)]*)/($DEB_VERSION)/" "$SRC/debian/changelog"

echo "Bundling pinned Python dependencies"
python3 -m pip install --quiet --disable-pip-version-check --root-user-action=ignore \
    --no-deps --no-compile --only-binary=:all: --require-hashes \
    --target "$SRC/vendor" -r "$HERE/vendor-requirements.txt"
rm -rf "$SRC/vendor/pulsectl/tests"

echo "Building package"
(cd "$SRC" && dpkg-buildpackage --build=binary --no-sign)

mkdir -p "$OUT_DIR"
cp "$WORK"/*.deb "$OUT_DIR"/
echo "Built: $(cd "$WORK" && ls -- *.deb | sed "s|^|$OUT_DIR/|")"
