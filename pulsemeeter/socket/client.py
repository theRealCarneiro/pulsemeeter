from ..settings import SOCK_FILE, __version__
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
        self.VERSION = __version__

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
        '''
        starts the listening thread.
        (starts if listen=True in Client class)
        '''
        self.stop_listen()
        self.listen_thread = threading.Thread(target=self.listen, args=(print_event,))
        self.listen_thread.start()

    # stop listen thread
    def stop_listen(self):
        '''
        stops the listening thread if there is one.
        '''
        if self.listen_thread is not None: 
            self.exit_flag = True
            self.listen_thread.join()
    
    def send_command(self, command, nowait=False):
        '''
        Send command manually to server.
        (only for advanced users)
        '''
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

                
        except Exception:
            print('closing socket')
            self.sock.close()
            raise


    def listen(self, print_event=True):
        '''
        Starts to listen to server events. (gets called by start_listen)
        '''
        while True:
            try:
                if self.exit_flag is True: break
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
                try:
                    sender_id = int(sender_id)
                except ValueError:
                    sender_id = None

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

            except Exception:
                raise


    # set a callback function to a command
    def set_callback_function(self, command, function):
        '''
        Set a callback so Pulsemeeter can call the function you specified if values change.

        available commands:
        - "connect":        ARGS(input_type, input_id, output_type, output_id, status, latency)
        - "mute":           ARGS(device_type, device_id, state)
        - "primary":        ARGS(device_type, device_id)
        - "rnnoise":        ARGS(input_id, status, control)
        - "eq":             ARGS(output_type, output_id, status, control)
        - "volume":         ARGS(device_type, device_id, val)
        - "primary":        ARGS(device_type, device_id, run_command)
        - "change-hd":      ARGS(output_type, output_id, name)
        - "device-new":     ARGS(index, facility)
        - "device-remove":  ARGS(index, facility)
        - "exit":           ARGS()
        '''
        self.callback_dict[command] = function
    
    def handle_callback(self, event):
        '''
        Handles calling callback functions.
        Only for internal use.
        '''
        command = event.split(' ')
        if command[0] not in self.callback_dict:
            return
        
        function = self.callback_dict[command[0]]
        args = tuple(command[1:])
        function(*args)

    def assert_config(self, event):
        '''update the config'''
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
        '''
        Connect two devices.
        if state is empty, it gets toggled.
        latency can be empty.

        input → output
        '''
        if (not self.verify_device(input_type, input_id, 'input') or
                not self.verify_device(output_type, output_id, 'output')):
            return
           
        command = f'connect {input_type} {input_id} {output_type} {output_id}'
        if state is not None: command += f' {state}'
        if latency is not None: command += f' {latency}'
        
        if self.config[input_type][input_id][f'{output_type}{output_id}'] == state:
            return

        print(command)
        return self.send_command(command)


    def mute(self, device_type, device_id, state=None):
        '''
        Mute/unmute a device.
        When the state is empty, it gets toggled.
        '''
        if not self.verify_device(device_type, device_id, 'any'):
            return

        command = f'mute {device_type} {device_id}'
        if state is not None: command += f' {state}'

        # print('config: ', self.config[device_type][device_id]['mute'], 'new: ', state)
        if self.config[device_type][device_id]['mute'] == state:
            return
        return self.send_command(command)


    def primary(self, device_type, device_id):
        '''
        Select a primary device.
        device_type: virtual devices ("vi", "b")
        '''
        if not self.verify_device(device_type, device_id, 'any'):
            return

        command = f'primary {device_type} {device_id}'

        if self.config[device_type][device_id]['primary'] is True:
            return
        return self.send_command(command)


    def rnnoise(self, input_id, state=None, control=None, latency=None):
        '''
        Turn rnnoise on or off and change values.
        state: boolean or "set"
        device_type: hardware_input ("hi")

        if state is "set":
            control: <value>
            latency (can be empty): <value>
        '''
        if not input_id.isdigit():
            return 'invalid device index'

        command = f'rnnoise {input_id}'
        if state is not None: command += f' {state}'
        if control and latency: command += f' {control} {latency}'

        if (self.config['hi'][input_id]['use_rnnoise'] == state or
                self.config['hi'][input_id]['rnnoise_control'] == control):
            return
        return self.send_command(command)


    def eq(self, output_type, output_id, state=None, control=None):
        '''
        Turn eq on or off and change values.
        device_type: output ("a", "b")
        state: boolean or "set"

        if state is "set":
            control: "<value1>,<value2>,<value3>,<...>"
        '''

        if not self.verify_device(output_type, output_id, 'output'):
            return

        command = f'eq {output_type} {output_id}'

        if control is not None and state == 'set':
            command += f' set {control}'

        elif control is None and state is not None:
            command += f' {state}'

        elif control is not None and state != 'set':
            return

        if (self.config[output_type][output_id]['use_eq'] == state or
                self.config[output_type][output_id]['eq_control'] == control):
            return
        return self.send_command(command)


    def volume(self, device_type, device_id, vol):
        '''
        change volume of a device
        vol: +<value> | -<value> | <value>
        '''
        if not self.verify_device(device_type, device_id, 'any'):
            return
        if type(vol) == str:
            if not re.match('[+-]?[1-9]+$', vol):
                return 'invalid volume'
            if re.match('^[1-9]+$', vol):
                if self.config[device_type][device_id]['vol'] == int(vol):
                    return

        command = f'volume {device_type} {device_id} {vol}'
        # print(command)

        return self.send_command(command)


    def rename(self, device_type, device_id, name):
        '''rename a virtual input'''
        if not self.verify_device(device_type, device_id, 'virtual'):
            return

        command = f'rename {device_type} {device_id} {name}'
        if self.config[device_type][device_id]['name'] == name:
            return
        return self.send_command(command)


    def change_hardware_device(self, device_type, device_id, device):
        '''
        Change the device of an input/output.

        Disclaimer:
        For this you need to specify the pulseaudio device name not the short name shown in the UI.
        '''
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
        '''
        returns json of hardware devices.
        '''
        if device_type not in ['sinks', 'sources']:
            return

        ret = self.send_command(f'get-hd {device_type}')
        # return is 'empty' if there are no devices
        if ret != 'empty':
            return json.loads(ret)


    def list_virtual_devices(self, device_type):
        if device_type not in ['sinks', 'sources']:
            return

        ret =self.send_command(f'get-vd {device_type}') 
        return json.loads(ret)

    # get sink-input and source-output list
    def list_apps(self, device_type):
        command = f'get-app-list {device_type}'
        try:
            ret_message = self.send_command(command)
            return json.loads(ret_message)
        except Exception:
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
        '''
        Changes the layout of the UI.
        '''
        if layout == self.config['layout']:
            return

        command = f'set-layout {layout}'
        return self.send_command(command)

    def set_tray(self, state):
        '''
        Specifies if the tray should be used.
        '''
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
        '''
        Closes the Pulsemeeter server (also closes UI).
        '''
        self.send_command('exit')

    def subscribe(self):
        '''
        Listen to Pulseaudio event.

        Disclaimer:
        Pulsemeeter already includes a Pulseaudio event listener and you can use the callback functions for that.
        '''
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
        if self.sub_proc is not None:
            self.sub_proc.terminate()
