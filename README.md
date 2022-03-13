# Pulsemeeter
A frontend to ease the use of pulseaudio's routing capabilities, mimicking voicemeeter's workflow

[![pypi](https://img.shields.io/badge/pypi-v1.2.13-blue)](https://pypi.org/project/pulsemeeter/)
[![AUR](https://img.shields.io/badge/AUR-V1.2.12-cyan)](https://aur.archlinux.org/packages/pulsemeeter/)
[![AUR](https://img.shields.io/badge/AUR-pulsemeeter--git-red)](https://aur.archlinux.org/packages/pulsemeeter-git/)
[![Discord](https://img.shields.io/badge/chat-Discord-lightgrey)](https://discord.gg/ekWt9NuEWv)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](./LICENSE)
[![Donate](https://img.shields.io/badge/donate-PayPal-green.svg)](https://www.paypal.com/donate/?hosted_button_id=6DSVJ3V3RCVT8)
[![Donate](https://img.shields.io/badge/donate-Patreon-yellow.svg)](https://www.patreon.com/theRealCarneiro)

### Wiki: \[[Installation](https://github.com/theRealCarneiro/pulsemeeter/wiki/Installation)\] \[[How to use](https://github.com/theRealCarneiro/pulsemeeter/wiki/Installation)\]

![](https://i.imgur.com/L4KZEqV.png)
(This screenshot was taken while using ant dracula gtk theme, it will use your theme)

# Table of Contents
- **[Features](#features)**
- **[Installation](#installation)**
    - [Dependencies](#dependencies)
    - [Arch](#arch-aur)
    - [Pypi install](#any-distro)
    - [Manual/Git install](#build-from-source)
- **[Auto Start](#start-devices-on-startup)**
- **[Discord Server](#discord-server)**

# Features
 - Create virtual inputs and outputs
 - Route audio from one device to another
 - Volume control
 - Equalizer for hardware and virtual outputs
 - Rnnoise noise reduction (same algorithm as [noisetorch](https://github.com/lawl/NoiseTorch)) for hardware inputs

# Installation


## Dependencies

### Python Dependencies

 - pip

Pip will automaticly install these dependencies if you're not building from source
 - [setuptools](https://pypi.org/project/setuptools)
 - [pygobject](https://pypi.org/project/PyGObject)
 - [pulsectl](https://pypi.org/project/pulsectl)
 
 ### Optional Dependencies
 These dependencies are optional and will enable new features in the application
 - [noise-suppression-for-voice](https://github.com/werman/noise-suppression-for-voice) for noise reduction
 - [swh-plugins](https://github.com/swh/ladspa) for equalizers (apt/dnf/pacman packages available)
 - [pulse-vumeter](https://github.com/theRealCarneiro/pulse-vumeter) for volume level information

Visit the [installation](https://github.com/theRealCarneiro/pulsemeeter/wiki/Installation) section in the wiki to get in depth information on how to install these for your specific system.

## Any distro

Only optional dependencies are not installed using this method, all essential dependencies are automatically installed 

### Single user
When installing for a single user (without sudo) you need to add ~/.local/bin to your path, [this section](#add-local-bin-to-path) will show you how to do it
```sh
pip install pulsemeeter
```
### For all users
```sh
sudo pip install pulsemeeter
```

## Arch (AUR)
Two packages are available in the AUR: [pulsemeeter](https://aur.archlinux.org/packages/pulsemeeter) and [pulsemeeter-git](https://aur.archlinux.org/packages/pulsemeeter-git/).

## Build from source:

### Single user
When installing for a single user (without sudo) you need to add ~/.local/bin to your path, [this section](#add-local-bin-to-path) will show you how to do it
```sh
git clone https://github.com/theRealCarneiro/pulsemeeter.git
cd pulsemeeter
pip install -r requirements.txt
pip install .
```

### For all users
```sh
git clone https://github.com/theRealCarneiro/pulsemeeter.git
cd pulsemeeter
sudo pip install -r requirements.txt
sudo pip install .
```

### Uninstall

```sh
sudo pip uninstall pulsemeeter
```

### Add local bin to PATH

When installing for a single user, you to need to have $HOME/.local/bin in your PATH, to do this, you'll have to add this line to your ~/.profile (or .zprofile if you use zsh as your login shell) file
```sh
export PATH="$HOME/.local/bin:$PATH"
```

## Start devices on startup
All connections and devices will be restored with the command `pulsemeeter init`

## Discord Server
If you want to get updates about new features, patches or leave some sugestions, join our [discord server](https://discord.gg/ekWt9NuEWv)

## Special thanks to

* [xiph.org](https://xiph.org)/[Mozilla's](https://mozilla.org) excellent [RNNoise](https://jmvalin.ca/demo/rnnoise/).
* [@werman](https://github.com/werman/)'s [noise-suppression-for-voice](https://github.com/werman/noise-suppression-for-voice/)
* [@swh](https://github.com/swh)'s [swh-plugins](https://github.com/swh/ladspa)
