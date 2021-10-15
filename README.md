# Pulsemeeter
A frontend to ease the use of pulseaudio's routing capabilities, mimicking voicemeeter's workflow

![](https://i.imgur.com/5nxfjSX.png)
(This screenshot was taken while using ant dracula gtk theme, its a gtk application so it will use your theme)

## Features
 - Create virtual inputs and outputs
 - Route audio from one device to another
 - Volume controll

## Dependencies
 - python-gobject

## Installation
### Arch/Manjaro
A package is available in the AUR [pulsemeeter-git](https://aur.archlinux.org/packages/pulsemeeter-git/). If you use an AUR helper:
```sh
paru -S pulsemeeter-git
```

### Any distro
Clone the repo and run the makefile:
```sh
git clone https://github.com/theRealCarneiro/pulsemeeter.git
cd pulsemeeter
sudo make install
```
#### Uninstall
```sh
sudo make uninstall
```

### Discord Server
If you want to get updates about new features, patches or leave some sugestions, join our [discord server](https://discord.gg/ekWt9NuEWv)

### Special thanks to

* [xiph.org](https://xiph.org)/[Mozilla's](https://mozilla.org) excellent [RNNoise](https://jmvalin.ca/demo/rnnoise/).
* [@lawl](https://github.com/lawl) for making ladspa rnnoise plugin and [Noisetorch](https://github.com/lawl/NoiseTorch)
