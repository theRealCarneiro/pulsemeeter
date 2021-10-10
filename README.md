# Pulsemeeter
A frontend to ease the use of pulseaudio's routing capabilities, mimicking voicemeeter's workflow

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
