#!/usr/bin/env python3
from interface import MainWindow
from pulse import Pulse
from gi.repository import Gtk
import json
import sys


def main():
    config = json.load(open("./config.json"))
    pulse = Pulse(config)
    app = MainWindow(config)
    return Gtk.main()


if __name__ == '__main__':
    mainret = main()
    sys.exit(mainret)
