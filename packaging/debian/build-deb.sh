#!/usr/bin/env bash
export PATH="/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
set -Eeuo pipefail

REPO_URL="https://github.com/theRealCarneiro/pulsemeeter.git"
DEBIAN_RELEASE="stable"
DEBIAN_MIRROR="http://deb.debian.org/debian"
PACKAGE_NAME="pulsemeeter"
GIT_REF="main"
KEEP_BUILD=0
CLEAN_APT_CACHE=1
DEBUG=0

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd -- "${SCRIPT_DIR}/../.." && pwd)"
OUTPUT_DIR="${REPO_ROOT}/dist"
BUILD_ROOT=""
CHROOT_DIR=""
MOUNTED_PROC=0
MOUNTED_SYS=0
MOUNTED_DEV=0

info() { printf '[INFO] %s\n' "$*"; }
warning() { printf '[WARN] %s\n' "$*" >&2; }
debug() { [[ "${DEBUG}" -eq 1 ]] && printf '[DEBUG] %s\n' "$*" >&2 || true; }
die() { printf '[ERROR] %s\n' "$*" >&2; exit 1; }
usage() {
    cat <<'EOF'
Usage: packaging/debian/build-deb.sh [options]

Options:
  --branch REF       Build the specified git ref (default: main)
  --keep-build       Keep the temporary build directory after the build
  --no-clean-apt     Keep apt caches inside the chroot
  --debug            Enable debug logging
  -h, --help         Show this help
EOF
}

while [[ $# -gt 0 ]]; do
    case "$1" in
        --branch) [[ $# -ge 2 ]] || die "--branch requires a value."; GIT_REF="$2"; shift 2 ;;
        --keep-build) KEEP_BUILD=1; shift ;;
        --no-clean-apt) CLEAN_APT_CACHE=0; shift ;;
        --debug) DEBUG=1; shift ;;
        -h|--help) usage; exit 0 ;;
        *) die "Unknown option: $1" ;;
    esac
done

if [[ "${EUID}" -eq 0 ]]; then
    SUDO=""
    if [[ -n "${SUDO_UID:-}" ]]; then HOST_UID="${SUDO_UID}"; else HOST_UID="$(id -u)"; fi
    if [[ -n "${SUDO_GID:-}" ]]; then HOST_GID="${SUDO_GID}"; else HOST_GID="$(id -g)"; fi
else
    HOST_UID="$(id -u)"
    HOST_GID="$(id -g)"
    command -v sudo >/dev/null 2>&1 || die "sudo is required when the script is not run as root."
    SUDO="sudo"
fi

require_command() { command -v "$1" >/dev/null 2>&1 || die "Required command not found: $1"; }
for cmd in bash chroot cp cut findmnt getent grep mktemp mount mountpoint rm sed stat tar tee umount awk dpkg-deb; do require_command "$cmd"; done
command -v debootstrap >/dev/null 2>&1 || die "debootstrap is required. Install it with: sudo apt install debootstrap"

[[ -d "${REPO_ROOT}" ]] || die "Repository root does not exist: ${REPO_ROOT}"
[[ -f "${REPO_ROOT}/pyproject.toml" || -f "${REPO_ROOT}/setup.py" || -f "${REPO_ROOT}/setup.cfg" ]] || die "Could not find a Python project file in ${REPO_ROOT}."

cleanup_mounts() {
    [[ -z "${CHROOT_DIR:-}" ]] && return 0
    if [[ "${MOUNTED_DEV}" -eq 1 && -d "${CHROOT_DIR}/dev" ]]; then ${SUDO} umount -lf "${CHROOT_DIR}/dev" 2>/dev/null || true; MOUNTED_DEV=0; fi
    if [[ "${MOUNTED_SYS}" -eq 1 && -d "${CHROOT_DIR}/sys" ]]; then ${SUDO} umount -lf "${CHROOT_DIR}/sys" 2>/dev/null || true; MOUNTED_SYS=0; fi
    if [[ "${MOUNTED_PROC}" -eq 1 && -d "${CHROOT_DIR}/proc" ]]; then ${SUDO} umount -lf "${CHROOT_DIR}/proc" 2>/dev/null || true; MOUNTED_PROC=0; fi
}
cleanup() {
    local exit_code=$?
    trap - EXIT INT TERM
    cleanup_mounts
    if [[ "${KEEP_BUILD}" -eq 1 ]]; then
        [[ -n "${BUILD_ROOT:-}" && -d "${BUILD_ROOT}" ]] && warning "Temporary build directory preserved: ${BUILD_ROOT}"
    elif [[ -n "${BUILD_ROOT:-}" && -d "${BUILD_ROOT}" ]]; then
        ${SUDO} rm -rf -- "${BUILD_ROOT}" || true
    fi
    exit "${exit_code}"
}
trap cleanup EXIT INT TERM

