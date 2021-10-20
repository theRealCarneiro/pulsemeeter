# Pulsemeeter
A frontend to ease the use of pulseaudio's routing capabilities, mimicking voicemeeter's workflow

![](https://i.imgur.com/djZgFTN.png)
(This screenshot was taken while using ant dracula gtk theme, its a gtk application so it will use your theme)

## Features
 - Create virtual inputs and outputs
 - Route audio from one device to another
 - Volume control
 - Equalizer for hardware and virtual outputs
 - Rnnoise noise reduction (same algorithm as noisetorch) for hardware inputs

## Dependencies
 - pip
 - python-gobject
 - [noise-suppression-for-voice](https://github.com/werman/noise-suppression-for-voice/)
 - [swh-plugins](https://github.com/swh/ladspa)

## Installation
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
```

Install for the local user:
```sh
pip install .
```

Install globaly:
```sh
sudo pip install .
```
#### Uninstall
Uninstall for the local user:
```sh
pip uninstall pulsemeeter
```

Uninstall globaly:
```sh
sudo pip uninstall pulsemeeter
```

## Discord Server
If you want to get updates about new features, patches or leave some sugestions, join our [discord server](https://discord.gg/ekWt9NuEWv)

## Special thanks to

* [xiph.org](https://xiph.org)/[Mozilla's](https://mozilla.org) excellent [RNNoise](https://jmvalin.ca/demo/rnnoise/).
* [@werman](https://github.com/werman/)'s [noise-suppression-for-voice](https://github.com/werman/noise-suppression-for-voice/)
