import socket 
import sys
import os
from .settings import SOCK_FILE

class Server:
    def __init__(self, audio_server):

        # audio server can be pulse or pipe, so just use a generic name
        self.audio_server = audio_server

        self.sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)

        # list of messages to deliver to listening clients
        self.msg_queue = []

        # list of clients
        self.client_list = []

        # delete socket file if exists
        try:
            os.unlink(SOCK_FILE)
        except OSError:
            if os.path.exists(SOCK_FILE):
                raise

        self.sock.bind(SOCK_FILE)
        self.sock.listen(1)
        self.listen()

    def listen(self):
        while True:

            # Wait for a connection
            print('waiting for a connection')
            connection, client_address = self.sock.accept()
            # self.client_list.append

            print('client connected ', client_address)
            pid = os.fork()
            if not pid:
                while True:
                    try:
                        data = connection.recv(20)
                        if not data: raise

                        print(data.decode())
                        ret_message = self.handle_command(data)
                        connection.sendall(ret_message)
                        if ret_message == False:
                            print('deu ruim')
                            raise
                    except:
                        print('client disconnect')
                        connection.close()
                        break

    def handle_command(self, data):

        decoded_data = data.decode()
        cmd_list = decoded_data.split(' ')

        # command interpreter
        # need to add error handling

        # connect [vi|hi] [1-3] [a|b] [1-3]
        if cmd_list[0] == 'connect':
            if len(cmd_list) != 5: return
            source_index = [cmd_list[1], cmd_list[2]]
            sink_index = [cmd_list[3], cmd_list[4]]
            if self.audio_server.connect('connect', source_index, sink_index):
                msg = f'{cmd_list[1]}{cmd_list[2]}:{cmd_list[3]}{cmd_list[4]}:True'
                self.msg_queue.append(str.encode(msg))

        # disconnect [vi|hi] [1-3] [a|b] [1-3]
        if cmd_list[0] == 'disconnect':
            source_index = [cmd_list[1], cmd_list[2]]
            sink_index = [cmd_list[3], cmd_list[4]]
            if self.audio_server.connect('disconnect', source_index, sink_index):
                return str.encode(f'{cmd_list[1]}{cmd_list[2]}:{cmd_list[3]}{cmd_list[4]}:False')

        # vol [vi|hi|a|b] [1-3] 
        if cmd_list[0] == 'vol':
            device_index = [cmd_list[1], cmd_list[2]]
            volume = cmd_list[3]
            if self.audio_server.volume(device_index, volume):
                return str.encode(f'{cmd_list[1]}{cmd_list[2]}:{cmd_list[3]}')

        if cmd_list[0] == 'mute':
            device_index = [cmd_list[1], cmd_list[2]]

        if cmd_list[0] == 'exit':
            return False

        return b' '

class Client:
    def __init__(self, command=None, is_listen=False):

        self.sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)

        # connect to server
        try:
            self.sock.connect(SOCK_FILE)
        except socket.error as msg:
            print(msg)
            sys.exit(1)   
            if is_listen == True: self.listen()

        if command != None:
            self.send_command(command)

        # while True:
            # self.send_command()
        

    def send_command(self, command=None):
        try:
            tmp = input()
            if len(tmp) == 0 or tmp == 'exit':
                raise

            message = str.encode(tmp)
            self.sock.sendall(message)
            # print(self.sock.recv(20))
        except:
            print('closing socket')
            self.sock.close()
            break

    def listen(self):
        while True:
            try:
                print(self.sock.recv(20))
            except:
                print('closing socket')
                self.sock.close()
                break
