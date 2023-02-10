import pulsemeeter.scripts.argparser as argparser
import traceback
import logging
import time
import sys

from pulsemeeter.controller.window_controller import WindowController
from meexer.ipc.server import Server
from meexer.ipc.client import Client

LOG = logging.getLogger("generic")


def start_server(server):
    try:
        server.start_server(daemon=True)
        time.sleep(0.1)
    except Exception:
        print('Could not start server because of:\n')
        traceback.print_exc()
        sys.exit(1)


def main():
    # it will raise ConnectionAbortedError if there's another instance running
    try:
        server = Server()
        isserver = True

    except ConnectionAbortedError:
        isserver = False

    # simple args parser
    match sys.argv[1:]:

        # no args: open window
        case []:
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
                client = Client()
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
    WindowController(isserver, trayonly)

    # close server if there was a server started
    if isserver: server.stop_server()

    return 0
