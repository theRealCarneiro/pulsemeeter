from ..settings import SOCK_FILE
import subprocess
import socket
import threading
import json
import sys
import os
import re
from queue import SimpleQueue

class Client:

    def __init__(self, listen=False, noconfig=False):

        self.sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.exit_flag = False
        self.callback_dict = {}
        self.listen_thread = None
        self.sub_proc = None
        self.return_queue = SimpleQueue()
        self.can_listen = listen
        self.noconfig = noconfig

        # connect to server
        try:
            self.sock.connect(SOCK_FILE)
            self.id = int(self.sock.recv(4))
        except socket.error as msg:
            print(msg)
            sys.exit(1)

        self.config = json.loads(self.send_command('get-config', nowait=True))

        if self.can_listen:
            self.start_listen()

    # start listen thread
    def start_listen(self, print_event=False):
        self.stop_listen()
        self.listen_thread = threading.Thread(target=self.listen, args=(print_event,))
        self.listen_thread.start()

    # stop listen thread
    def stop_listen(self):
        if self.listen_thread != None: 
            self.exit_flag = True
            self.listen_thread.join()

    def send_command(self, command, nowait=False):
        try:

            # encode message ang get it's length
            message = command.encode()
            msg_len = len(message)
            if msg_len == 0: raise

            # send message length
            msg_len = str(msg_len).rjust(4, '0')
            self.sock.sendall(msg_len.encode())

            # send message
            self.sock.sendall(message)

            # wait for answer
            ret_msg = ''
            if nowait or not self.can_listen:
                ret_msg = self.get_message() 
            else: 
                ret_msg = self.return_queue.get()

            return ret_msg

                
        except:
            print('closing socket')
            self.sock.close()
            raise


    def listen(self, print_event=True):
        while True:
            try:
                if self.exit_flag == True: break
                sender_id = self.sock.recv(4)
                if not sender_id: raise ConnectionError
                sender_id = int(sender_id)

                # length of the message
                msg_len = self.sock.recv(4)
                if not msg_len: raise ConnectionError
                msg_len = int(msg_len.decode())
                
                # get event
                event = self.sock.recv(msg_len)
                if not event: raise ConnectionError
                event = event.decode()

                if event == 'exit':
                    self.handle_callback(event)
                    continue

                if not self.noconfig: self.assert_config(event)
                if print_event: print(event)
                if sender_id != self.id:
                    self.handle_callback(event)
                else:
                    self.return_queue.put(event)

            except ConnectionError:
                print('closing socket')
                break

            # except Exception as ex:
                # print('closing socket')
                # raise



    def get_message(self):
        while True:
            try:
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


                if self.id == sender_id:
                    return event

            except:
                raise


    # set a callback function to a command
    def set_callback_function(self, command, function):
        self.callback_dict[command] = function

    def handle_callback(self, event):
        command = event.split(' ')
        if command[0] not in self.callback_dict:
            return
        
        function = self.callback_dict[command[0]]
        args = tuple(command[1:])
        function(*args)

    # update the config
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

        elif command == 'mute':
            device_type = args[0]
            device_id = args[1]
            state = args[2].lower() == 'true'
            self.config[device_type][device_id]['mute'] = state

        elif command == 'primary':
            device_type = args[0]
            device_id = args[1]
            self.config[device_type][device_id]['primary'] = True

            for dev_id in self.config[device_type]:
                if dev_id != device_id:
                    self.config[device_type][dev_id]['primary'] = False

        elif command == 'volume':
            device_type = args[0]
            device_id = args[1]
            vol = int(args[2])
            self.config[device_type][device_id]['vol'] = vol
        
        elif command == 'rename' or command == 'change-hd':
            device_type = args[0]
            device_id = args[1]
            name = args[2]
            if name == 'None':
                name = ''
            self.config[device_type][device_id]['name'] = name

        elif command == 'eq':
            device_type = args[0]
            device_id = args[1]
            state = args[2].lower() == 'true'
            self.config[device_type][device_id]['use_eq'] = state

            if len(args) > 3:
                control = args[3]
                self.config[device_type][device_id]['eq_control'] = control

        elif command == 'layout':
            layout = args[0]
            self.config['layout'] = layout

        elif command == 'cleanup':
            state = args[0]
            self.config['cleanup'] = state.lower() == 'true'

        elif command == 'tray':
            state = args[0]
            self.config['tray'] = state.lower() == 'true'

        elif command == 'rnnoise':
            device_id = args[0]
            state = args[1].lower() == 'true'
            self.config['hi'][device_id]['use_rnnoise'] = state

            if len(args) > 2:
                control = args[2]
                self.config['hi'][device_id]['rnnoise_control'] = control


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

    def connect(self, input_type, input_id, output_type, output_id, state=None, latency=None):

        if (not self.verify_device(input_type, input_id, 'input') 
                or not self.verify_device(output_type, output_id, 'output')):
            return
           
        command = f'connect {input_type} {input_id} {output_type} {output_id}'
        if state != None: command += f' {state}'
        if latency != None: command += f' {latency}'
        
        if self.config[input_type][input_id][f'{output_type}{output_id}'] == state:
            return

        return self.send_command(command)


    def mute(self, device_type, device_id, state=None):

        if not self.verify_device(device_type, device_id, 'any'):
            return

        command = f'mute {device_type} {device_id}'
        if state != None: command += f' {state}'

        # print('config: ', self.config[device_type][device_id]['mute'], 'new: ', state)
        if self.config[device_type][device_id]['mute'] == state:
            return
        return self.send_command(command)


    def primary(self, device_type, device_id):

        if not self.verify_device(device_type, device_id, 'any'):
            return

        command = f'primary {device_type} {device_id}'

        if self.config[device_type][device_id]['primary'] == True:
            return
        return self.send_command(command)


    def rnnoise(self, input_id, state=None, control=None, latency=None):

        if not input_id.isdigit():
            return 'invalid device index'

        command = f'rnnoise {input_id}'
        if state != None: command += f' {state}'
        if control and latency: command += f' {control} {latency}'

        if (self.config['hi'][input_id]['use_rnnoise'] == state
                or self.config['hi'][input_id]['rnnoise_control'] == control):
            return
        return self.send_command(command)


    def eq(self, output_type, output_id, state=None, control=None):

        if not self.verify_device(output_type, output_id, 'output'):
            return

        command = f'eq {output_type} {output_id}'

        if control != None and state == 'set':
            command += f' set {control}'

        elif control == None and state != None:
            command += f' {state}'

        elif control != None and state != 'set':
            return

        if (self.config[output_type][output_id]['use_eq'] == state
                or self.config[output_type][output_id]['eq_control'] == control):
            return
        return self.send_command(command)


    def volume(self, device_type, device_id, vol):

        if not self.verify_device(device_type, device_id, 'any'):
            return
        if type(vol) == str:
            if not re.match('[+-]?\d+$', vol):
                return 'invalid volume'
            if re.match('^\d+$', vol):
                if self.config[device_type][device_id]['vol'] == int(vol):
                    return

        command = f'volume {device_type} {device_id} {vol}'

        return self.send_command(command)


    def rename(self, device_type, device_id, name):

        if not self.verify_device(device_type, device_id, 'virtual'):
            return

        command = f'rename {device_type} {device_id} {name}'
        if self.config[device_type][device_id]['name'] == name:
            return
        return self.send_command(command)


    def change_hardware_device(self, device_type, device_id, device):

        if device == self.config[device_type][device_id]['name']:
            return

        if device == '':
            device = None

        if not self.verify_device(device_type, device_id, 'any'):
            return

        command = f'change_hd {device_type} {device_id} {device}'
        if self.config[device_type][device_id]['name'] == device:
            return
        return self.send_command(command)


    def list_hardware_devices(self, device_type):
        if device_type not in ['sinks', 'sources']:
            return

        return json.loads(self.send_command(f'get-hd {device_type}'))


    def list_virtual_devices(self, device_type):
        if device_type not in ['sinks', 'sources']:
            return

        ret =self.send_command(f'get-vd {device_type}') 
        return json.loads(ret)

    # get sink-input and source-output list
    def list_apps(self, device_type):
        command = f'get-app-list {device_type}'
        try:
            ret_message = json.loads(self.send_command(command))
            return ret_message
        except:
            print('invalid json from server')
            return False
            raise

    # change application device
    def move_app_device(self, app_id, device, stream_type):
        command = f'move-app-device {app_id} {device} {stream_type}'
        return self.send_command(command)

    def get_app_volume(self, app_id, stream_type):
        command = f'get-stream-volume {app_id} {stream_type}'
        return int(self.send_command(command))

    def set_app_volume(self, app_id, vol, stream_type):
        command = f'app-volume {app_id} {vol} {stream_type}'
        return self.send_command(command)

    def set_layout(self, layout):
        if layout == self.config['layout']:
            return

        command = f'set-layout {layout}'
        return self.send_command(command)

    def set_tray(self, state):
        if type(state) == str:
            state = state.lower() == 'true'

        if state == self.config['tray']:
            return

        command = f'set-tray {state}'
        return self.send_command(command)

    def set_cleanup(self, state):
        if type(state) == str:
            state = state.lower() == 'true'

        if state == self.config['cleanup']:
            return

        command = f'set-cleanup {state}'
        return self.send_command(command)

    def close_connection(self):
        self.sock.shutdown(socket.SHUT_RDWR)

    def close_server(self):
        self.send_command('exit')


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
