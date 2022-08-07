import traceback
import logging
import time
import sys

import pulsemeeter.scripts.argparser as argparser
from pulsemeeter.interface_old.main_window import MainWindow
from pulsemeeter.api.audio_server import AudioServer
from pulsemeeter.api.audio_client import AudioClient

from gi import require_version as gi_require_version
gi_require_version('Gtk', '3.0')
from gi.repository import Gtk  # type: ignore

LOG = logging.getLogger("generic")


def start_server(server):
    try:
        server.start_server(daemon=True)
        time.sleep(0.1)
    except Exception:
        print('Could not start server because of:\n')
        traceback.print_exc()
        sys.exit(1)


def start_app(isserver, trayonly):
    MainWindow(isserver=isserver, trayonly=trayonly)
    Gtk.main()


def main():

    # it will raise ConnectionAbortedError if there's another instance running
    try:
        server = AudioServer(init_server=False)
        isserver = True

    except ConnectionAbortedError:
        isserver = False

    # simple args parser
    match sys.argv[1:]:

        # no args: open window
        case []:
            print('aq')
            trayonly = False

        # daemon: start only the server
        case ['daemon']:
            if not isserver:
                LOG.error('There\'s another server instance running')
                return 1

            trayonly = True

        # init: Just start devices and connections
        case ['init']:
            server.init_audio()
            return 0

        # exit: close server, all clients should close after they recive an exit signal
        case ['exit']:
            if not isserver:
                LOG.info('Closing server, it may take a few seconds...')
                client = AudioClient()
                client.close_server()
                return 0
            else:
                LOG.error('No instance is running')
                return 1

        # default: call cli interface
        case _:
            argparser.create_parser_args()
            return 0

    # only no args and daemon arg reach this part of the code

    # start server if there's no server running
    if isserver: start_server(server)
    start_app(isserver, trayonly)

    # close server if there was a server started
    if isserver: server.stop_server()

    return 0
