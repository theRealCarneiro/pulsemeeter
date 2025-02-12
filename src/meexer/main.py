'''
Entry point
'''
import logging
# import time
import sys

from meexer.api.app_api import ipc as app_routes
from meexer.api.device_api import ipc as device_routes
from meexer.api.server_api import ipc as server_routes

# from meexer.scripts import argparser
from meexer.clients.gtk.gtk_client import GtkClient
from meexer.ipc.server_async import Server
# from meexer.ipc.client import Client

LOG = logging.getLogger("generic")


def main():
    '''
    Entry point and simple argparser
    '''

    try:
        server = Server()
        isserver = True
        server.register_blueprint(app_routes)
        server.register_blueprint(device_routes)
        server.register_blueprint(server_routes)

    except ConnectionAbortedError:
        isserver = False

    # simple args parser
    match sys.argv[1:]:

        # no args: open window
        case []:
            # trayonly = False
            if isserver:
                server.start_server(daemon=False)

            app = GtkClient()
            app.run()

            server.close_server()
            # server.exit_signal()

        # daemon: start only the server
        case ['daemon']:
            if not isserver:
                LOG.error('There\'s another server instance running')
                return 1

            # trayonly = True
            server.start_server(daemon=True)
            # server.exit_signal()

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
            pass
            # argparser.create_parser_args()

    return 0


if __name__ == '__main__':
    main()
