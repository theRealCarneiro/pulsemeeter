import os
import shutil
import json
import re
import sys
import subprocess
 
import pulsectl

class Pulse:
    def __init__(self, config, loglevel=0):
        self.config = config
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
        # self.read_config()
        self.pulsectl = pulsectl.Pulse('pulsemeeter')
        # if init == 'cmd': return
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

        # self.restart_window = False


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
        for device_id in self.config['vi']:

            # if device does not have a name
            if self.config['vi'][device_id]['name'] != '':

                # if device is available on pulse
                if not re.search(self.config['vi'][device_id]['name'], sink_list):

                    # set sink properties
                    sink = self.config['vi'][device_id]['name']
                    channels = ''
                    channel_map = ''
                    output_type = 'sink'

                    # for jack sinks
                    if self.config['jack']['enable'] == True:
                        channels = self.config['vi'][device_id]['channels']
                        channel_map = self.config['vi'][device_id]['channel_map']
                        channel_map = ','.join(channel_map) if len(channel_map) > 0 else ','.join(self.channels[:channels])
                        output_type = 'jack-sink'

                    command += f"pmctl init {output_type} {sink} {channels} {channel_map}\n"

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
                    channels = ''
                    channel_map = ''
                    input_type = 'source'

                    # for jack sources
                    if self.config['jack']['enable'] == True:
                        channels = self.config['hi'][device_id]['channels']
                        channel_map = self.config['hi'][device_id]['channel_map']
                        channel_map = ','.join(channel_map) if len(channel_map) > 0 else ','.join(self.channels[:channels])
                        input_type = 'jack-source'

                    command += f"pmctl init {input_type} {source} {channels} {channel_map}\n"


        if self.loglevel > 1: print(command)
        return command


    # creates all ladspa sinks for eq plugin
    def start_eqs(self):
        command = ''
        for output_type in ['a', 'b']:
            for output_id in self.config[output_type]:

                # check if device uses an eq
                if self.config[output_type][output_id]['use_eq'] == True:

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
            if self.config[input_type][input_id]['use_rnnoise'] == True:

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
                if self.config[device_type][device_id]['primary'] == True:
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

        if latency == None:
            latency = source_config['rnnoise_latency']

        if control == None:
            control = source_config['rnnoise_control'] 
            control == 95 if control == '' else int(control)

        # set name for the plugin sink
        if ladspa_sink == None: ladspa_sink = f'{input_type}{input_id}_rnnoise'

        # status = None -> toggle state
        if status == None:
            status = not source_config['use_rnnoise']

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
                    
                    #if the source is connected to that device
                    if source_config[sink] == True:
                        sink_name = self.get_correct_device([output_type, output_id], 'sink')
                        latency = source_config[sink + '_latency']

                        # disconnect source from sinks, then connect ladspa sink to sinks
                        if status == 'set' and conn_status:
                            command += f'pmctl disconnect {ladspa_sink}.monitor {sink_name}\n'
                            command += f'pmctl connect {ladspa_sink}.monitor {sink_name} {latency}\n'
                        
                        # disconnect source from sinks, then connect ladspa sink to sinks
                        elif status == True:
                            command += f'pmctl disconnect {source} {sink_name}\n'
                            command += f'pmctl connect {ladspa_sink}.monitor {sink_name} {latency}\n'

                        # disconnect ladspa sink from sinks, then connect source to sinks
                        elif status == False:
                            command += f'pmctl disconnect {ladspa_sink}.monitor {sink_name} {latency}\n'
                            command += f'pmctl connect {source} {sink_name} {latency}\n'

        if run_command == True:
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
        if ladspa_sink == None: ladspa_sink = f'{output_type}{output_id}_eq'

        # control values for the eq
        if control == None:
            control = sink_config['eq_control']
            control = '0,0,0,0,0,0,0,0,0,0,0,0,0,0,0' if control == '' else control

        # toggle on/off
        if status == None:
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

        if status == sink_config['use_eq'] == False:
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

                    #if the source is connected to that device
                    if self.config[input_type][input_id][sink] == True:
                        vi = self.get_correct_device([input_type, input_id], 'source')


                        # disconnect source from sinks, then connect ladspa sink to sinks
                        if status == 'set' and conn_status:
                            command += f'pmctl disconnect {vi} {ladspa_sink}\n'
                            command += f'pmctl connect {vi} {master}\n'

                        # disconnect source from sinks, then connect ladspa sink to sinks
                        if conn_status:
                            command = command + f'pmctl disconnect {vi} {master}\n'
                            command = command + f'pmctl connect {vi} {ladspa_sink}\n'

                        # disconnect ladspa sink from sinks, then connect source to sinks
                        else:
                            command += f'pmctl disconnect {vi} {ladspa_sink}\n'
                            command += f'pmctl connect {vi} {master}\n'


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
                if self.config[input_type][input_id][sink] == True:
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
        sink_config = self.config[output_type][output_id]
        jack_config = self.config['jack']
        cur_conn_status = source_config[output_type + output_id]

        # toggle connection status
        if status == None:
            status = not cur_conn_status
        else:
            status = str2bool(status)

        conn_status = 'connect' if status else 'disconnect'

        # if trying to set the same state
        if (init == False and latency == None) and ((cur_conn_status and status)
                or (not cur_conn_status and not status)):
            return ''

        # if true, will change the config status
        if change_state == True:
            source_config[output_type + output_id] = True if status else False

        # if using jack
        if (jack_config['enable'] == True and 
                ((sink_config['jack'] == True and output_type == 'a') or 
                (source_config['jack'] == True and input_type == 'hi') or 
                (input_type == 'vi' and output_type == 'b'))):
                    return self.connect_jack(conn_status, [input_type, input_id], 
                            [output_type, output_id])

        # get name and latency of devices
        source = self.get_correct_device([input_type, input_id], 'source')
        sink = self.get_correct_device([output_type, output_id], 'sink')
        if latency == None:
            latency = source_config[f'{output_type}{output_id}_latency']
        else:
            source_config[f'{output_type}{output_id}_latency'] = int(latency)

        # check if device exists
        # if (source == '' or sink == ''):
        #    return ''

        command = f"pmctl {conn_status} {source} {sink} {latency}\n"
        device_exists = self.config[output_type][output_id]['name'] != ''

        if device_exists:
            if run_command == True: 
                if self.loglevel > 1: print(command)
                os.popen(command)
                return f'connect {input_type} {input_id} {output_type} {output_id} {status} {latency}'
            else:
                return command
        else: 
            return f'connect {input_type} {input_id} {output_type} {output_id} {status} {latency}'

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
            output_type = device_type
            output_id = device_id
            sink = f'{device_type}{device_id}'
        else:
            device_list =['a', 'b']
            input_type = device_type
            input_id = device_id

        if status:
            if device_type == 'a' and device_config['use_eq']:
                command += self.eq(output_type, output_id, status=True, 
                        reconnect=False, change_config=False, run_command=False)

            elif device_type == 'hi' and device_config['use_rnnoise']:
                command += self.rnnoise(input_id, status=True, 
                        reconnect=False, change_config=False, run_command=False)


        # set connections
        for target_type in device_list:
            for target_num in self.config[target_type]:

                if device_type == 'a':
                    input_type = target_type
                    input_id = target_num
                else:
                    output_type = target_type
                    output_id = target_num
                    sink = f'{output_type}{output_id}'

                if self.config[input_type][input_id][sink] == True:
                    command += self.connect(input_type, input_id, output_type, output_id,
                            status=status, run_command=False, change_state=False, init=True)

        if not status:
            if device_type == 'a' and device_config['use_eq']:
                command += self.eq(output_type, output_id, status=False, 
                        reconnect=False, change_config=False, run_command=False)

            elif device_type == 'hi' and device_config['use_rnnoise']:
                command += self.rnnoise(input_id, status=False, 
                        reconnect=False, change_config=False, run_command=False)

        if self.loglevel > 1: print(command)
        if run_command: os.popen(command)

    def toggle_virtual_device(self, device_type, device_id, status=False, disconnect=True, run_command=True):
        command = ''
        device_config = self.config[device_type][device_id]
        name = device_config["name"]
        if name == '': return ''
        status = str2bool(status)
        conn_type = 'sink' if device_type == 'vi' else 'source'

        if status:
            command += f'pmctl init {conn_type} {name}\n'
            if device_config['primary']:
                command += self.set_primary(device_type, device_id, run_command=False)

        if disconnect:
            command += self.reconnect(device_type, device_id, status=status, run_command=False)

        if not status:
            command += f'pmctl remove {name}\n'


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

    def change_layout(self, layout):
        self.config['layout'] = layout
        return f'layout {layout}'

    def set_cleanup(self, state):
        state = str2bool(state)
        self.config['cleanup'] = state
        ret = f'cleanup {state}'
        return ret

    # get a dict list of inputs
    def get_virtual_devices(self, kind):
        command = f"pmctl list-virtual-{kind}"
        devices = cmd(command)
        if devices == '':
            devices = '[]'
        # jason = []
        # try:
            # jason = json.loads(devices)
        # except:
            # print(f'ERROR: invalid json {devices}')

        # if kind == 'sources':
            # self.virtual_source_list = jason
        # else:
            # self.virtual_sink_list = jason
        return devices

    # get list of cards
    def get_hardware_devices(self, kind):
        command = f"pmctl list {kind}"
        devices = cmd(command)
        try:
            jason = json.loads(devices)
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

    def mute(self, device_type, device_id, state=None, run_command=True):
        device_config = self.config[device_type][device_id]
        name = device_config['name']
        if name == '': return

        # set device type
        device = 'sink' if device_type == 'a' or device_type == 'vi' else 'source'

        # if a state is None, toggle it
        if state == None:
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
        command = f'pmctl set-primary {device} {name}\n'
        if run_command: 
            os.popen(command)
            return f'primary {device_type} {device_id}'
        return command

    # get volume from source outputs and sink inputs
    def get_app_stream_volume(self, id, stream_type):
        command = f'pmctl get-{stream_type}-volume {id}'
        return cmd(command)

    def volume(self, device_type, device_id, val):
        device_config = self.config[device_type][device_id]

        # if volume is a string, convert it to integer
        if type(val) == str:

            # check if is an absolute number or + and -
            if val.isdigit():
                val = int(val)
            #if re.match('[1-9]', val):
            #    val = int(val)

            # if not an absolute number, add it to current volume 
            else:
                val = device_config['vol'] + int(val)

        # limit volume at 153
        if val > 153:
            val = 153

        device_config['vol'] = val
        name = device_config['name']
        
        # get device info from pulsectl
        if device_type in ['a', 'vi']:
            device = self.pulsectl.get_sink_by_name(name)
        else:
            device = self.pulsectl.get_source_by_name(name)

        # set the volume
        volume = device.volume
        volume.value_flat = val / 100 
        self.pulsectl.volume_set(device, volume)
        return f'volume {device_type} {device_id} {val}'

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
        volume = pulsectl.PulseVolumeInfo(val / 100, chann)
        id = int(id)

        if stream_type == 'sink-input':
            self.pulsectl.sink_input_volume_set(id, volume)
        else:
            self.pulsectl.source_output_volume_set(id, volume)

        return f'app-volume {id} {val} {stream_type}'

    # get a list of application
    def get_app_streams(self, dev_type):
        command = f'pmctl list-{dev_type}s'
        devices = cmd(command)
        if devices != '':
            try:
                jason = json.loads(devices)
            except Exception:
                print(f'ERROR: invalid json {devices}')
                return 'ERROR: invalid json'
            return devices
        else: return '[]'

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
    stdout,stderr = p.communicate()
    if p.returncode:
        raise
    return stdout.decode()

def run_command(command):
    try:
        subprocess.check_call(command)
    except:
        sys.exit(1)

def str2bool(v):
    if type(v) == bool: 
        return v
    else:
        return v.lower() in ['connect', 'true', 'on', '1']
