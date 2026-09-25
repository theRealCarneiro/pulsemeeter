# Pulsemeeter

A frontend to ease the use of pulseaudio's routing capabilities, much like voicemeeter's workflow

[![translated](https://hosted.weblate.org/widget/pulsemeeter/pulsemeeter/svg-badge.svg)](https://hosted.weblate.org/projects/pulsemeeter/pulsemeeter/)
[![pypi](https://img.shields.io/pypi/v/pulsemeeter)](https://pypi.org/project/pulsemeeter/)
[![AUR](https://img.shields.io/aur/version/pulsemeeter?label=AUR-stable&color=cyan)](https://aur.archlinux.org/packages/pulsemeeter/)
[![AUR](https://img.shields.io/aur/version/pulsemeeter-git?label=AUR-git&color=red)](https://aur.archlinux.org/packages/pulsemeeter-git/)
[![Discord](https://img.shields.io/badge/chat-Discord-lightgrey)](https://discord.gg/ekWt9NuEWv)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](./LICENSE)
[![Donate](https://img.shields.io/badge/donate-PayPal-green.svg)](https://www.paypal.com/donate/?hosted_button_id=6DSVJ3V3RCVT8)
[![Donate](https://img.shields.io/badge/donate-Patreon-yellow.svg)](https://www.patreon.com/theRealCarneiro)

### Wiki: \[[Installation](https://github.com/theRealCarneiro/pulsemeeter/wiki/Installation)\] \[[How to use](https://github.com/theRealCarneiro/pulsemeeter/wiki/How-to-use)\]

![](https://github.com/user-attachments/assets/19e06982-6c91-4c13-97c0-8b3b8ab173c5)

<!--(This screenshot was taken while using ant dracula gtk theme, it will use your theme)-->

# Features
- Create virtual inputs and outputs
- Route audio from input devices to output devices, either hardware or virtual
- Volume and mute control
- Channel layout for virtual devices (mono, stereo, etc.)
- Port selection for hardware devices (choose which channels of a hardware device should be active)
- Custom port-to-port connection mapping

# Installation
Please visit the [wiki](https://github.com/theRealCarneiro/pulsemeeter/wiki/Installation) for in depth information on how to install.

# Debian package

A Debian .deb package can be built locally using the 
packaging script included in this repository.
Requirements

The build host must be a Debian-based system with debootstrap installed:

sudo apt update
sudo apt install debootstrap

## Build

From the repository root:

./packaging/debian/build-deb.sh

The generated package will be available in the dist/ directory.

To install the package:

sudo dpkg -i ~/Desktop/pulsemeeter_*.deb

For troubleshooting, the temporary build environment can be kept with:

The Debian package builder creates an isolated Debian build environment and does not modify the host system apart from the tools required to perform the build.

# Discord Server
If you want to get updates about new features, patches or leave some sugestions, join our [discord server](https://discord.gg/ekWt9NuEWv)
