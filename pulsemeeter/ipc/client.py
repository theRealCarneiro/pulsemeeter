import threading
import traceback
import logging
import socket
# import json

from queue import SimpleQueue

from pulsemeeter.settings import SOCK_FILE

LOG = logging.getLogger("generic")


class Client:

    def __init__(self, listen=False, noconfig=False):

        self.sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.exit_flag = False
        self.listen_thread = None
        self.sub_proc = None
        self.return_queue = SimpleQueue()
        self.event_queue = SimpleQueue()
        self.can_listen = listen
        self.noconfig = noconfig

        # connect to server
        try:
            self.sock.connect(SOCK_FILE)
            self.id = int(self.sock.recv(4))
        except socket.error:
            LOG.error(traceback.format_exc())
            LOG.error("Could not connect to server")
            raise

        if listen:
            self.start_listen()

    # start listen thread
    def start_listen(self):
        '''
        starts the listening thread.
        (starts if listen=True in Client class)
        '''
        if self.listen_thread is not None:
            self.stop_listen()
        self.listen_thread = threading.Thread(target=self.listen)
        self.listen_thread.start()

    # stop listen thread
    def stop_listen(self):
        '''
        stops the listening thread if there is one.
        '''
        self.exit_flag = True
        # if self.listen_thread is not None:
            # self.listen_thread.join()

    def disconnect(self):
        self.send_command('quit')
        self.stop_listen()
        self.sock.close()
        LOG.info('closing connection to socket')

    def send_command(self, command, nowait=False):
        '''
        Send command manually to server.

        '''
        try:

            # encode message ang get it's length
            message = command.encode()
            msg_len = len(message)
            if msg_len == 0: raise Exception

            # send message length
            msg_len = str(msg_len).rjust(4, '0')
            self.sock.sendall(msg_len.encode())

            # send message
            self.sock.sendall(message)

            if command == 'quit':
                return

            # wait for answer
            ret_msg = ''
            if nowait or not self.can_listen:
                ret_msg = self.get_message()
            else:
                ret_msg = self.return_queue.get()

            return ret_msg

        except Exception:
            LOG.info('closing connection to socket')
            self.sock.close()
            raise

    def listen(self):
        '''
        Starts to listen to server events. (gets called by start_listen)
        '''
        while not self.exit_flag:
            try:
                sender_id = self.sock.recv(4)
                if not sender_id: raise ConnectionError
                try:
                    sender_id = int(sender_id)
                except ValueError:
                    sender_id = None

                # length of the message
                msg_len = self.sock.recv(4)
                if not msg_len: raise ConnectionError
                msg_len = int(msg_len.decode())

                # get event
                event = self.sock.recv(msg_len)
                if not event: raise ConnectionError
                event = event.decode()

                # if not self.noconfig and sender_id is not None:
                    # self.assert_config(event)

                # exit and primary are the only events that the caller needs
                # to recive like a normal event
                self.event_queue.put((event, sender_id))
                if sender_id == self.id:
                    self.return_queue.put(event)

            except ConnectionError:
                LOG.info('closing socket')
                break

            # except Exception as ex:
                # print('closing socket')
                # raise

    def get_message(self):
        while True:
            try:
                # get the id of the client that sent the message
                sender_id = self.sock.recv(4)
                if not sender_id: raise Exception
                try:
                    sender_id = int(sender_id)
                except ValueError:
                    sender_id = None

                # length of the message
                msg_len = self.sock.recv(4)
                if not msg_len: raise Exception
                msg_len = int(msg_len.decode())

                # get event
                event = self.sock.recv(msg_len)
                if not event: raise Exception
                event = event.decode()

                if self.id == sender_id:
                    return event

            except Exception:
                raise