if [[ ! -d /var/tmp ]]; then die "/var/tmp does not exist."; fi

# XDG desktop detection; intentionally avoids nested sed quoting.
detect_desktop() {
    local user_home=""
    local desktop_dir=""
    user_home="$(getent passwd "${HOST_UID}" | cut -d: -f6)"
    [[ -n "${user_home}" && -d "${user_home}" ]] || return 0
    if [[ -f "${user_home}/.config/user-dirs.dirs" ]]; then
        desktop_dir="$(awk -F= '/^XDG_DESKTOP_DIR=/ { value=$2; gsub(/^"/, "", value); gsub(/"$/, "", value); print value; exit }' "${user_home}/.config/user-dirs.dirs")"
    fi
    [[ -n "${desktop_dir}" ]] || desktop_dir="${user_home}/Desktop"
    desktop_dir="${desktop_dir/#\$HOME/${user_home}}"
    [[ -d "${desktop_dir}" ]] && printf '%s\n' "${desktop_dir}"
}
DESKTOP_DIR="$(detect_desktop || true)"

info "Repository root: ${REPO_ROOT}"
info "Output directory: ${OUTPUT_DIR}"
${SUDO} mkdir -p -- "${OUTPUT_DIR}"
${SUDO} chown "${HOST_UID}:${HOST_GID}" "${OUTPUT_DIR}"

BUILD_ROOT="$(mktemp -d /var/tmp/pulsemeeter-deb-build.XXXXXXXX)"
CHROOT_DIR="${BUILD_ROOT}/chroot"
info "Temporary build directory: ${BUILD_ROOT}"

MOUNT_OPTIONS="$(findmnt --noheadings --output OPTIONS --target "${BUILD_ROOT}" 2>/dev/null || true)"
debug "Filesystem mount options: ${MOUNT_OPTIONS}"
grep -Eq '(^|,)nodev(,|$)' <<<"${MOUNT_OPTIONS}" && die "The build filesystem is mounted with nodev. debootstrap requires mknod; use a filesystem without nodev."
grep -Eq '(^|,)noexec(,|$)' <<<"${MOUNT_OPTIONS}" && die "The build filesystem is mounted with noexec. Use a filesystem without noexec."

info "Bootstrapping Debian ${DEBIAN_RELEASE}..."
${SUDO} debootstrap --variant=minbase "${DEBIAN_RELEASE}" "${CHROOT_DIR}" "${DEBIAN_MIRROR}"

${SUDO} mount -t proc proc "${CHROOT_DIR}/proc"
MOUNTED_PROC=1
${SUDO} mount --rbind /sys "${CHROOT_DIR}/sys"
${SUDO} mount --make-rslave "${CHROOT_DIR}/sys"
MOUNTED_SYS=1
${SUDO} mount --rbind /dev "${CHROOT_DIR}/dev"
${SUDO} mount --make-rslave "${CHROOT_DIR}/dev"
MOUNTED_DEV=1

${SUDO} rm -f "${CHROOT_DIR}/etc/resolv.conf"
${SUDO} cp --dereference /etc/resolv.conf "${CHROOT_DIR}/etc/resolv.conf"
${SUDO} mkdir -p "${CHROOT_DIR}/build/output" "${CHROOT_DIR}/build/pkg"

