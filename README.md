# Pulsemeeter
A frontend to ease the use of pulseaudio's routing capabilities, mimicking voicemeeter's workflow

![](https://i.imgur.com/djZgFTN.png)
(This screenshot was taken while using ant dracula gtk theme, its a gtk application so it will use your theme)

## Features
 - Create virtual inputs and outputs
 - Route audio from one device to another
 - Volume control
 - Equalizer for hardware and virtual outputs
 - Rnnoise noise reduction (same algorithm as [noisetorch](https://github.com/lawl/NoiseTorch)) for hardware inputs

## Installation

### Dependencies
 - pip
 - [setuptools](https://pypi.org/project/setuptools/) (installed automatically when installing app with pip)
 - [pygobject](https://pypi.org/project/PyGObject/) (installed automatically when installing app with pip)
 
 #### Optional Dependencies
 - [noise-suppression-for-voice](https://github.com/werman/noise-suppression-for-voice/)
 - [swh-plugins](https://github.com/swh/ladspa) (apt/dnf/pacman packages available)

Visit the [installation](https://github.com/theRealCarneiro/pulsemeeter/wiki/Installation) section in the wiki to get in depth information on how to install these for your specific system.

### Arch/Manjaro
A package is available in the AUR [pulsemeeter-git](https://aur.archlinux.org/packages/pulsemeeter-git/). If you use an AUR helper:
```sh
paru -S pulsemeeter-git
```

### Any distro
Clone the repo and cd into it:
```sh
git clone https://github.com/theRealCarneiro/pulsemeeter.git
cd pulsemeeter
sudo pip install .
```

### Uninstall

```sh
sudo pip uninstall pulsemeeter
```

## Discord Server
If you want to get updates about new features, patches or leave some sugestions, join our [discord server](https://discord.gg/ekWt9NuEWv)

## Special thanks to

* [xiph.org](https://xiph.org)/[Mozilla's](https://mozilla.org) excellent [RNNoise](https://jmvalin.ca/demo/rnnoise/).
* [@werman](https://github.com/werman/)'s [noise-suppression-for-voice](https://github.com/werman/noise-suppression-for-voice/)
* [@swh](https://github.com/swh)'s [swh-plugins](https://github.com/swh/ladspa)
