import os
import re
import sys
import subprocess
import pulsectl
from . import pmctl


class AudioServer:
    def __init__(self, pulse_socket, config, loglevel=0, init=True):
        self.config = config
        self.loglevel = 2
        self.audio_server = 'Pipewire'

        # check if pulseaudio is running
        try:
            subprocess.check_call('pmctl')
        except Exception:
            sys.exit(1)

        self.channels = ['front-left', 'front-right', 'rear-left',
                         'rear-right', 'front-center', 'lfe', 'side-left',
                         'side-right', 'aux0', 'aux1', 'aux2', 'aux3'
                         ]

        self.pulsectl = pulsectl.Pulse('pulsemeeter')
        self.pulse_socket = pulse_socket

        command = ''
        command += self.start_sinks()
        command += self.start_sources()
        command += self.start_eqs()
        command += self.start_rnnoise()
        command += self.start_connections()
        command += self.start_primarys()

        # print(command)

        os.popen(command)

        # self.restart_window = False

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
            if self.config[index[0]][index[1]]['use_rnnoise'] is True:
                name = f'{index[0]}{index[1]}_rnnoise'

                if self.audio_server != 'Pipewire':
                    name += ".monitor"

        # for hardware outputs
        if index[0] == 'a':

            # return ladspa sink with eq plugin
            if self.config[index[0]][index[1]]['use_eq'] is True:
                name = f'{index[0]}{index[1]}_eq'

        # virtual outputs need an aux sink to route audio into it
        if index[0] == 'b':

            # return ladspa sink with eq plugin
            if self.config[index[0]][index[1]]['use_eq'] is True:
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

            # if device does not have a name
            if self.config['vi'][device_id]['name'] != '':

                # external key means that the user is responsible for managing that sink
                if self.config['vi'][device_id]['external'] is False:

                    # if device is available on pulse
                    if not re.search(self.config['vi'][device_id]['name'], sink_list):

                        # set sink properties
                        sink = self.config['vi'][device_id]['name']
                        command += pmctl.init('sink', sink)

        if self.loglevel > 1: print(command)
        return command

    # init virtual outputs
    def start_sources(self):
        command = ''
        source_list = cmd("pactl list sources short")
        # itarate between all devices
        for device_id in self.config['b']:

            # if device does not have a name
            if self.config['b'][device_id]['name'] != '':

                # if device is available on pulse
                if not re.search(self.config['b'][device_id]['name'], source_list):

                    # set source properties
                    source = self.config['b'][device_id]['name']
                    command += pmctl.init('source', source)

        if self.loglevel > 1: print(command)
        return command

    # creates all ladspa sinks for eq plugin
    def start_eqs(self):
        command = ''
        for output_type in ['a', 'b']:
            for output_id in self.config[output_type]:

                # check if device uses an eq
                if self.config[output_type][output_id]['use_eq'] is True:

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
            if self.config[input_type][input_id]['use_rnnoise'] is True:

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

        if self.loglevel > 1: print(command)
        return command

    def stop_connections(self, run_command=True):
        command = ''
        for input_type in ['vi', 'hi']:
            for input_id in self.config[input_type]:
                command += self.reconnect(input_type, input_id, status=False, run_command=False)
        if run_command: os.popen(command)
        return command

    def cleanup(self):
        # remove connections
        # print('removing connections')
        command = self.stop_connections(run_command=False)

        # remove rnnoise
        # print('removing rnnoise')
        for hi_id in self.config['hi']:
            hi_config = self.config['hi'][hi_id]
            if hi_config['use_rnnoise']:
                command += self.rnnoise(hi_id, status=False,
                        reconnect=False, change_config=False, run_command=False)

        # remove eqs
        # print('removing eqs')
        for output_type in ['a', 'b']:
            for output_id in self.config[output_type]:
                output_config = self.config[output_type][output_id]
                if output_config['use_eq']:
                    command += self.eq(output_type, output_id, status=False,
                            reconnect=False, change_config=False, run_command=False)

        # remove virtual devices
        # print('removing virtual devices')
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
            latency = source_config['rnnoise_latency']

        if control is None:
            control = source_config['rnnoise_control']
            control == 95 if control == '' else int(control)

        # set name for the plugin sink
        if ladspa_sink is None: ladspa_sink = f'{input_type}{input_id}_rnnoise'

        # status = None -> toggle state
        if status is None:
            status = not source_config['use_rnnoise']
            conn_status = 'connect' if status else 'disconnect'

        # if only changing control
        elif status == 'set':
            conn_status = 'connect' if source_config['use_rnnoise'] else 'disconnect'

        else:
            status = str2bool(status)
            conn_status = 'connect' if status else 'disconnect'

        # create ladspa sink
        command = f'pmctl rnnoise {ladspa_sink} {source} {control} {conn_status} {latency}\n'

        if change_config:
            if status != 'set': source_config['use_rnnoise'] = status
            source_config['rnnoise_latency'] = int(latency)
            source_config['rnnoise_control'] = int(control)

        # recreates all loopbacks from the device
        if reconnect:

            # itarate in all output devices
            for output_type in ['a', 'b']:
                for output_id in self.config[output_type]:
                    sink = output_type + output_id

                    # if the source is connected to that device
                    if source_config[sink] is True:
                        sink_name = self.get_correct_device([output_type, output_id], 'sink')
                        latency = source_config[sink + '_latency']
                        ls = f'{ladspa_sink}.monitor' if self.audio_server != 'Pipewire' else ladspa_sink

                        # disconnect source from sinks, then connect ladspa sink to sinks
                        if status == 'set' and conn_status:
                            command += pmctl.disconnect(ls, sink_name)
                            command += pmctl.connect(ls, sink_name, latency=latency)

                        # disconnect source from sinks, then connect ladspa sink to sinks
                        elif status is True:
                            command += pmctl.disconnect(source, sink_name)
                            command += pmctl.connect(ls, sink_name, latency=latency)

                        # disconnect ladspa sink from sinks, then connect source to sinks
                        elif status is False:
                            command += pmctl.disconnect(ls, sink_name)
                            command += pmctl.connect(source, sink_name, latency=latency)

        if run_command is True:
            if self.loglevel > 1: print(command)
            os.popen(command)
            return f'rnnoise {input_id} {status} {control}'
        else:
            return command

    # creates a ladspa sink with eq plugin for a given output
    def eq(self, output_type, output_id, status=None, control=None, ladspa_sink=None,
            reconnect=True, change_config=True, run_command=True):

        # get information about the device
        sink = output_type + output_id
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
            status = not sink_config['use_eq']
            conn_status = status

        # if only changing the control
        elif status == 'set':
            conn_status = sink_config['use_eq']

        else:
            conn_status = str2bool(status)

        if change_config:
            if status != 'set': sink_config['use_eq'] = conn_status
            sink_config['eq_control'] = control

        if status == sink_config['use_eq'] is False:
            return f'eq {output_type} {output_id} {conn_status} {control}'

        # create ladspa sink
        if conn_status:
            command = f'pmctl eq init {ladspa_sink} {master} {control}\n'

        # removes ladspa sink
        else:
            command = f'pmctl eq remove {ladspa_sink}\n'

        # recreates all loopbacks from the device
        if reconnect:

            # itarate in all output devices
            for input_type in ['hi', 'vi']:
                for input_id in self.config[input_type]:

                    # if the source is connected to that device
                    if self.config[input_type][input_id][sink] is True:
                        vi = self.get_correct_device([input_type, input_id], 'source')

                        # disconnect source from sinks, then connect ladspa sink to sinks
                        if status == 'set' and conn_status:
                            command += pmctl.disconnect(vi, ladspa_sink)
                            command += pmctl.connect(vi, ladspa_sink)

                        # disconnect source from sinks, then connect ladspa sink to sinks
                        if conn_status:
                            command += pmctl.disconnect(vi, master)
                            command += pmctl.connect(vi, ladspa_sink)

                        # disconnect ladspa sink from sinks, then connect source to sinks
                        else:
                            command += pmctl.disconnect(vi, ladspa_sink)
                            command += pmctl.connect(vi, master)

        if run_command:
            if self.loglevel > 1: print(command)
            os.popen(command)
            return f'eq {output_type} {output_id} {status} {control}'
        else:
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
                if self.config[input_type][input_id][sink] is True:
                    command += self.connect(input_type, input_id, output_type, output_id,
                            status=status, change_state=False, run_command=False, init=True)

        if run_command:
            if self.loglevel > 1: print(command)
            os.popen(command)
        # print(command)
        return command

    # connects an input to an output
    def connect(self, input_type, input_id, output_type, output_id,
            status=None, latency=None, run_command=True, change_state=True, init=False):

        source_config = self.config[input_type][input_id]
        # sink_config = self.config[output_type][output_id]
        cur_conn_status = source_config[output_type + output_id]

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
            source_config[output_type + output_id] = status

        # get name and latency of devices
        source = self.get_correct_device([input_type, input_id], 'source')
        sink = self.get_correct_device([output_type, output_id], 'sink')
        if latency is None:
            latency = source_config[f'{output_type}{output_id}_latency']
        else:
            source_config[f'{output_type}{output_id}_latency'] = int(latency)

        # check if device exists
        # if (source == '' or sink == ''):
        #    return ''

        device_exists = source != '' and sink != ''

        command = pmctl.connect(source, sink, status, latency, run_command=False) if device_exists else ''

        if run_command is True:
            if device_exists:
                if self.loglevel > 1: print(command)
                os.popen(command)
            return f'connect {input_type} {input_id} {output_type} {output_id} {status} {latency}'
        else:
            return command

    def change_hardware_device(self, output_type, output_id, name):
        if name in ['None', None]: name = ''
        # print(f'{output_type} {output_id} {name}')
        device_config = self.config[output_type][output_id]

        # if device its not an empty name
        if device_config['name'] != '':
            self.toggle_hardware_device(output_type, output_id, False)

        device_config['name'] = name

        # if chosen device is not an empty name
        if name != '':
            self.toggle_hardware_device(output_type, output_id, True)
            # self.config[output_type][output_id]['jack'] = re.search('JACK:',
                    # new_device['description'])
            # self.config[output_type][output_id]['jack'] = name in
        else:
            name = None

        return f'change-hd {output_type} {output_id} {name}'

    # this will cleanup a hardware device and will not affect the config
    # useful when e.g. changing the device used in a hardware input/output strip
    def toggle_hardware_device(self, device_type, device_id, status, run_command=True):
        device_config = self.config[device_type][device_id]
        command = ''
        status = str2bool(status)

        # check what type of device, then disable plugins
        if device_type == 'a':
            device_list = ['hi', 'vi']

            if status:
                if device_config['use_eq']:
                    command += self.eq(device_type, device_id, status=True,
                            reconnect=False, change_config=False, run_command=False)

        else:
            device_list = ['a', 'b']

            if status:
                if device_type == 'hi' and device_config['use_rnnoise']:
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

                if self.config[input_type][input_id][sink] is True:
                    command += self.connect(input_type, input_id, output_type, output_id,
                            status=status, run_command=False, change_state=False, init=True)

        if not status:
            if device_type == 'a' and device_config['use_eq']:
                command += self.eq(device_type, device_id, status=False,
                        reconnect=False, change_config=False, run_command=False)

            elif device_type == 'hi' and device_config['use_rnnoise']:
                command += self.rnnoise(device_id, status=False,
                        reconnect=False, change_config=False, run_command=False)

        if self.loglevel > 1: print(command)
        if run_command: os.popen(command)

    def toggle_virtual_device(self, device_type, device_id, status=False, disconnect=True, run_command=True):
        command = ''
        device_config = self.config[device_type][device_id]

        if device_config['external'] is True:
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

        if self.loglevel > 1: print(command)
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
        device = 'sink' if device_type == 'a' or device_type == 'vi' else 'source'

        # if a state is None, toggle it
        if state is None:
            state = not device_config['mute']
        else:
            state = str2bool(state)

        # save setting
        device_config['mute'] = state

        conn_status = 1 if state else 0
        command = f"pmctl mute {device} {name} {conn_status}\n"

        if run_command:
            if self.loglevel > 1: print(command)
            os.popen(command)
            return f'mute {device_type} {device_id} {state}'
        else:
            return command

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
            # if re.match('[1-9]', val):
            #    val = int(val)

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
        volume.value_flat = val / 100
        self.pulse_socket.pulsectl.volume_set(device, volume)
        return f'volume {device_type} {device_id} {val}'

    def device_new(self, index, facility):
        if index != 'None' and facility != 'None':
            return f'device-new {index} {facility}'
        else:
            return ''

    def device_remove(self, index, facility):
        if index != 'None' and facility != 'None':
            return f'device-remove {index} {facility}'
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
        volume = self.pulse_socket.pulsectl.PulseVolumeInfo(val / 100, chann)
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

    # subscribe to pulseaudio events
    def subscribe(self):
        command = ['pactl', 'subscribe']
        sys.stdout.flush()
        env = os.environ
        env['LC_ALL'] = 'C'
        self.MyOut = subprocess.Popen(command, env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True)

        for stdout_line in iter(self.MyOut.stdout.readline, ""):
            yield stdout_line

        self.MyOut.stdout.close()
        return_code = self.MyOut.wait()
        if return_code:
            raise subprocess.CalledProcessError(return_code, command)

    def end_subscribe(self):
        self.MyOut.terminate()

    def jack_get_ports(self):
        return cmd('pmctl jack-system-ports')


def cmd(command):
    sys.stdout.flush()
    p = subprocess.Popen(command.split(' '),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT)
    stdout, stderr = p.communicate()
    if p.returncode:
        raise
    return stdout.decode()


def str2bool(v):
    if type(v) == bool:
        return v
    else:
        return v.lower() in ['connect', 'true', 'on', '1']
