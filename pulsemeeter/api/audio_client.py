import subprocess
import threading
import logging
import json
import sys
import re

import pulsemeeter.scripts.pmctl as pmctl
from pulsemeeter.ipc.client import Client

LOG = logging.getLogger("generic")


class AudioClient(Client):

    def __init__(self, listen=False, noconfig=False):

        super(AudioClient, self).__init__(listen=listen, noconfig=noconfig)
        self.config = json.loads(self.send_command('get-config', nowait=not listen))
        self.callback_dict = {}
        self.listen_thread = None
        self.exit_flag = False
        self.noconfig = noconfig

        if listen:
            self.start_callbacks()

    def start_callbacks(self):
        # self.stop_listen()
        # self.exit_flag = False
        self.callback_thread = threading.Thread(target=self.handle_callback, args=())
        self.callback_thread.start()

    def stop_callbacks(self):
        self.exit_flag = True
        if self.callback_thread is not None:
            self.callback_thread.join()
        self.callback_thread = None

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

    def handle_callback(self):
        '''
        Handles calling callback functions.
        Only for internal use.
        '''
        while not self.exit_flag:
            msg, sender_id = self.event_queue.get()
            # LOG.debug(event)
            self.assert_config(msg)
            event = msg.split(' ')

            # leave it until model
            if event[0] in ['create-device', 'edit-device']:
                event = msg.split(' ', 3)

            command = event[0]
            args = tuple(event[1:])

            if command in self.callback_dict and (
                    sender_id != self.id or (
                        event[0] in ['remove-device', 'create-device', 'edit-device'])):
                function = self.callback_dict[command]
                function(*args)

            if command == 'exit':
                self.disconnect()

    def verify_device(self, device_type, device_id="0", dev="all"):
        """
        see if device name and device_id is correct
        """

        if dev == 'virtual':
            if device_type not in ['vi', 'b']:
                LOG.error(f'input type {device_type} not found')
                return False

        if dev == 'hardware':
            if device_type not in ['a', 'hi']:
                LOG.error(f'input type {device_type} not found')
                return False

        if dev == 'input':
            if device_type not in ['hi', 'vi']:
                LOG.error(f'input type {device_type} not found')
                return False

        if dev == 'output':
            if device_type not in ['a', 'b']:
                LOG.error(f'output type {device_type} not found')
                return False

        if dev == 'any':
            if device_type not in ['hi', 'vi', 'a', 'b']:
                LOG.error(f'output type {device_type} not found')
                return False

        if not device_id.isdigit():
            LOG.error(f'invalid device index {device_id}')
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

        if self.config[input_type][input_id][f'{output_type}{output_id}']['status'] == state:
            return

        LOG.debug(command)
        return self.send_command(command)

    def create_device(self, device_type, j):
        """
        create a new device (slot)
        """
        if self.verify_device(device_type) is not True:
            return

        command = f"create-device {device_type} {json.dumps(j)}"

        LOG.debug(command)
        return self.send_command(command)

    def remove_device(self, device_type, device_id=-1):
        """
        remove a device (slot)
        """
        if self.verify_device(device_type) is not True:
            return

        command = f"remove-device {device_type} {device_id}"

        LOG.debug(command)
        return self.send_command(command)

    def edit_device(self, device_type, device_id, j):
        """
        edits a device
        """
        if self.verify_device(device_type) is not True:
            return

        command = f"edit-device {device_type} {device_id} {json.dumps(j)}"

        LOG.debug(command)
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
            if not re.match('[+-]?[0-9]+$', vol):
                return 'invalid volume'
            if re.match('^[0-9]+$', vol):
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

    def list(self, device_type, hardware=False, virtual=False, all=False):
        '''
        returns json of hardware devices.
        '''

        devl = pmctl.listobj(device_type)

        # all for for returning the entire json
        if all: return devl

        devices = {}

        h, v = ('a', 'vi') if device_type == 'sinks' else ('hi', 'b')

        devices[h] = []
        devices[v] = []

        for i in devl:
            if 'HARDWARE' in i['flags']:
                devices[h].append(i)
            else:
                devices[v].append(i)

        if hardware is True:
            return devices[h]

        if virtual is True:
            return devices[v]

        return devices

    def get_app_list(self, device_type, id=None):
        return pmctl.get_app_list(device_type, id)

    def set_port_map(self, input_type, input_id, output, port_map):
        port_map = json.dumps(port_map).replace(" ", "")
        command = f'port-map {input_type} {input_id} {output} {port_map}'
        return self.send_command(command)

    def set_auto_ports(self, input_type, input_id, output, status):
        command = f'auto-ports {input_type} {input_id} {output} {status}'
        return self.send_command(command)

    # change application device
    def move_app_device(self, app_id, device, stream_type):
        command = f'move-app-device {app_id} {device} {stream_type}'
        return self.send_command(command)

    def get_app_volume(self, app_id, stream_type):
        return int(pmctl.get_stream_volume(stream_type, app_id))

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

    def set_vumeter(self, state):
        if type(state) == str:
            state = state.lower() == 'true'

        if state == self.config['enable_vumeters']:
            return

        command = f'set-vumeter {state}'
        return self.send_command(command)

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

        self.sub_proc = pmctl.subscribe()

        for stdout_line in iter(self.sub_proc.stdout.readline, ""):
            yield stdout_line

        self.sub_proc.stdout.close()
        return_code = self.sub_proc.wait()
        if return_code:
            raise subprocess.CalledProcessError(return_code, ['pmctl', 'subscribe'])

    def end_subscribe(self):
        if self.sub_proc is not None:
            self.sub_proc.terminate()

    def listen_peak(self, device_name, device_type):
        if device_name == '': return
        dev_type = '0' if device_type == 'vi' or device_type == 'a' else '1'
        command = ['pulse-vumeter', self.name, dev_type]
        sys.stdout.flush()
        self.process = subprocess.Popen(command,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            shell=False,
            encoding='utf-8',
            universal_newlines=False)

        # return piped values

        for stdout_line in iter(self.process.stdout.readline, ""):
            yield stdout_line

    def assert_config(self, msg):
        '''update the config'''
        event = msg.split(' ')
        if event[0] in ['create-device', 'edit-device']:
            event = msg.split(' ', 3)

        command = event[0]
        args = event[1:]

        match command:
            case 'connect':
                input_type = args[0]
                input_id = args[1]
                sink = args[2] + args[3]
                state = args[4].lower() == 'true'
                self.config[input_type][input_id][sink]['status'] = state
                if len(args) > 4:
                    latency = int(args[5])
                    self.config[input_type][input_id][sink]['latency'] = int(latency)

            case 'mute':
                device_type = args[0]
                device_id = args[1]
                state = args[2].lower() == 'true'
                self.config[device_type][device_id]['mute'] = state

            case 'primary':
                device_type = args[0]
                device_id = args[1]
                self.config[device_type][device_id]['primary'] = True

                for dev_id in self.config[device_type]:
                    if dev_id != device_id:
                        self.config[device_type][dev_id]['primary'] = False

            case 'volume':
                device_type = args[0]
                device_id = args[1]
                vol = int(args[2])
                self.config[device_type][device_id]['vol'] = vol

            case 'port-map':
                input_type = args[0]
                input_id = args[1]
                output = args[2]
                port_map = args[3]
                self.config[input_type][input_id][output]['port_map'] = json.loads(port_map)

            case 'auto-ports':
                input_type = args[0]
                input_id = args[1]
                output = args[2]
                status = args[3] == 'true'
                self.config[input_type][input_id][output]['auto_ports'] = status

            case 'rename':
                device_type = args[0]
                device_id = args[1]
                name = args[2]
                if name == 'None':
                    name = ''
                self.config[device_type][device_id]['name'] = name

            case 'change-hd':
                device_type = args[0]
                device_id = args[1]
                name = args[2]
                # channel_map = args[3]
                channels = args[3]
                if name == 'None':
                    name = ''

                if channels != 'None':
                    self.config[device_type][device_id]['channels'] = int(channels)

                # if channel_map != 'None':
                    # self.config[device_type][device_id]['channel_map'] = channel_map

                self.config[device_type][device_id]['name'] = name

            case 'eq':
                device_type = args[0]
                device_id = args[1]
                state = args[2].lower() == 'true'
                self.config[device_type][device_id]['use_eq'] = state

                if len(args) > 3:
                    control = args[3]
                    self.config[device_type][device_id]['eq_control'] = control

            case 'layout':
                layout = args[0]
                self.config['layout'] = layout

            case 'cleanup':
                state = args[0]
                self.config['cleanup'] = state.lower() == 'true'

            case 'vumeter':
                state = args[0]
                self.config['enable_vumeters'] = state.lower() == 'true'

            case 'tray':
                state = args[0]
                self.config['tray'] = state.lower() == 'true'

            case 'rnnoise':
                device_id = args[0]
                state = args[1].lower() == 'true'
                self.config['hi'][device_id]['use_rnnoise'] = state

                if len(args) > 2:
                    control = args[2]
                    self.config['hi'][device_id]['rnnoise_control'] = control

            case 'create-device':
                device_type = args[0]
                device_id = args[1]
                self.config[device_type][device_id] = json.loads(args[2])

            case 'remove-device':
                device_type = args[0]
                device_id = args[1]
                del self.config[device_type][device_id]

            case 'edit-device':
                device_type = args[0]
                device_id = args[1]
                self.config[device_type][device_id] = json.loads(args[2])