info "Generating chroot build script..."
${SUDO} tee "${CHROOT_DIR}/build/build-inside-chroot.sh" >/dev/null <<'CHROOT_SCRIPT'
#!/usr/bin/env bash
set -Eeuo pipefail
export DEBIAN_FRONTEND=noninteractive
REPO_URL="${REPO_URL:?REPO_URL is required}"
GIT_REF="${GIT_REF:?GIT_REF is required}"
DPKG_ARCH="${DPKG_ARCH:?DPKG_ARCH is required}"
CLEAN_APT_CACHE="${CLEAN_APT_CACHE:-1}"
SOURCE_DIR="/build/source"
VENV_DIR="/build/venv"
PKG_DIR="/build/pkg"
OUTPUT_DIR="/build/output"
PACKAGE_NAME="pulsemeeter"
info() { printf '[CHROOT] %s\n' "$*"; }
warning() { printf '[CHROOT][WARN] %s\n' "$*" >&2; }
die() { printf '[CHROOT][ERROR] %s\n' "$*" >&2; exit 1; }
info "Updating APT..."
apt-get update
info "Installing build dependencies..."
apt-get install -y --no-install-recommends ca-certificates git python3 python3-dev python3-venv python3-pip python3-gi python3-pydantic gobject-introspection gir1.2-gtk-4.0 pkg-config pipewire-pulse dpkg-dev
rm -rf "${SOURCE_DIR}" "${VENV_DIR}" "${PKG_DIR}"
mkdir -p "${SOURCE_DIR}" "${PKG_DIR}/DEBIAN" "${OUTPUT_DIR}"
info "Cloning Pulsemeeter (${GIT_REF})..."
git clone --filter=blob:none --no-tags "${REPO_URL}" "${SOURCE_DIR}"
git -C "${SOURCE_DIR}" fetch --depth 1 origin "${GIT_REF}"
git -C "${SOURCE_DIR}" checkout --detach FETCH_HEAD
[[ -f "${SOURCE_DIR}/pyproject.toml" || -f "${SOURCE_DIR}/setup.py" || -f "${SOURCE_DIR}/setup.cfg" ]] || die "Python project metadata not found."
VERSION="$(PYTHONPATH="${SOURCE_DIR}/src" python3 -c 'from pulsemeeter.settings import VERSION; print(VERSION)')"
[[ -n "${VERSION}" ]] || die "Could not determine Pulsemeeter version."
case "${VERSION}" in *[!0-9A-Za-z.+~:-]*) die "Invalid Debian package version: ${VERSION}";; esac
info "Pulsemeeter version: ${VERSION}"
python3 -m venv --system-site-packages "${VENV_DIR}"
PYTHON="${VENV_DIR}/bin/python"
PIP="${VENV_DIR}/bin/pip"
"${PIP}" install --disable-pip-version-check --no-cache-dir --upgrade pip setuptools wheel
"${PIP}" install --disable-pip-version-check --no-cache-dir pulsectl pulsectl_asyncio pydantic
"${PIP}" install --disable-pip-version-check --no-cache-dir --no-deps "${SOURCE_DIR}"
"${PYTHON}" -c 'import pulsemeeter; print("Pulsemeeter import OK:", pulsemeeter.__file__)'
mkdir -p "${PKG_DIR}/DEBIAN" "${PKG_DIR}/opt/pulsemeeter" "${PKG_DIR}/usr/bin" "${PKG_DIR}/usr/share/applications" "${PKG_DIR}/usr/share/doc/${PACKAGE_NAME}"
cp -a "${VENV_DIR}/." "${PKG_DIR}/opt/pulsemeeter/"
cat > "${PKG_DIR}/usr/bin/pulsemeeter" <<'EOF'
#!/bin/sh
exec /opt/pulsemeeter/bin/python -m pulsemeeter "$@"
EOF
chmod 0755 "${PKG_DIR}/usr/bin/pulsemeeter"
DESKTOP_SOURCE=""
for candidate in "${SOURCE_DIR}/share/applications/pulsemeeter.desktop" "${SOURCE_DIR}/share/applications/org.pulsemeeter.pulsemeeter.desktop"; do
    if [[ -f "${candidate}" ]]; then DESKTOP_SOURCE="${candidate}"; break; fi
done
if [[ -n "${DESKTOP_SOURCE}" ]]; then
    DESKTOP_NAME="$(basename -- "${DESKTOP_SOURCE}")"
    cp "${DESKTOP_SOURCE}" "${PKG_DIR}/usr/share/applications/${DESKTOP_NAME}"
    sed -i 's|^Exec=.*|Exec=/usr/bin/pulsemeeter|' "${PKG_DIR}/usr/share/applications/${DESKTOP_NAME}"
fi
if [[ -f "${SOURCE_DIR}/README.md" ]]; then cp "${SOURCE_DIR}/README.md" "${PKG_DIR}/usr/share/doc/${PACKAGE_NAME}/README.md"; fi
cat > "${PKG_DIR}/DEBIAN/control" <<EOF
Package: ${PACKAGE_NAME}
Version: ${VERSION}
Section: sound
Priority: optional
Architecture: ${DPKG_ARCH}
Maintainer: Pulsemeeter contributors
Depends: python3 (>= 3.10), python3-gi, gir1.2-gtk-4.0, gobject-introspection, pipewire-pulse
Description: PulseAudio/PipeWire volume mixer
 Pulsemeeter is a graphical mixer for PulseAudio/PipeWire.
