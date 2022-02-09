import os
import shutil
import json
import re
import sys
import subprocess
 
import pulsectl
from .settings import CONFIG_DIR, CONFIG_FILE, ORIG_CONFIG_FILE, __version__

class Pulse:
    def __init__(self, init=None, loglevel=0):
        self.loglevel = loglevel

        # check if pulseaudio is running
        try:
            subprocess.check_call('pmctl')
        except:
            sys.exit(1)

        self.channels = ['front-left','front-right','rear-left',
                'rear-right', 'front-center', 'lfe', 'side-left',
                'side-right', 'aux0', 'aux1', 'aux2', 'aux3'
                ]
        self.read_config()
        self.pulsectl = pulsectl.Pulse('pulsemeeter')
        if init == 'cmd': return
        command = ''
        command += self.start_sinks()
        command += self.start_sources()
        command += self.start_eqs()
        command += self.start_rnnoise()
        command += self.start_connections()
        command += self.start_primarys()
        # command += self.start_mute()
        
        # print(command)

        os.popen(command)

        self.vu_list = {}
        for i in ['hi', 'vi', 'a', 'b']:
            self.vu_list[i] = {}

        self.restart_window = False


    # get the correct device to connect to, e.g. include .monitor in a 
    # virtual sink name, or use a ladspa sink for a hardware source
    def get_correct_device(self, index, conn_type):

        # for virtual inputs
        if index[0] == 'vi':
            name = self.config[index[0]][index[1]]['name']

            if conn_type == "source":
                return name + ".monitor"
            else:
                return name

        # for hardware inputs
        if index[0] == 'hi':

            # return ladspa sink with rnnoise plugin
            if self.config[index[0]][index[1]]['use_rnnoise'] == True:
                name = f'{index[0]}{index[1]}_rnnoise'
                return name + ".monitor"

            else:
                name = self.config[index[0]][index[1]]['name']
                return name

        # for hardware outputs
        if index[0] == 'a':

            # return ladspa sink with eq plugin
            if self.config[index[0]][index[1]]['use_eq'] == True:
                name = f'{index[0]}{index[1]}_eq'
                return name

            else:
                name = self.config[index[0]][index[1]]['name']
                return name

        # virtual outputs need an aux sink to route audio into it
        if index[0] == 'b':

            # return ladspa sink with eq plugin
            if self.config[index[0]][index[1]]['use_eq'] == True:
                name = f'{index[0]}{index[1]}_eq'
                if conn_type == 'source':
                    name = name + ".monitor"
                return name

            # return aux sink
            else:
                name = self.config[index[0]][index[1]]['name'] + "_sink"
                if conn_type == 'source':
                    name = name + ".monitor"
                return name


    # init virtual inputs
    def start_sinks(self):
        command = ''
        sink_list = cmd("pactl list sinks short")

        # itarate between all devices
        for device_num in self.config['vi']:

            # if device does not have a name
            if self.config['vi'][device_num]['name'] != '':

                # if device is available on pulse
                if not re.search(self.config['vi'][device_num]['name'], sink_list):

                    # set sink properties
                    sink = self.config['vi'][device_num]['name']
                    channels = ''
                    channel_map = ''
                    sink_type = 'sink'

                    # for jack sinks
                    if self.config['jack']['enable'] == True:
                        channels = self.config['vi'][device_num]['channels']
                        channel_map = self.config['vi'][device_num]['channel_map']
                        channel_map = ','.join(channel_map) if len(channel_map) > 0 else ','.join(self.channels[:channels])
                        sink_type = 'jack-sink'

                    command += f"pmctl init {sink_type} {sink} {channels} {channel_map}\n"

        if self.loglevel > 1: print(command)
        return command

    # init virtual outputs
    def start_sources(self):
        command = ''
        source_list = cmd("pactl list sources short")
        # itarate between all devices
        for device_num in self.config['b']:

            # if device does not have a name
            if self.config['b'][device_num]['name'] != '':

                # if device is available on pulse
                if not re.search(self.config['b'][device_num]['name'], source_list):

                    # set source properties
                    source = self.config['b'][device_num]['name']
                    channels = ''
                    channel_map = ''
                    source_type = 'source'

                    # for jack sources
                    if self.config['jack']['enable'] == True:
                        channels = self.config['hi'][device_num]['channels']
                        channel_map = self.config['hi'][device_num]['channel_map']
                        channel_map = ','.join(channel_map) if len(channel_map) > 0 else ','.join(self.channels[:channels])
                        source_type = 'jack-source'

                    command += f"pmctl init {source_type} {source} {channels} {channel_map}\n"

        if self.loglevel > 1: print(command)
        return command

    # creates all ladspa sinks for eq plugin
    def start_eqs(self):
        command = ''
        for sink_type in ['a', 'b']:
            for sink_num in self.config[sink_type]:

                # check if device uses an eq
                if self.config[sink_type][sink_num]['use_eq'] == True:

                    # create eq sink
                    command += self.eq(sink_type, sink_num, status=True, 
                            reconnect=False, change_config=False, run_command=False)

        return command

    # creates all ladspa sinks for rnnoise plugin
    def start_rnnoise(self):
        command = ''
        source_type = 'hi'
        for source_num in self.config[source_type]:

            # check if device uses rnnoise
            if self.config[source_type][source_num]['use_rnnoise'] == True:

                # create rnnoise sink
                command += self.rnnoise(source_num, status=True, 
                        reconnect=False, change_config=False, run_command=False)
        return command

    # create connections
    def start_connections(self):
        command = ''
        for source_type in ['vi', 'hi']:
            for source_num in self.config[source_type]:
                for sink in ['a1', 'a2', 'a3', 'b1', 'b2', 'b3']:

                    # separate the chars to get info about sink
                    sink_type, sink_num = list(sink)

                    # if devices should be connected
                    if self.config[source_type][source_num][sink] == True:
                        command += self.connect(source_type, source_num, sink_type, sink_num,
                                status=True, run_command=False, init=True)
        return command

    # set all primary devices
    def start_primarys(self):
        command = ''
        for device_type in ['vi', 'b']:
            for device_num in self.config[device_type]:
                if self.config[device_type][device_num]['primary'] == True:
                    command += self.set_primary(device_type, device_num, run_command=False)
                
        if self.loglevel > 1: print(command)
        return command


    
    # creates a ladspa sink with rnnoise for a given hardware input
    def rnnoise(self, source_num, status=None, reconnect=True, change_config=True,
            run_command=True, ladspa_sink=None):

        # get control values
        source_type = 'hi'
        source_config = self.config[source_type][source_num]
        source = source_config['name']
        control = source_config['rnnoise_control']
        latency = source_config['rnnoise_latency']

        # set name for the plugin sink
        if ladspa_sink == None: ladspa_sink = f'{source_type}{source_num}_rnnoise'

        # status = None -> toggle state
        if status == None:
            status = not source_config['use_rnnoise']
        else:
            status = str2bool(status)

        conn_status = 'connect' if status else 'disconnect'

        # create ladspa sink
        command = f'pmctl rnnoise {ladspa_sink} {source} {control} {conn_status} {latency}\n'

        if change_config: 
            source_config['use_rnnoise'] = status

        # recreates all loopbacks from the device
        if reconnect:

            # itarate in all output devices
            for sink_type in ['a', 'b']:
                for sink_num in self.config[sink_type]:
                    
                    #if the source is connected to that device
                    if source_config[sink] == True:
                        sink = sink_type + sink_num
                        sink_name = self.get_correct_device([sink_type, sink_num], 'sink')
                        latency = source_config[sink + '_latency']
                        
                        # disconnect source from sinks, then connect ladspa sink to sinks
                        if status:
                            command += f'pmctl disconnect {source} {sink_name}\n'
                            command += f'pmctl connect {sink_name}.monitor {sink_name} {latency}\n'

                        # disconnect ladspa sink from sinks, then connect source to sinks
                        else:
                            command += f'pmctl disconnect {sink_name}.monitor {sink_name} {latency}\n'
                            command += f'pmctl connect {source} {sink_name} {latency}\n'

        if self.loglevel > 1: print(command)
        if run_command == True:
            os.popen(command)
            return f'rnoise {source_type} {source_num} {status}'
        else:
            return command

    # creates a ladspa sink with eq plugin for a given output
    def eq(self, sink_type, sink_num, status=None, control=None, ladspa_sink=None,
            reconnect=True, change_config=True, run_command=True):

        # get information about the device
        sink = sink_type + sink_num
        sink_config = self.config[sink_type][sink_num]
        master = sink_config['name']

        # set name for the plugin sink
        if ladspa_sink == None: ladspa_sink = f'{sink_type}{sink_num}_eq'

        # control values for the eq
        if control == None:
            control = sink_config['eq_control']
            control = '0,0,0,0,0,0,0,0,0,0,0,0,0,0,0' if control == '' else control

        # toggle on/off
        if status == None:
            status = not sink_config['use_eq']

        # if only changing the control
        elif status == 'set':
            status = sink_config['use_eq']

        else:
            status = str2bool(status)


        if change_config: 
            sink_config['use_eq'] = True if status else False
            sink_config['eq_control'] = control
        
        # create ladspa sink
        if status:
            command = f'pmctl eq init {ladspa_sink} {master} {control}\n'

        # removes ladspa sink
        else:
            command += f'pmctl eq remove {ladspa_sink}\n'

        # recreates all loopbacks from the device
        if reconnect:

            # itarate in all output devices
            for source_type in ['hi', 'vi']:
                for source_num in self.config[source_type]:

                    #if the source is connected to that device
                    if self.config[source_type][source_num][sink] == True:
                        vi = self.get_correct_device([source_type, source_num], 'source')

                        # disconnect source from sinks, then connect ladspa sink to sinks
                        if status:
                            command = command + f'pmctl disconnect {vi} {master}\n'
                            command = command + f'pmctl connect {vi} {ladspa_sink}\n'

                        # disconnect ladspa sink from sinks, then connect source to sinks
                        else:
                            command += f'pmctl disconnect {vi} {ladspa_sink}\n'
                            command += f'pmctl connect {vi} {master}\n'


        if self.loglevel > 1: print(command)
        if run_command:
            os.popen(command)
            return f'eq {sink_type} {sink_num} {status} {control}'
        else:
            return command

    # this will cleanup a hardware device and will not affect the config
    # useful when e.g. changing the device used in a hardware input/output strip
    def change_device_status(self, device_type, device_num, status, run_command=True):
        command = ''
        status = str2bool(status)

        # check what type of device, then disable plugins
        if device_type == 'a': 
            device_list = ['hi', 'vi']
            sink_type = device_type
            sink_num = device_num
            sink = f'{device_type}{device_num}'
            command += self.eq(sink_type, sink_num, status=False, 
                    reconnect=False, change_config=False, run_command=False)
        else:
            device_list =['a', 'b']
            source_type = device_type
            source_num = device_num
            command += self.rnnoise(source_num, status=False, 
                    reconnect=False, change_config=False, run_command=False)

        # remove connections
        for target_type in device_list:
            for target_num in self.config[target_type]:

                if device_type == 'a':
                    source_type = target_type
                    source_num = target_num
                else:
                    sink_type = target_type
                    sink_num = target_num
                    sink = f'{sink_type}{sink_num}'

                # disconnect
                if self.config[source_type][source_num][sink] == True:
                    command += self.connect(source_type, source_num, 'a', sink_num,
                            status=status, run_command=False, init=True)

        # if self.loglevel > 1: print(command)
        if run_command: os.popen(command)
        
    # recreates connections from an input, does not affect config
    def reconnect(self, source_type, source_num, run_command=True):
        command = ''

        # itarate between all output devices
        for sink_type in ['a', 'b']:
            for sink_num in self.config[sink_type]:
                sink = sink_type + sink_num

                # connection status check
                if self.config[source_type][source_num][sink] == True:
                    command += self.connect(source_type, source_num, sink_type, sink_num,
                            status=True, change_state=False, run_command=False, init=True)

        # if self.loglevel > 1: print(command)
        if run_command: os.popen(command)
        return command

    # connects an input to an output
    def connect(self, source_type, source_num, sink_type, sink_num, 
            status=None, run_command=True, change_state=True, init=False):

        source_config = self.config[source_type][source_num]
        sink_config = self.config[sink_type][sink_num]
        jack_config = self.config['jack']
        cur_conn_status = source_config[sink_type + sink_num]

        # toggle connection status
        if status == None:
            status = not cur_conn_status
        else:
            status = str2bool(status)

        conn_status = 'connect' if status else 'disconnect'

        # if trying to set the same state
        if init == False and ((cur_conn_status and status)
                or (not cur_conn_status and not status)):
            return False

        # if true, will change the config status
        if change_state == True:
            source_config[sink_type + sink_num] = True if status else False

        # if using jack
        if (jack_config['enable'] == True and 
                ((sink_config['jack'] == True and sink_type == 'a') or 
                (source_config['jack'] == True and source_type == 'hi') or 
                (source_type == 'vi' and sink_type == 'b'))):
                    return self.connect_jack(conn_status, [source_type, source_num], 
                            [sink_type, sink_num])

        # get name and latency of devices
        source = self.get_correct_device([source_type, source_num], 'source')
        sink = self.get_correct_device([sink_type, sink_num], 'sink')
        latency = self.config[source_type][source_num][f'{sink_type}{sink_num}_latency']

        # check if device exists
        if (source == '' or sink == ''):
            return ''

        command = f"pmctl {conn_status} {source} {sink} {latency}\n"

        if self.loglevel > 1: print(command)
        if run_command == True: 
            os.popen(command)
            return f'{source_type} {source_num} {sink_type}{sink_num} {status}'
        else:
            return command

    # needs commenting
    def connect_jack(self, state, source_index, sink_index, init=None):
        source_config = self.config[source_index[0]][source_index[1]]
        sink_config = self.config[sink_index[0]][sink_index[1]]
        jack_config = self.config['jack']

        dev_name = sink_config['name']
        if dev_name == '': return ''
        
        jack_map = f'{sink_index[0]}{sink_index[1]}_jack_map'
        port_group = f'{sink_index[0]}{sink_index[1]}_port_group'
        command = ''
        source = source_config['name']
        if source_config[port_group] == False:
            for channel in source_config[jack_map]:
                for system_chan in source_config[jack_map][channel]:
                    if sink_index[0] == 'a':
                        system_chan = f'playback_{system_chan}'
                        sink = 'system'
                    if source_index[0] == 'hi':
                        channel = f'capture_{channel}'
                        source = 'system'
                    if sink_index[0] == 'b':
                        sink = sink_config['name']
                    command += f"pmctl jack-{state} {source} {channel} {sink} {system_chan}\n"
                    # command += f"jack-{state} {source} {channel} {system_chan}\n"
        else:
            if source_config['jack'] == False or source_index[0] == 'vi':
                source_channels = source_config['channel_map']
                len_source_channels = source_config['channels']
            else:
                source_channels = jack_config['input_groups'][source_config['name']]
                len_source_channels = len(source_channels)
            if sink_index[0] == 'a':
                channel_group = jack_config['output_groups'][dev_name]
            else:
                channel_group = sink_config['channel_map']
            len_sink_channels = len(channel_group)
            min_len = min(len_sink_channels, len_source_channels)
            if len(source_channels) == 0:
                source_channels = self.channels[:len_source_channels]
            for channel_num in range(min_len):
                channel = source_channels[channel_num]
                sink_channel = channel_group[channel_num]
                if source_index[0] == 'hi':
                    channel = f'capture_{channel}'
                    source = 'system'
                if sink_index[0] == 'a':
                    sink = 'system'
                    sink_channel = f'playback_{sink_channel}'

                if sink_index[0] == 'b':
                    sink = sink_config['name']

                command += f"pmctl jack-{state} {source} {channel} {sink} {sink_channel}\n"
        if self.loglevel > 1:
            print(command)
        if init != 'init' and init != 'disconnect_init':
            os.popen(command)
        return command

    def change_hardware_device(self, sink_type, sink_num, name):
        device_config = self.config[sink_type][sink_num]

        # if device its not an empty name
        if device_config['name'] != '':
            self.change_device_status(sink_type, sink_num, False)

        device_config['name'] = name

        # if chosen device is not an empty name
        if name != '':
            self.change_device_status(sink_type, sink_num, True)
            # self.config[sink_type][sink_num]['jack'] = re.search('JACK:', 
                    # new_device['description'])
            # self.config[sink_type][sink_num]['jack'] = name in  

        print(f'{sink_type} {sink_num} {name}')
        return f'{sink_type} {sink_num} {name}'

    # get volume from source outputs and sink inputs
    def get_app_stream_volume(self, id, stream_type):
        command = f'pmctl get-{stream_type}-volume {id}'
        return int(cmd(command))

    def volume(self, device_type, device_num, val):
        device_config = self.config[device_type][device_num]

        # if volume is a string, convert it to integer
        if type(val) == str:

            # check if is an absolute number or + and -
            if re.match('[1-9]', val):
                val = int(val)

            # if not an absolute number, add it to current volume 
            else:
                val = device_config['vol'] + int(val)

        # limit volume at 153
        if val > 153:
            val = 153

        device_config['vol'] = val
        name = device_config['name']
        
        # get device info from pulsectl
        if device_type == 'a' or device_type == 'vi':
            device = self.pulsectl.get_sink_by_name(name)
        else:
            device = self.pulsectl.get_source_by_name(name)

        # set the volume
        volume = device.volume
        volume.value_flat = val / 100 
        self.pulsectl.volume_set(device, volume)
        return f'{device_type} {device_num} {val}'

    # sink input and source output volumes
    def app_volume(self, id, val, stream_type):

        if type(val) == str:

            # check if is an absolute number
            if re.match('[1-9]', val):
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
        volume = pulsectl.PulseVolumeInfo(val / 100, chann)

        if stream_type == 'sink-input':
            self.pulsectl.sink_input_volume_set(id, volume)
        else:
            self.pulsectl.source_output_volume_set(id, volume)

    # removes a device, then creates another one with the new name
    def rename(self, device_type, device_num, new_name):
        device_config = self.config[device_type][device_num]
        command = ''
        old_name = device_config['name']

        if new_name == old_name:
            return False

        if old_name != '' and new_name != '':
            device_config['name'] = new_name
            command += f'pmctl remove {old_name}'
            command += f'pmctl init sink {new_name}\n'
            command += self.reconnect(device_type, device_num, run_command=False)
            command += self.set_primary([device_type, device_num], run_command=False)
            os.popen(command)

        return True

    # get a dict list of inputs
    def get_virtual_devices(self, kind):
        command = f"pmctl list-virtual-{kind}"
        devices = cmd(command).split('\n')
        devices_concat = []

        # if list is not empty
        if devices[0] != '':

            # iterate between jsons
            for i in devices:

                # load a json and add it into a list
                try:
                    jason = json.loads(i)
                    devices_concat.append(jason)
                except:
                    print(f'ERROR: invalid json {i}')

        if kind == 'sources':
            self.virtual_source_list = devices_concat
        else:
            self.virtual_sink_list = devices_concat
        return devices_concat

    # get list of cards
    def get_hardware_devices(self, kind):
        command = f"pmctl list {kind}"
        devices = cmd(command)
        # devices_concat = []

        # if list is not empty
        # if devices[0] != '':

            # iterate between jsons
            # for i in devices:

            # load a json and add it into a list
        try:
            jason = json.loads(devices)
            # devices_concat.append(jason)
        except:
            print(f'ERROR: invalid json {devices}')

        # if using jack, also list groups
        if self.config['jack']['enable'] == True:
            group_type = 'input_groups' if kind == 'sources' else 'output_groups'
            for group in self.config['jack'][group_type]:
                channels = self.config['jack'][group_type][group]
                jason.append({'name': group, 'description': f'JACK:{group}{channels}'})
                # devices_concat.append()

        if kind == 'sources':
            self.source_list = jason
        else:
            self.sink_list = jason
        return json.dumps(jason, ensure_ascii=False)

    def get_config(self):
        return json.dumps(self.config, ensure_ascii=False)

    # def mute(self, index, state=None, init=None):
    def mute(self, device_type, device_num, state=None, run_command=True):
        device_config = self.config[device_type][device_num]
        name = device_config['name']
        if name == '': return

        # set device type
        device = 'sink' if device_type == 'a' or device_type == 'vi' else 'source'

        # if a state is None, toggle it
        if state == None:
            state = 1 if device_config['mute'] == False else 0

        # save setting
        device_config['mute'] = True if state == 1 else False

        command = f"pmctl mute {device} {name} {state}\n"

        if self.loglevel > 1: print(command)
        if run_command: 
            os.popen(command)
            return f'mute {device_type} {device_num} {state}'
        else:
            return command


    # todo
    # remove these two below
    # def apply_eq(self, index, name=None, control=None, status=None):
        # master = self.config[index[0]][index[1]]['name']
        # name = index[0] + index[1] + '_eq' if name == None else name
        # self.config[index[0]][index[1]]['use_eq'] = True

        # if control == None:
            # control = self.config[index[0]][index[1]]['eq_control']
            # control = '0,0,0,0,0,0,0,0,0,0,0,0,0,0,0' if control == '' else control

        # self.config[index[0]][index[1]]['eq_control'] = control

        # command = f'pmctl eq init {name} {master} {control}\n'
        # if status != 'init':
            # output = index[0] + index[1]
            # for i in ['hi', 'vi']:
                # for j in ['1', '2', '3']:
                    # if self.config[i][j][output] == True:
                        # vi = self.get_correct_device([i, j], 'source')
                        # command = command + f'pmctl disconnect {vi} {master}\n'
                        # command = command + f'pmctl connect {vi} {name}\n'

            # os.popen(command)

        # if self.loglevel > 1:
            # print(command)
        # return command
    # # reconnect = false will remove the eq but wont affect settings, nor reconnect devices
    # def remove_eq(self, sink_type, sink_num, reconnect=True, run_command=True, name=None):
        # sink = sink_type + sink_num
        # sink_config = self.config[sink_type][sink_num]
        # name = sink + '_eq' if name == None else name
        # master = sink_config['name']
        # command = ''

        # command += f'pmctl eq remove {name}\n'

        # # reconnect to proper devices
        # if reconnect:
            # sink_config['use_eq'] = False
            # for source_type in ['hi', 'vi']:
                # for source_num in self.config[source_type]:
                    # if self.config[source_type][source_num][sink] == True:
                        # vi = self.get_correct_device([source_type, source_num], 'source')
                        # command += f'pmctl disconnect {vi} {name}\n'
                        # command += f'pmctl connect {vi} {master}\n'

        # if self.loglevel > 1: print(command)
        # if run_command: os.popen(command)
        # return command
    
    # set a device as primary (only vi and b)
    def set_primary(self, device_type, device_num, run_command=True):
        name = self.config[device_type][device_num]['name']
        for i in self.config[device_type]:
            self.config[device_type][i]['primary'] = False if i != device_num else True

        device = 'sink' if device_type == 'vi' else 'source'
        command = f'pmctl set-primary {device} {name}\n'
        if run_command: os.popen(command)
        return command

    def get_virtual_device_name(self, dev_type):
        name_vi = []
        name_b = []
        for i in ['1','2','3']:
            if dev_type == 'source-output':
                if self.config['b'][i]['name'] != '':
                    name_b.append(self.config['b'][i]['name'])
                if self.config['vi'][i]['name'] != '':
                    name_vi.append(self.config['vi'][i]['name'] + '.monitor')
            elif self.config['vi'][i]['name'] != '':
                    name_vi.append(self.config['vi'][i]['name'])


        if dev_type == 'source-output':
            name_b.extend(name_vi)
            dev_list = name_b
        else:
            dev_list = name_vi
        return dev_list

    # get a list of application
    def get_app_streams(self, dev_type):
        command = f'pmctl list-{dev_type}s'
        devices = cmd(command).split('\n')
        apps = []
        if devices[0] != '':
            for i in devices:
                if 'name' not in i:
                    continue

                try:
                    jason = json.loads(i)
                    if 'icon' not in jason:
                        jason['icon'] = 'audio-card'
                    apps.append(jason)
                except Exception:
                    print(f'ERROR: invalid json {i}')
        return apps

    def move_app_device(self, app, name, stream_type):
        command = f'pmctl move-{stream_type} {app} {name}'
        os.popen(command)

    def move_source_output(self, app, name):
        command = f'pmctl move-source-output {app} {name}'
        os.popen(command)

    def move_sink_input(self, app, name):
        command = f'pmctl move-sink-input {app} {name}'
        os.popen(command)

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

    # subscribe to vumeter events
    def vumeter(self, index):
        name = self.config[index[0]][index[1]]['name']
        dev_type = '0' if index[0] == 'vi' or index[0] == 'a' else '1'
        command = ['pulse-vumeter', name, dev_type]
        sys.stdout.flush()
        self.vu_list[index[0]][index[1]] = subprocess.Popen(command,
            stdout=subprocess.PIPE, 
            stderr=subprocess.STDOUT,
            shell=False,
            encoding='utf-8',
            universal_newlines=False)

        # return piped values
        for stdout_line in iter(self.vu_list[index[0]][index[1]].stdout.readline, ""):
            yield stdout_line 
            
        # close connection
        self.vu_list[index[0]][index[1]].stdout.close()
        return_code = self.vu_list[index[0]][index[1]].wait()
        self.vu_list[index[0]].pop(index[1])

        # if return_code:
            # raise subprocess.CalledProcessError(return_code, command)

    def end_vumeter(self):
        for i in ['hi', 'vi', 'a', 'b']:
            for j in ['1','2','3']:
                if j in self.vu_list[i]:
                    self.vu_list[i][j].terminate()

    def jack_get_ports(self):
        return cmd('pmctl jack-system-ports')

    def read_config(self):

        # if config exists XDG_CONFIG_HOME 
        if os.path.isfile(CONFIG_FILE):
            try:
                self.config = json.load(open(CONFIG_FILE))
            except:
                print('ERROR loading config file')
                sys.exit(1)

            # if config is outdated it will try to add missing keys
            if not 'version' in self.config or self.config['version'] != __version__:
                self.config['layout'] = 'default'
                config_orig = json.load(open(ORIG_CONFIG_FILE))
                self.config['version'] = __version__
                self.config['enable_vumeters'] = True

                if 'jack' not in self.config:
                    self.config['jack'] = {}
                for i in config_orig['jack']:
                    if i not in self.config['jack']:
                        self.config['jack'][i] = config_orig['jack'][i]

                for i in ['a', 'b', 'vi', 'hi']:
                    for j in config_orig[i]:
                        for k in config_orig[i][j]:
                            if not k in self.config[i][j]:
                                self.config[i][j][k] = config_orig[i][j][k]
                self.save_config()
        else:
            self.config = json.load(open(ORIG_CONFIG_FILE))
             
            self.config['version'] = __version__

            self.save_config()


    def save_config(self):
        if not os.path.isdir(CONFIG_DIR):
            os.mkdir(CONFIG_DIR)
        with open(CONFIG_FILE, 'w') as outfile:
            json.dump(self.config, outfile, indent='\t', separators=(',', ': '))

def cmd(command):
    sys.stdout.flush()
    MyOut = subprocess.Popen(command.split(' '), 
        stdout=subprocess.PIPE, 
        stderr=subprocess.STDOUT)
    stdout,stderr = MyOut.communicate()
    return stdout.decode()

def str2bool(v):
    if type(v) == bool: 
        return v
    else:
        return v.lower() in ['connect', 'true', 'on', '1']
