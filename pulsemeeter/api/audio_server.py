import subprocess
import traceback
import threading
import pulsectl
import logging
import signal
import shutil
import json
import sys
import re
import os

from pulsemeeter.settings import CONFIG_DIR, CONFIG_FILE, ORIG_CONFIG_FILE, __version__
from pulsemeeter.scripts import pmctl
from pulsemeeter.api.pulse_socket import PulseSocket
from pulsemeeter.ipc.server import Server


LOG = logging.getLogger("generic")


class AudioServer(Server):

    def __init__(self, init_server=True):

        # check if pulseaudio is running
        try:
            subprocess.check_call('pmctl')
        except subprocess.CalledProcessError:
            sys.exit(1)

        # check what audio server the user is running
        self.audio_server = 'Pulseaudio' if shutil.which('pulseaudio') else 'Pipewire'

        # read config file
        self.read_config()

        # create a dict with the commands and functions
        self.create_command_dict()

        # call server __init__
        super().__init__(init_server)

        self.exit_flag = False
        if init_server: self.start_server()

    def start_server(self, daemon=False):

        # start audio devices and connections
        self.init_audio()

        # start pulsectl client
        self.pulsectl = pulsectl.Pulse('pulsemeeter')
        self.pulse_socket = PulseSocket(self.command_queue, self.config)
        self.pulse_socket.start_listener()

        self.start_query()
        self.main_loop_thread = threading.Thread(target=self.main_loop)
        self.main_loop_thread.start()

        # Register signal handlers
        if daemon:
            signal.signal(signal.SIGINT, self.stop_server)
            signal.signal(signal.SIGTERM, self.stop_server)

    def main_loop(self):

        # Make sure that even in the event of an error, cleanup still happens
        try:
            # Listen for commands
            while not self.exit_flag:
                message_type, sender_id, command = self.command_queue.get()

                match message_type:

                    case 'command':
                        ret_message, notify_all = self.handle_command(command)

                    case 'audio_server':
                        ret_message, notify_all = self.handle_pulsectl(command), True
                        if not ret_message:
                            continue

                    case 'exit':
                        ret_message, notify_all = 'exit', True
                        self.exit_flag = True

                self.send_message(ret_message, sender_id, notify_all)

        finally:

            # Set the exit flag and wait for the listener thread to timeout
            LOG.info('sending exit signal to listener threads, they should exit within a few seconds...')
            self.exit_flag = True

            try:
                self.pulse_socket.stop_listener()
            except Exception:
                LOG.error('Could not close pulse listener')
                LOG.error(traceback.format_exc())

            # Call any code to clean up virtual devices or similar
            self.save_config(buffer=False)
            if self.config['cleanup']:
                self.cleanup()

    def handle_pulsectl(self, event):
        evt = event.split(' ')

        if len(evt) > 3:
            return event

        command, id, device_type = evt

        if device_type not in ['sink_input', 'source_output']:
            return None

        device_type = device_type.replace('_', '-') + 's'

        if (command == 'device-plugged-in'):

            # if list len is 0, it will just skip to return None
            app_list = pmctl.get_app_list(device_type, id)
            if len(app_list) == 0: return None

            id, label, icon, volume, device = app_list[0]
            return f'{command} {device_type} {id} {label} {icon} {volume} {device}'

        return f'{command} {id} {device_type}'

    # handles incoming commands
    def handle_command(self, data):
        decoded_data = data.decode()
        msg = tuple(decoded_data.split(' '))

        # special case for now, when there's a model ill remove this
        if msg[0] == 'create-device':
            msg = decoded_data.split(' ', 2)
        if msg[0] == 'edit-device':
            msg = decoded_data.split(' ', 3)

        str_args = re.sub(r'^.*?\ ', '', decoded_data)
        command = msg[0]
        if len(msg) > 1:
            args = msg[1:]
        else:
            args = ()

        if command == 'exit':
            return 'exit', True

        try:

            # check if args are valid
            if not re.match(self.commands[command]['regex'], str_args):
                LOG.error("invalid arguments")
                return None

            LOG.debug(command)

            function = self.commands[command]['function']
            notify = self.commands[command]['notify']
            save_to_config = self.commands[command]['save_config']
            ret_msg = function(*args)
            if save_to_config: self.save_config()

            if not ret_msg:
                LOG.error("internal errror, command return not valid")
                return None

            return (ret_msg, notify)

        # except TypeError:
            # LOG.error('invalid number of arguments')
            # return None

        except KeyError as ex:
            LOG.error(f"command \'{command}\' not found {ex}")
            return None

    def init_audio(self):
        command = ''
        command += self.start_sinks()
        command += self.start_sources()
        command += self.start_eqs()
        command += self.start_rnnoise()
        command += self.start_connections()
        command += self.start_primarys()

        os.popen(command)

    # get the correct device to connect to, e.g. include .monitor in a
    # virtual sink name, or use a ladspa sink for a hardware source
    def get_correct_device(self, index, conn_type):

        name = self.config[index[0]][index[1]]['name']

        # for virtual inputs
        if index[0] == 'vi':

            if conn_type == "source" and self.audio_server != 'Pipewire':
                name += ".monitor"

        # for hardware inputs
        if index[0] == 'hi':

            # return ladspa sink with rnnoise plugin
            if self.config[index[0]][index[1]]['rnnoise'] is True:
                name = f'{index[0]}{index[1]}_rnnoise'

                if self.audio_server != 'Pipewire':
                    name += ".monitor"

        # for hardware outputs
        if index[0] == 'a':

            # return ladspa sink with eq plugin
            if self.config[index[0]][index[1]]['eq'] is True:
                name = f'{index[0]}{index[1]}_eq'

        # virtual outputs need an aux sink to route audio into it
        if index[0] == 'b':

            # return ladspa sink with eq plugin
            if self.config[index[0]][index[1]]['eq'] is True:
                name = f'{index[0]}{index[1]}_eq'
                if conn_type == 'source' and self.audio_server != 'Pipewire':
                    name += '.monitor'

            # return aux sink
            else:
                if self.audio_server != 'Pipewire':
                    name += '_sink'
                    if conn_type == 'source':
                        name += '.monitor'

        return name

    # init virtual inputs
    def start_sinks(self):
        command = ''
        sink_list = cmd("pactl list sinks short")

        # itarate between all devices
        for device_id in self.config['vi']:
            device_config = self.config['vi'][device_id]

            # if device does not have a name
            if device_config['name'] != '':

                # external key means that the user is responsible for managing that sink
                if device_config['external'] is False:

                    # if device is available on pulse
                    if not re.search(device_config['name'], sink_list):

                        # set sink properties
                        sink = device_config['name']
                        channels = device_config['channels']
                        command += pmctl.init('sink', sink, channels)

        LOG.debug(command)
        return command

    # init virtual outputs
    def start_sources(self):
        command = ''
        source_list = cmd("pactl list sources short")
        # itarate between all devices
        for device_id in self.config['b']:
            device_config = self.config['b'][device_id]

            # if device does not have a name
            if device_config['name'] != '':

                # if device is available on pulse
                if not re.search(device_config['name'], source_list):

                    # set source properties
                    source = device_config['name']
                    channels = device_config['channels']
                    command += pmctl.init('source', source, channels)

        LOG.debug(command)
        return command

    # creates all ladspa sinks for eq plugin
    def start_eqs(self):
        command = ''
        for output_type in ['a', 'b']:
            for output_id in self.config[output_type]:

                # check if device uses an eq
                if self.config[output_type][output_id]['eq'] is True:

                    # create eq sink
                    command += self.eq(output_type, output_id, status=True,
                            reconnect=False, change_config=False, run_command=False)

        return command

    # creates all ladspa sinks for rnnoise plugin
    def start_rnnoise(self):
        command = ''
        input_type = 'hi'
        for input_id in self.config[input_type]:

            # check if device uses rnnoise
            if self.config[input_type][input_id]['rnnoise'] is True:

                # create rnnoise sink
                command += self.rnnoise(input_id, status=True,
                        reconnect=False, change_config=False, run_command=False)
        return command

    # create connections
    def start_connections(self):
        command = ''
        for input_type in ['vi', 'hi']:
            for input_id in self.config[input_type]:
                command += self.reconnect(input_type, input_id, run_command=False)

        return command

    # set all primary devices
    def start_primarys(self):
        command = ''
        for device_type in ['vi', 'b']:
            for device_id in self.config[device_type]:
                if self.config[device_type][device_id]['primary'] is True:
                    command += self.set_primary(device_type, device_id, run_command=False)

        LOG.debug(command)
        return command

    # def start_hardware_devices(self):
        # inputs = pmctl.list('sources')
        # outputs = pmctl.list('sinks')
        # names = []
        # for device_type in ['hi', 'a']:
            # for device_id in self.config[device_type]:
                # names.append()

    def stop_connections(self, run_command=True):
        command = ''
        for input_type in ['vi', 'hi']:
            for input_id in self.config[input_type]:
                command += self.reconnect(input_type, input_id, status=False, run_command=False)
        if run_command: os.popen(command)
        return command

    def cleanup(self):
        # remove connections
        command = self.stop_connections(run_command=False)

        # remove rnnoise
        for hi_id in self.config['hi']:
            hi_config = self.config['hi'][hi_id]
            if hi_config['rnnoise']:
                command += self.rnnoise(hi_id, status=False,
                        reconnect=False, change_config=False, run_command=False)

        # remove eqs
        for output_type in ['a', 'b']:
            for output_id in self.config[output_type]:
                output_config = self.config[output_type][output_id]
                if output_config['eq']:
                    command += self.eq(output_type, output_id, status=False,
                            reconnect=False, change_config=False, run_command=False)

        # remove virtual devices
        for device_type in ['b', 'vi']:
            for device_id in self.config[device_type]:
                command += self.toggle_virtual_device(device_type, device_id, status=False, disconnect=False, run_command=False)

        os.popen(command)

    # creates a ladspa sink with rnnoise for a given hardware input
    def rnnoise(self, input_id, status=None, control=None, latency=None, reconnect=True,
            change_config=True, run_command=True, ladspa_sink=None):

        # get control values
        input_type = 'hi'
        source_config = self.config[input_type][input_id]
        source = source_config['name']

        if latency is None:
            if self.audio_server == 'Pipewire':
                pmap = source_config['selected_channels']
                chann_lat = ''
                for i in range(len(pmap)):
                    if pmap[i] is True:
                        chann_lat += f'{i}:0 '
                chann_lat = chann_lat[:-1]
            else:
                chann_lat = source_config['rnnoise_latency']

        if control is None:
            control = source_config['rnnoise_control']
            control == 95 if control == '' else int(control)

        # set name for the plugin sink
        ladspa_sink = f'{input_type}{input_id}_rnnoise'

        # status = None -> toggle state
        if status is None:
            status = not source_config['rnnoise']

        # if only changing control
        elif status == 'set':
            status = source_config['rnnoise']

        else:
            status = str2bool(status)

        # label, plugin = 'noisetorch', 'rnnoise_ladspa'
        # label, plugin = 'noise_suppressor_mono', 'librnnoise_ladspa'

        # create ladspa sink
        # command = pmctl.ladspa(status, 'source', source, ladspa_sink, label, plugin, control, chann_lat)
        command = pmctl.rnnoise(status, source, ladspa_sink, control, chann_lat)

        # recreates all loopbacks from the device
        if reconnect:
            command += self.reconnect('hi', input_id, False, run_command=False)

        if change_config:
            if status != 'set': source_config['rnnoise'] = status
            source_config['rnnoise_control'] = int(control)
            if self.audio_server != 'Pipewire':
                source_config['rnnoise_latency'] = chann_lat

        if reconnect:
            command += self.reconnect('hi', input_id, True, run_command=False)

        LOG.debug(command)
        if run_command is True:
            LOG.debug(command)
            os.popen(command)
            return f'rnnoise {input_id} {status} {control}'
        return command

    # creates a ladspa sink with eq plugin for a given output
    def eq(self, output_type, output_id, status=None, control=None, ladspa_sink=None,
            reconnect=True, change_config=True, run_command=True):

        # get information about the device
        sink_config = self.config[output_type][output_id]
        master = self.get_correct_device([output_type, output_id], 'sink')

        # set name for the plugin sink
        if ladspa_sink is None: ladspa_sink = f'{output_type}{output_id}_eq'

        # control values for the eq
        if control is None:
            control = sink_config['eq_control']
            control = '0,0,0,0,0,0,0,0,0,0,0,0,0,0,0' if control == '' else control

        # toggle on/off
        if status is None:
            status = not sink_config['eq']
            conn_status = status

        # if only changing the control
        elif status == 'set':
            conn_status = sink_config['eq']

        else:
            conn_status = str2bool(status)

        if status == sink_config['eq'] is False:
            return f'eq {output_type} {output_id} {conn_status} {control}'

        # create ladspa sink
        command = pmctl.ladspa(status, 'sink', master, ladspa_sink, 'mbeq', 'mbeq_1197', control, '')

        if reconnect:
            command += self.reconnect(output_type, output_id, False, run_command=False)

        if change_config:
            if status != 'set': sink_config['eq'] = conn_status
            sink_config['eq_control'] = control

        # recreates all loopbacks from the device
        if reconnect:
            command += self.reconnect(output_type, output_id, True, run_command=False)

        if run_command:
            LOG.debug(command)
            os.popen(command)
            return f'eq {output_type} {output_id} {status} {control}'
        return command

    # recreates connections fom a device, does not affect config
    def reconnect(self, device_type, device_id, status=True, run_command=True):
        command = ''
        sinks = ['a', 'b']
        sources = ['hi', 'vi']

        input_type = ''
        input_id = ''
        output_type = ''
        output_id = ''

        # if trying to reset a sink
        if device_type in sinks:
            device_types = sources
            output_type = device_type
            output_id = device_id

        # if trying to reset a source
        elif device_type in sources:
            device_types = sinks
            input_type = device_type
            input_id = device_id

        else: return 'invalid device'

        # reseting the values here just to be clear that they're different now
        device_type = ''
        device_id = ''

        # itarate between all output devices
        for device_type in device_types:
            for device_id in self.config[device_type]:

                # if trying to reset a sink
                if device_type in sources:
                    input_type = device_type
                    input_id = device_id

                # if trying to reset a source
                else:
                    output_type = device_type
                    output_id = device_id

                sink = output_type + output_id
                # connection status check
                if self.config[input_type][input_id][sink]['status'] is True:
                    command += self.connect(input_type, input_id, output_type, output_id,
                            status=status, change_state=False, run_command=False, init=True)

        if run_command:
            LOG.debug(command)
            os.popen(command)
        return command

    # connects an input to an output
    def connect(self, input_type, input_id, output_type, output_id,
            status=None, latency=None, run_command=True, change_state=True, init=False):

        source_config = self.config[input_type][input_id]
        sink_config = self.config[output_type][output_id]
        cur_conn_status = source_config[output_type + output_id]['status']

        # toggle connection status
        if status is None:
            status = not cur_conn_status
        else:
            status = str2bool(status)

        # if trying to set the same state
        if (init is False and latency is None) and ((cur_conn_status and status) or
                (not cur_conn_status and not status)):
            return ''

        # if true, will change the config status
        if change_state is True:
            source_config[output_type + output_id]['status'] = status

        # get name and latency of devices
        source = self.get_correct_device([input_type, input_id], 'source')
        sink = self.get_correct_device([output_type, output_id], 'sink')
        if latency is None:
            latency = source_config[f'{output_type}{output_id}']['latency']
        else:
            source_config[f'{output_type}{output_id}']['latency'] = int(latency)

        # check if device exists
        # if (source == '' or sink == ''):
        #    return ''

        device_exists = source != '' and sink != ''

        # port map
        port_map = None
        if self.audio_server == 'Pipewire':

            # get selected ports
            if input_type == 'hi' and 'selected_channels' in source_config:
                if source_config['rnnoise']:
                    iselports = [0]
                iselports = source_config['selected_channels']
                iselports = [i for i in range(len(iselports)) if iselports[i] is True]
            else:
                iselports = list(range(source_config['channels']))

            if output_type == 'a' and 'selected_channels' in sink_config:
                oselports = sink_config['selected_channels']
                oselports = [i for i in range(len(oselports)) if oselports[i] is True]
            else:
                oselports = list(range(sink_config['channels']))

            # manual port mapping
            if source_config[f'{output_type}{output_id}']['auto_ports'] is False:
                port_map = source_config[f'{output_type}{output_id}']['port_map']

                ports = ''
                n = len(port_map) if input_type != 'hi' else 1
                for i in range(n):
                    for o in port_map[i]:
                        ports += f'{iselports[i]}:{o} '
                ports = ports[:-1]

            # auto ports
            else:
                try:
                    input_port_size = source_config['selected_channels'].count(True)
                except Exception:
                    input_port_size = source_config['channels']

                try:
                    output_port_size = sink_config['selected_channels'].count(True)
                except Exception:
                    output_port_size = sink_config['channels']

                ports = ''
                cnum = min(input_port_size, output_port_size)

                for i in range(cnum):
                    ports += f'{iselports[i]}:{oselports[i]} '

        if device_exists:
            command = pmctl.connect(source, sink, status,
                                    latency=latency if self.audio_server != 'Pipewire' else None,
                                    port_map=ports, run_command=False)
        else:
            command = ''

        if run_command is True:
            if device_exists:
                LOG.debug(command)
                os.popen(command)
            return f'connect {input_type} {input_id} {output_type} {output_id} {status} {latency}'
        return command

    def change_hardware_device(self, output_type, output_id, name):
        if name in ['None', None]: name = ''
        device_config = self.config[output_type][output_id]
        # channel_map = None
        channels = None

        # if device its not an empty name
        if device_config['name'] != '':
            self.toggle_hardware_device(output_type, output_id, False)

        if name != '':
            device = pmctl.list('sinks' if output_type == 'a' else 'sources', name)

            if 'properties' in device:
                # channel_map = device['properties']['audio.position']
                if 'audio.channels' in device['properties']:
                    channels = int(device['properties']['audio.channels'])
                else:
                    channels = device['channel_map'].count(',') + 1

                device_config['channels'] = channels
                device_config['selected_channels'] = [True for _ in range(channels)]
        device_config['name'] = name

        # if chosen device is not an empty name
        if name != '':
            self.toggle_hardware_device(output_type, output_id, True)
        else:
            name = None

        return f'change-hd {output_type} {output_id} {name} {channels}'

    def set_port_map(self, input_type, input_id, output, port_map):
        input_config = self.config[input_type][input_id]
        input_config[output]['port_map'] = json.loads(port_map)
        return f'port-map {input_type} {input_id} {output} {port_map}'

    def set_auto_ports(self, input_type, input_id, output, status):
        status = str2bool(status)
        input_config = self.config[input_type][input_id]
        input_config[output]['auto_ports'] = status
        return f'auto-ports {input_type} {input_id} {output} {status}'

    # this will cleanup a hardware device and will not affect the config
    # useful when e.g. changing the device used in a hardware input/output strip
    def toggle_hardware_device(self, device_type, device_id, status, run_command=True):
        device_config = self.config[device_type][device_id]
        command = ''
        status = str2bool(status)

        # check what type of device, then disable plugins
        if device_type == 'a':
            device_list = ['hi', 'vi']

            if status and device_config['eq']:
                command += self.eq(device_type, device_id, status=True,
                        reconnect=False, change_config=False, run_command=False)

        else:
            device_list = ['a', 'b']

            if status and device_type == 'hi' and device_config['rnnoise']:
                command += self.rnnoise(device_id, status=True,
                        reconnect=False, change_config=False, run_command=False)

        # set connections
        for target_type in device_list:
            for target_num in self.config[target_type]:

                sink = ''
                if device_type == 'a':
                    input_type = target_type
                    input_id = target_num
                    output_type = device_type
                    output_id = device_id
                    sink = f'{device_type}{device_id}'
                else:
                    input_type = device_type
                    input_id = device_id
                    output_type = target_type
                    output_id = target_num
                    sink = f'{output_type}{output_id}'

                if self.config[input_type][input_id][sink]['status'] is True:
                    command += self.connect(input_type, input_id, output_type, output_id,
                            status=status, run_command=False, change_state=False, init=True)

        if not status:
            if device_type == 'a' and device_config['eq']:
                command += self.eq(device_type, device_id, status=False,
                        reconnect=False, change_config=False, run_command=False)

            elif device_type == 'hi' and device_config['rnnoise']:
                command += self.rnnoise(device_id, status=False,
                        reconnect=False, change_config=False, run_command=False)

        LOG.debug(command)
        if run_command: os.popen(command)
        return command

    def toggle_virtual_device(self, device_type, device_id, status=False, disconnect=True, run_command=True):
        command = ''
        device_config = self.config[device_type][device_id]

        if device_config.get('external') is True:
            return ''

        name = device_config["name"]
        if name == '': return ''
        status = str2bool(status)
        conn_type = 'sink' if device_type == 'vi' else 'source'

        if status:
            command += pmctl.init(conn_type, name)
            if device_config['primary']:
                command += self.set_primary(device_type, device_id, run_command=False)

        if disconnect:
            command += self.reconnect(device_type, device_id, status=status, run_command=False)

        if not status:
            command += pmctl.remove(name)

        LOG.debug(command)
        if run_command: os.popen(command)
        return command

    # removes a device, then creates another one with the new name
    def rename(self, device_type, device_id, new_name):
        device_config = self.config[device_type][device_id]
        command = ''
        old_name = device_config['name']

        # if new_name == old_name:
            # return False

        if old_name != '':
            command += self.toggle_virtual_device(device_type, device_id, status=False,
                    run_command=False)

        if new_name != '':
            device_config['name'] = new_name
            command += self.toggle_virtual_device(device_type, device_id, status=True,
                    run_command=False)

            os.popen(command)

        return f'rename {device_type} {device_id} {new_name}'

    def mute(self, device_type, device_id, state=None, run_command=True):
        device_config = self.config[device_type][device_id]
        name = device_config['name']
        if name == '': return

        # set device type
        device = 'sink' if device_type in ('a', 'vi') else 'source'

        # if a state is None, toggle it
        if state is None:
            state = not device_config['mute']
        else:
            state = str2bool(state)

        # save setting
        device_config['mute'] = state

        conn_status = 1 if state else 0
        command = pmctl.mute(device, name, conn_status)

        if run_command:
            LOG.debug(command)
            os.popen(command)
            return f'mute {device_type} {device_id} {state}'
        return command

    # create a new device (slot)
    def create_device(self, device_type, j):

        j = json.loads(j)
        # get current highest device
        if len(self.config[f"{device_type}"]) > 0:
            highest_number = max(self.config[f"{device_type}"], key=int)
        else:
            highest_number = 0

        # get the right number for the device
        device_number = int(highest_number) + 1

        self.config[device_type][f"{device_number}"] = {}
        new_device = self.config[device_type][f"{device_number}"]

        # insert standard device config here
        # I let it so long cause it kind of represents the json
        # maybe we could also just create a json for "standard devices" which could get copied
        if device_type == "hi":
            new_device["name"] = j['device']
            new_device["nick"] = j['nick']
            new_device["description"] = j['description']
            new_device["channels"] = j['channels']
            new_device["selected_channels"] = j['selected_channels']
            new_device["vol"] = 100
            new_device["mute"] = False
            new_device["jack"] = False
            new_device["rnnoise"] = False
            new_device["rnnoise_name"] = ""
            new_device["rnnoise_control"] = 95
            new_device["rnnoise_latency"] = 200
            new_device["channels"] = 1

        elif device_type == "a":
            new_device["name"] = j['device']
            new_device["description"] = j['description']
            new_device["nick"] = j['nick']
            new_device["channels"] = j['channels']
            new_device["selected_channels"] = j['selected_channels']
            new_device["vol"] = 100
            new_device["mute"] = False
            new_device["eq_control"] = ""
            new_device["eq_name"] = ""
            new_device["eq"] = False
            new_device["channels"] = 2

        elif device_type == "vi":
            new_device["name"] = j['name']
            new_device["primary"] = False
            new_device["external"] = j['external']
            new_device["mute"] = False
            new_device["vol"] = 100
            new_device["channels"] = 2

        elif device_type == "b":
            new_device["name"] = j['name']
            new_device["external"] = j['external']
            new_device["primary"] = False
            new_device["vol"] = 100
            new_device["mute"] = False
            new_device["eq_control"] = ""
            new_device["eq_name"] = ""
            new_device["eq"] = False
            new_device["channels"] = 1
            new_device["channel_map"] = "1"

        # generate connections for THIS device
        if device_type in ("vi", "hi"):
            for output_type in ("a", "b"):
                for output_id in self.config[output_type]:
                    # create device
                    new_device[f"{output_type}{output_id}"] = {}
                    # add new values
                    p = new_device[f"{output_type}{output_id}"]
                    p["status"] = False
                    p["latency"] = 200
                    p["auto_ports"] = True
                    p["port_map"] = []

        # update connections FOR EVERY device
        if device_type in ("a", "b"):
            # update connections for each device
            if device_type == "a":
                new_port = f"a{device_number}"
            else:
                new_port = f"b{device_number}"

            for category in (self.config["vi"], self.config["hi"]):
                for device in category:
                    category[device][new_port] = {}
                    # add new values
                    p = category[device][new_port]
                    p["status"] = False
                    p["latency"] = 200
                    p["auto_ports"] = True
                    p["port_map"] = []

        device_id = f'{device_number}'
        if device_type in ['vi', 'b']:
            self.toggle_virtual_device(device_type, device_id, status=True)

        j = json.dumps(self.config[device_type][device_id])
        return f"create-device {device_type} {device_number} {j}"

    # remove a device (slot)
    # use -1 as device id to delete the last one
    def remove_device(self, device_type, device_id):

        # delete the device with the highest num
        if device_id == -1:
            highest_num = max(self.config[device_type], key=int)
            del self.config[device_type][f"{highest_num}"]
            return f"remove-device {device_type} {highest_num}"

        if device_type in ['vi', 'b']:
            self.toggle_virtual_device(device_type, device_id, status=False)

        # delete the specified device
        del self.config[device_type][f"{device_id}"]
        return f"remove-device {device_type} {device_id}"

    def edit_device(self, device_type, device_id, j):
        device_config = self.config[device_type][device_id]

        j = json.loads(j)
        if device_type in ['a', 'hi']:

            # disable old device
            command = self.toggle_hardware_device(device_type, device_id, False,
                                                  run_command=False)
            device_config['nick'] = j['nick']
            device_config['name'] = j['device']
            device_config['description'] = j['description']
            device_config['channels'] = j['channels']
            device_config['selected_channels'] = j['selected_channels']
            command += self.toggle_hardware_device(device_type, device_id, True,
                                                  run_command=False)
        else:

            command = self.toggle_virtual_device(device_type, device_id, status=False,
                                                 run_command=False)
            device_config['name'] = j['name']
            device_config['channels'] = j['channels']
            device_config['external'] = j['external']
            command += self.toggle_virtual_device(device_type, device_id, status=True,
                                                 run_command=False)

        os.popen(command)
        return f'edit-device {device_type} {device_id} {json.dumps(device_config, ensure_ascii=False)}'

    # set a device as primary (only vi and b)
    def set_primary(self, device_type, device_id, run_command=True):
        name = self.config[device_type][device_id]['name']
        for i in self.config[device_type]:
            self.config[device_type][i]['primary'] = False if i != device_id else True

        device = 'sink' if device_type == 'vi' else 'source'
        command = pmctl.set_primary(device, name)
        if run_command:
            os.popen(command)
            return f'primary {device_type} {device_id}'
        return command

    def volume(self, device_type, device_id, val):
        device_config = self.config[device_type][device_id]

        # if volume is a string, convert it to integer
        if type(val) == str:

            # check if is an absolute number or + and -
            if val.isdigit():
                val = int(val)

            # if not an absolute number, add it to current volume
            else:
                val = device_config['vol'] + int(val)

        # limit volume at 153
        if val > 153:
            val = 153

        # limit volume at 0
        elif val < 0:
            val = 0

        device_config['vol'] = val
        name = device_config['name']

        # get device info from pulsectl
        if device_type in ['a', 'vi']:
            device = self.pulse_socket.pulsectl.get_sink_by_name(name)
        else:
            device = self.pulse_socket.pulsectl.get_source_by_name(name)

        # set the volume
        volume = device.volume

        # set by channel
        nchan = len(device.volume.values)
        vollist = device.volume.values
        v = []
        if device_type in ['a', 'hi']:
            selected_channels = device_config['selected_channels']
            for c in range(nchan):
                v.append(val / 100 if selected_channels[c] is True else vollist[c])
            volume = pulsectl.PulseVolumeInfo(v)
        else:
            volume.value_flat = val / 100

        # volume.value_flat = val / 100
        self.pulse_socket.pulsectl.volume_set(device, volume)
        return f'volume {device_type} {device_id} {val}'

    def device_plugged_in(self, index, facility):
        if index != 'None' and facility != 'None':
            return f'device-plugged-in {index} {facility}'
        else:
            return ''

    def device_unplugged(self, index, facility):
        if index != 'None' and facility != 'None':
            return f'device-unplugged {index} {facility}'
        else:
            return ''

    # sink input and source output volumes
    def app_volume(self, id, val, stream_type):

        if type(val) == str:

            # check if is an absolute number
            if val.isdigit():
                val = int(val)
            else:
                return False

            # if not an absolute number, add it to current volume
            # else:
                # cur_vol = cmd('pmctl get-{stream_type}-volume {id}')
                # val = device_config['vol'] + int(val)

        # limit volume at 153
        if val > 153:
            val = 153
        # get channel number
        # chann = int(cmd(f'pmctl get-{stream_type}-chann {id}'))
        chann = 2

        # set volume object
        volume = self.pulse_socket.volume_info(val / 100, chann)
        id = int(id)

        if stream_type == 'sink-input':
            self.pulse_socket.pulsectl.sink_input_volume_set(id, volume)
        else:
            self.pulse_socket.pulsectl.source_output_volume_set(id, volume)

        return f'app-volume {id} {val} {stream_type}'

    def move_app_device(self, app, name, stream_type):
        command = f'pmctl move-{stream_type} {app} {name}'
        os.popen(command)
        return f'app {app} {name} {stream_type}'

    def read_config(self):
        # if config exists XDG_CONFIG_HOME
        if os.path.isfile(CONFIG_FILE):
            try:
                config = json.load(open(CONFIG_FILE))
            except Exception:
                LOG.error('could not load config file')
                sys.exit(1)

            # if config is outdated it will try to add missing keys
            if 'version' not in config or config['version'] != __version__:
                self.update_old_config(config)
                self.save_config(config)
        else:
            LOG.debug("Copying config file")
            config = json.load(open(ORIG_CONFIG_FILE))
            config['version'] = __version__
            self.save_config(config)

        self.config = config

    def update_old_config(self, config):
        LOG.debug("Updating config")

        config_orig = json.load(open(ORIG_CONFIG_FILE))
        config['version'] = __version__

        for key in config_orig:
            if key not in config:
                config[key] = config_orig[key]

        for i in ['a', 'b', 'vi', 'hi']:
            for j in config_orig[i]:
                for k in config_orig[i][j]:
                    if k not in config[i][j]:
                        config[i][j][k] = config_orig[i][j][k]

        # update legacy connection ...
        for i in (config['hi'], config['vi']):
            for num in i:
                for key in ('a1', 'a2', 'a3', 'b1', 'b2', 'b3'):
                    if isinstance(i[num].get(key), bool):

                        if i[num].get(key) is not None:
                            status = i[num][key]
                            del i[num][key]
                        else:
                            status = False

                        if i[num].get(f"{key}_latency") is not None:
                            latency = i[num][f"{key}_latency"]
                            del i[num][f"{key}_latency"]
                        else:
                            latency = 200

                        i[num][key] = {}
                        conn = i[num][key]
                        conn["status"] = status
                        conn["latency"] = latency
                        conn["auto_ports"] = True
                        conn["port_map"] = []

    # change buffer to not wait for other changes
    def save_config(self, config=None, buffer=True):
        if config is None: config = self.config
        if not os.path.isdir(CONFIG_DIR):
            os.mkdir(CONFIG_DIR)
        LOG.debug("writing config")
        with open(CONFIG_FILE, 'w') as outfile:
            json.dump(config, outfile, indent='\t', separators=(',', ': '))

    def get_config(self, args=None):
        if args is None:
            return json.dumps(self.config, ensure_ascii=False)
        else:
            args = args.split(':')
            config = self.config
            for arg in args:
                config = config[arg]

            if type(config) != dict:
                return config
            else:
                return json.dumps(config, ensure_ascii=False)

    def set_tray(self, state):
        if isinstance(state, str):
            state = state.lower() == 'true'
        self.config['tray'] = state
        ret_msg = f'tray {state}'
        return ret_msg

    def change_layout(self, layout):
        self.config['layout'] = layout
        return f'layout {layout}'

    def set_cleanup(self, state):
        state = str2bool(state)
        self.config['cleanup'] = state
        ret = f'cleanup {state}'
        return ret

    def set_vumeters(self, state):
        state = str2bool(state)
        self.config['enable_vumeters'] = state
        ret = f'vumeter {state}'
        return ret

    def create_command_dict(self):

        # some useful regex
        state = '(True|False|1|0|on|off|true|false)'
        # eq_control = r'([0-9](\.[0-9])?)(,[0-9](\.[0-9])?){14}'

        # None means that is an optional argument
        # STATE == [ [connect|true|on|1] | [disconnect|false|off|0] ]
        self.commands = {
            # ARGS: [hi|vi] id [a|b] id [None|STATE]
            # None = toggle
            'connect': {
                'function': self.connect,
                'notify': True,
                'save_config': True,
                'regex': f'(vi|hi) [0-9]+( (a|b) [0-9]+)?( ({state}))?( [0-9]+)?$'
            },

            # ARGS: [hi|vi|a|b] [None|STATE]
            # None = toggle
            'mute': {
                'function': self.mute,
                'notify': True,
                'save_config': True,
                'regex': f'(vi|hi|a|b) [0-9]+( ({state}))?$'
            },

            # ARGS: [hi|vi|a|b]
            'primary': {
                'function': self.set_primary,
                'notify': True,
                'save_config': True,
                'regex': r'(vi|hi|a|b) [0-9]+$'
            },

            # ARGS: id
            # id = hardware input id
            'rnnoise': {
                'function': self.rnnoise,
                'notify': True,
                'save_config': True,
                'regex': f'[0-9]+( ({state}|(set [0-9]+ [0-9]+)))?$'
            },

            # ARGS: [a|b] id [None|STATE|set] [None|control]
            # 'set' is for saving a new control value, if used you HAVE to pass
            # control, you can ommit the second and third args to toggle
            'eq': {
                'function': self.eq,
                'notify': True,
                'save_config': True,
                'regex': r'(a|b) [0-9]+( ((True|False|1|0|on|off|true|false)|(set ([0-9]+(\.[0-9]+)?)(,[0-9]+(\.[0-9]+)?){{14}})))?$'
            },

            ''
            # ARGS: [hi|a] id STATE
            # this will cleanup a hardware device and will not affect the config
            # useful when e.g. changing the device used in a hardware input strip
            'toggle-hd': {
                'function': self.toggle_hardware_device,
                'notify': False,
                'save_config': False,
                'regex': f'(hi|a) [0-9]+( {state})?$'
            },

            # ARGS: [vi|b] id STATE
            # this will cleanup a virtual device and will not affect the config
            # useful when e.g. renaming the device
            'toggle-vd': {
                'function': self.toggle_virtual_device,
                'notify': False,
                'save_config': False,
                'regex': f'(vi|b) [0-9]+( {state})?$'
            },

            # ARGS: [a|b|vi|hi] id NEW_NAME
            'rename': {
                'function': self.rename,
                'notify': True,
                'regex': ''
            },

            # ARGS: [a|hi] id NEW_DEVICE
            # NEW_DEVICE is the name of the device
            'change_hd': {
                'function': self.change_hardware_device,
                'notify': True,
                'save_config': True,
                'regex': r'(a|hi) [0-9]+ \w([\w\.-]+)?$'
            },

            # ARGS: [hi|vi|a|b] id vol
            # vol can be an absolute number from 0 to 153
            # you can also add and subtract
            'volume': {
                'function': self.volume,
                'notify': True,
                'save_config': False,
                'regex': '(a|b|hi|vi) [0-9]+ [+-]?[0-9]+$'
            },

            # ARGS: id vol [sink-input|source-output]
            # vol can ONLY be an absolute number from 0 to 153
            'app-volume': {
                'function': self.app_volume,
                'notify': True,
                'save_config': False,
                'regex': '[0-9]+ [0-9]+ (sink-input|source-output)$'
            },

            # ARGS: id device [sink-input|source-output]
            'move-app-device': {
                'function': self.move_app_device,
                'notify': True,
                'save_config': False,
                'regex': r'[0-9]+ \w([\w\.-]+)? (sink-input|source-output)$'
            },

            'port-map': {
                'function': self.set_port_map,
                'notify': True,
                'save_config': True,
                'regex': '(vi|hi) [0-9]+ (a|b)[0-9]+'
            },

            'auto-ports': {
                'function': self.set_auto_ports,
                'notify': True,
                'save_config': False,
                'regex': f'(vi|hi) [0-9]+ (a|b)[0-9]+ {state}'
            },

            'get-config': {
                'function': self.get_config,
                'notify': False,
                'save_config': False,
                'regex': ''
            },

            'save_config': {
                'function': self.save_config,
                'notify': False,
                # already saves the config without the waiting
                'save_config': False,
                'regex': ''
            },

            'set-cleanup': {
                'function': self.set_cleanup,
                'notify': True,
                'save_config': False,
                'regex': f'{state}$'
            },

            'set-vumeter': {
                'function': self.set_vumeters,
                'notify': True,
                'save_config': False,
                'regex': f'{state}$'
            },

            'set-layout': {
                'function': self.change_layout,
                'notify': True,
                'regex': '[aA-zZ]+$'
            },

            'set-tray': {
                'function': self.set_tray,
                'notify': True,
                'save_config': True,
                'regex': f'{state}$'
            },

            'device-plugged-in': {
                'function': self.device_plugged_in,
                'notify': True,
                'save_config': False,
                'regex': ''
            },

            'device-unplugged': {
                'function': self.device_unplugged,
                'notify': True,
                'save_config': False,
                'regex': ''
            },
            'create-device': {
                'function': self.create_device,
                'notify': True,
                'save_config': True,
                'regex': ''
            },
            'remove-device': {
                'function': self.remove_device,
                'notify': True,
                'save_config': True,
                'regex': '(hi|vi|a|b) [0-9]+'
            },
            'edit-device': {
                'function': self.edit_device,
                'notify': True,
                'save_config': True,
                'regex': ''
            }
        }


def cmd(command):
    sys.stdout.flush()
    p = subprocess.Popen(command.split(' '),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT)
    stdout, stderr = p.communicate()
    if p.returncode:
        LOG.warning('cmd \'%s\' returned %s', command, p.returncode)
        return
    return stdout.decode()


def str2bool(v):
    if type(v) == bool:
        return v
    else:
        return v.lower() in ['connect', 'true', 'on', '1']