EOF
cat > "${PKG_DIR}/usr/share/doc/${PACKAGE_NAME}/copyright" <<'EOF'
Format: https://www.debian.org/doc/packaging-manuals/copyright-format/1.0/
Upstream-Name: Pulsemeeter
Source: https://github.com/theRealCarneiro/pulsemeeter

Files: *
Copyright: Pulsemeeter contributors
License: MIT
 Permission is hereby granted, free of charge, to any person obtaining a copy
 of this software and associated documentation files (the "Software"), to deal
 in the Software without restriction, including without limitation the rights
 to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 copies of the Software, and to permit persons to whom the Software is
 furnished to do so, subject to the following conditions:
 .
 The above copyright notice and this permission notice shall be included in all
 copies or substantial portions of the Software.
 .
 THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 SOFTWARE.
EOF
cat > "${PKG_DIR}/usr/share/doc/${PACKAGE_NAME}/changelog.Debian" <<EOF
${PACKAGE_NAME} (${VERSION}) unstable; urgency=medium

  * Package Pulsemeeter for Debian.

 -- Pulsemeeter contributors  $(date -u '+%a, %d %b %Y %H:%M:%S +0000')
EOF
cat > "${PKG_DIR}/DEBIAN/postinst" <<'EOF'
#!/bin/sh
set -e
exit 0
EOF
cat > "${PKG_DIR}/DEBIAN/prerm" <<'EOF'
#!/bin/sh
set -e
exit 0
EOF
chmod 0755 "${PKG_DIR}/DEBIAN/postinst" "${PKG_DIR}/DEBIAN/prerm"
DEB_FILE="${OUTPUT_DIR}/${PACKAGE_NAME}_${VERSION}_${DPKG_ARCH}.deb"
info "Building ${DEB_FILE}..."
dpkg-deb --build --root-owner-group "${PKG_DIR}" "${DEB_FILE}"
dpkg-deb --info "${DEB_FILE}" >/dev/null
dpkg-deb --contents "${DEB_FILE}" >/dev/null
if [[ "${CLEAN_APT_CACHE}" -eq 1 ]]; then rm -rf /var/lib/apt/lists/*; fi
info "Package created: ${DEB_FILE}"
CHROOT_SCRIPT

${SUDO} chmod 0755 "${CHROOT_DIR}/build/build-inside-chroot.sh"
DPKG_ARCH="$(dpkg --print-architecture)"
CHROOT_DEB="$(basename -- "${OUTPUT_DIR}")"
${SUDO} env REPO_URL="${REPO_URL}" GIT_REF="${GIT_REF}" DPKG_ARCH="${DPKG_ARCH}" CLEAN_APT_CACHE="${CLEAN_APT_CACHE}" chroot "${CHROOT_DIR}" /build/build-inside-chroot.sh

CHROOT_DEB="${CHROOT_DIR}/build/output/${PACKAGE_NAME}_*.deb"
shopt -s nullglob
DEB_FILES=( ${CHROOT_DEB} )
shopt -u nullglob
[[ "${#DEB_FILES[@]}" -eq 1 ]] || die "Expected exactly one Debian package in ${CHROOT_DIR}/build/output; found ${#DEB_FILES[@]}."
CHROOT_DEB="${DEB_FILES[0]}"
HOST_DEB="${OUTPUT_DIR}/$(basename -- "${CHROOT_DEB}")"
${SUDO} cp --preserve=mode,timestamps "${CHROOT_DEB}" "${HOST_DEB}"
${SUDO} chown "${HOST_UID}:${HOST_GID}" "${HOST_DEB}"
${SUDO} chmod 0644 "${HOST_DEB}"
if [[ -n "${DESKTOP_DIR}" && -d "${DESKTOP_DIR}" ]]; then
    DESKTOP_DEB="${DESKTOP_DIR}/$(basename -- "${HOST_DEB}")"
    ${SUDO} cp --preserve=mode,timestamps "${HOST_DEB}" "${DESKTOP_DEB}"
    ${SUDO} chown "${HOST_UID}:${HOST_GID}" "${DESKTOP_DEB}"
    ${SUDO} chmod 0644 "${DESKTOP_DEB}"
fi
info "Validating final Debian package..."
dpkg-deb --info "${HOST_DEB}" >/dev/null
dpkg-deb --contents "${HOST_DEB}" >/dev/null
info "Build completed successfully."
printf '\nDebian package:\n  %s\n' "${HOST_DEB}"
if [[ -n "${DESKTOP_DIR}" && -d "${DESKTOP_DIR}" ]]; then printf 'Desktop copy:\n  %s\n' "${DESKTOP_DIR}/$(basename -- "${HOST_DEB}")"; fi

