from ..settings import SOCK_FILE
import subprocess
import socket
import json
import sys
import os
import re

class Client:

    def __init__(self):

        self.sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.callback_dict = {}
        self.sub_proc = None

        # connect to server
        try:
            self.sock.connect(SOCK_FILE)
            self.id = int(self.sock.recv(4))
        except socket.error as msg:
            print(msg)
            sys.exit(1)

        self.config = json.loads(self.send_command('get-config'))


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


    def listen(self, print_event=True, blacklist_id=None):
        while True:
            try:
                event, sender_id = self.get_message()

                # only yield it if not blacklisted

                self.assert_config(event)
                if sender_id != blacklist_id:
                    self.handle_callback(event)
                    if print_event: print(event)

            except Exception as ex:
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

    def assert_config(self, event):
        event = event.split(' ')
        command = event[0]
        args = event[1:]

        if command == 'connect':
            input_type = args[0]
            input_id = args[1]
            sink = args[2] + args[3]
            state = args[4].lower() == 'true'
            self.config[input_type][input_id][sink] = state
            if len(args) > 4:
                latency = int(args[5])
                self.config[input_type][input_id][f'{sink}_latency'] = int(latency)
            print(self.config[input_type][input_id][sink])

        elif command == 'mute':
            device_type = args[0]
            device_id = args[1]
            state = args[2].lower() == 'true'
            self.config[device_type][device_id]['mute'] = state
            print(self.config[device_type][device_id]['mute'])

        elif command == 'primary':
            device_type = args[0]
            device_id = args[1]
            self.config[device_type][device_id]['primary'] = True
            print(self.config[device_type][device_id]['primary'])

            for dev_id in self.config[device_type]:
                if dev_id != device_id:
                    self.config[device_type][dev_id]['primary'] = False
                    print(self.config[device_type][dev_id]['primary'])

        elif command == 'volume':
            device_type = args[0]
            device_id = args[1]
            vol = int(args[2])
            self.config[device_type][device_id]['vol'] = vol
            print(self.config[device_type][device_id]['vol'])
        
        elif command == 'rename' or command == 'change-hd':
            device_type = args[0]
            device_id = args[1]
            name = args[2]
            self.config[device_type][device_id]['name'] = name
            print(self.config[device_type][device_id]['name'])

        elif command == 'eq':
            device_type = args[0]
            device_id = args[1]
            state = args[2].lower() == 'true'
            self.config[device_type][device_id]['use_eq'] = state
            print(self.config[device_type][device_id]['use_eq'])

            if len(args > 3):
                control = args[3]
                self.config[device_type][device_id]['eq_control'] = control
                print(self.config[device_type][device_id]['eq_control'])

        elif command == 'rnnoise':
            device_id = args[0]
            state = args[1].lower() == 'true'
            self.config[device_type][device_id]['use_rnnoise'] = state
            print(self.config[device_type][device_id]['use_rnnoise'])

            if len(args > 3):
                control = args[3]
                self.config[device_type][device_id]['rnnoise_control'] = control
                print(self.config[device_type][device_id]['rnnoise_control'])


    def verify_device(self, device_type, device_id, dev):

        if dev == 'virtual':
            if device_type not in ['vi', 'b']:
                print(f'input type {device_type} not found')
                return False

        if dev == 'hardware':
            if device_type not in ['a', 'hi']:
                print(f'input type {device_type} not found')
                return False

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

    def list_apps(self, device_type):
        command = f'get-app-list {device_type}'
        return json.loads(self.send_command(command))

    def move_app_device(self, app_id, device, stream_type):
        command = f'move-app-device {app_id} {device} {stream_type}'
        return self.send_command(command)

    def get_app_volume(self, app_id, stream_type):
        command = f'get-stream-volume {app_id} {stream_type}'
        return int(self.send_command(command))

    def set_app_volume(self, app_id, vol, stream_type):
        command = f'app-volume {app_id} {vol} {stream_type}'
        return self.send_command(command)

    def connect(self, input_type, input_id, output_type, output_id, state=None, latency=None):
        
        if (not self.verify_device(input_type, input_id, 'input') 
                or not self.verify_device(output_type, output_id, 'output')):
            return

        command = f'connect {input_type} {input_id} {output_type} {output_id}'
        if state != None: command += f' {state}'
        if latency != None: command += f' {latency}'

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


    def rnnoise(self, input_id, state=None, control=None, latency=None):

        if not input_id.isdigit():
            return 'invalid device index'

        command = f'rnnoise {input_id}'
        if state != None: command += f' {state}'
        if control and latency: command += f' {control} {latency}'
        print(command)

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
        if type(vol) == str:
            if not re.match('[+-]?\d+$', vol):
                return 'invalid volume'

        command = f'volume {device_type} {device_id} {vol}'
        return self.send_command(command)


    def rename(self, device_type, device_id, name):

        if not self.verify_device(device_type, device_id, 'virtual'):
            return

        command = f'rename {device_type} {device_id} {name}'
        return self.send_command(command)


    def change_hardware_device(self, device_type, device_id, device):

        if not self.verify_device(device_type, device_id, 'any'):
            return

        command = f'change_hd {device_type} {device_id} {device}'
        return self.send_command(command)


    def list_hardware_devices(self, device_type):
        if device_type not in ['sinks', 'sources']:
            return

        return json.loads(self.send_command(f'get-hd {device_type}'))


    def list_virtual_devices(self, device_type):
        if device_type not in ['sinks', 'sources']:
            return

        return json.loads(self.send_command(f'get-vd {device_type}'))


    def close_connection(self):
        self.sock.shutdown(socket.SHUT_RDWR)

    def subscribe(self):
        command = ['pactl', 'subscribe']
        sys.stdout.flush()
        env = os.environ
        env['LC_ALL'] = 'C'
        self.sub_proc = subprocess.Popen(command, env=env, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.STDOUT,
            universal_newlines=True)

        for stdout_line in iter(self.sub_proc.stdout.readline, ""):
            yield stdout_line 
            
        self.sub_proc.stdout.close()
        return_code = self.sub_proc.wait()
        if return_code:
            raise subprocess.CalledProcessError(return_code, command)

    def end_subscribe(self):
        if self.sub_proc != None:
            self.sub_proc.terminate()
