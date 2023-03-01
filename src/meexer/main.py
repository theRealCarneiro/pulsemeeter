'''
Entry point
'''
import logging
import time
import sys

# pylint: disable=unused-import
from meexer.api import app_api, device_api, server_api  # noqa: F401
# pylint: enable=unused-import

from meexer.scripts import argparser
from meexer.clients.gtk.gtk_client import GtkClient
from meexer.ipc.server import Server
# from meexer.ipc.client import Client

LOG = logging.getLogger("generic")


def main():
    '''
    Entry point and simple argparser
    '''

    try:
        server = Server()
        isserver = True

    except ConnectionAbortedError:
        isserver = False

    # simple args parser
    match sys.argv[1:]:

        # no args: open window
        case []:
            # trayonly = False
            if isserver:
                start_server(server)

            app = GtkClient()
            app.run()

            server.exit_signal()

        # daemon: start only the server
        case ['daemon']:
            if not isserver:
                LOG.error('There\'s another server instance running')
                return 1

            # trayonly = True
            start_server(server)
            server.exit_signal()

        # init: Just start devices and connections
        case ['init']:
            # server.init_audio()
            pass

        # exit: close server, clients should close after they recive an exit signal
        case ['exit']:
            if server:
                LOG.error('No instance is running')
                return 1

            # TODO: close
            LOG.info('Closing server, it may take a few seconds...')

        # default: call cli interface
        case _:
            argparser.create_parser_args()

    return 0


def start_server(server):
    server.start_queries(daemon=True)
    time.sleep(0.1)
