from ..settings import SOCK_FILE
import socket
import sys
import os
import re

class Client:
    def __init__(self):

        self.sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.callback_dict = {}

        # connect to server
        try:
            self.sock.connect(SOCK_FILE)
            self.id = int(self.sock.recv(4))
        except socket.error as msg:
            print(msg)
            sys.exit(1)

    def send_command(self, command):
        try:

            # encode message ang get it's length
            message = command.encode()
            msg_len = len(message)
            if msg_len == 0 or command == 'exit': raise

            # send message length
            msg_len = str(msg_len).rjust(4, '0')
            self.sock.sendall(msg_len.encode())

            # send message
            self.sock.sendall(message)

            # wait for answer
            message, id = self.get_message(wait_id=self.id)
            return message
            # for event in self.listen(wait_id=self.id):
                # return(event)
                
        except:
            print('closing socket')
            self.sock.close()

    def listen(self, yield_event=True, blacklist_id=None):
        while True:
            try:
                event, sender_id = self.get_message()

                # only yield it if not blacklisted
                if sender_id != blacklist_id:
                    self.handle_callback(event)
                    if yield_event: yield event

            except Exception as ex:
                print('closing socket')
                print(ex)
                break

    def get_message(self, wait_id=None):
        sender_id = None
        while True:
            # get the id of the client that sent the message
            sender_id = self.sock.recv(4)
            if not sender_id: raise
            sender_id = int(sender_id)

            # length of the message
            msg_len = self.sock.recv(4)
            if not msg_len: raise
            msg_len = int(msg_len.decode())
            
            # get event
            event = self.sock.recv(msg_len)
            if not event: raise
            event = event.decode()

            if wait_id == None or wait_id == sender_id:
                return (event, sender_id)

    def set_callback_function(self, command, function):
        self.callback_dict[command] = function

    def handle_callback(self, event):
        command = event.split(' ')
        if command[0] not in self.callback_dict:
            return

        function = self.callback_dict[command[0]]
        args = tuple(command[1:])
        function(*args)

    def verify_device(self, device_type, device_id, dev):

        if dev == 'input':
            if device_type not in ['hi', 'vi']:
                print(f'input type {device_type} not found')
                return False

        if dev == 'output':
            if device_type not in ['a', 'b']:
                print(f'output type {device_type} not found')
                return False

        if dev == 'any':
            if device_type not in ['hi', 'vi', 'a', 'b']:
                print(f'output type {device_type} not found')
                return False

        if not device_id.isdigit() or not device_id.isdigit():
            print(f'invalid device index {device_id}')
            return False

        return True

    def connect(self, input_type, input_id, output_type, output_id, state=None):
        
        if (not self.verify_device(input_type, input_id, 'input') 
                or not self.verify_device(output_type, output_id, 'output')):
            return

        command = f'connect {input_type} {input_id} {output_type} {output_id}'
        if state != None: command += f' {state}'

        return self.send_command(command)

    def mute(self, device_type, device_id, state=None):

        if not self.verify_device(device_type, device_id, 'any'):
            return

        command = f'mute {device_type} {device_id}'
        if state != None: command += f' {state}'

        return self.send_command(command)

    def primary(self, device_type, device_id):

        if not self.verify_device(device_type, device_id, 'any'):
            return

        command = f'mute {device_type} {device_id}'

        return self.send_command(command)

    def rnnoise(self, input_id, state=None):

        if not input_id.isdigit():
            return 'invalid device index'

        command = f'rnnoise {input_id}'
        if state != None: command += f' {state}'

        return self.send_command(command)

    def eq(self, output_type, output_id, state=None, control=None):

        if not self.verify_device(output_type, output_id, 'output'):
            return

        command = f'eq {output_type} {output_id}'

        if control != None and state == 'set':
            command += f' set {control}'

        elif control != None and state != 'set':
            return

        return self.send_command(command)

    def volume(self, device_type, device_id, vol):

        if not self.verify_device(device_type, device_id, 'any'):
            return

        if not re.match('(\+|\-)?\d+$', vol):
            return 'invalid volume'

        command = f'volume {device_type} {device_id} {vol}'

        return self.send_command(command)

    def change_hardware_device(self, device_type, device_id, device):

        if not self.verify_device(device_type, device_id, 'any'):
            return

        command = f'eq {device_type} {device_id} {device}'

        return self.send_command(command)

    def close_connection(self):
        print('closing socket')
        self.sock.close()
