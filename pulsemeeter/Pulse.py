import shutil
import os
import json
import re
import sys
import subprocess
from pathlib import Path

class Pulse:

    def __init__(self, config):
        command = ''
        command = command + self.start_sinks(config)
        command = command + self.start_sources(config)
        command = command + self.start_eqs(config)
        command = command + self.start_rnnoise(config)
        command = command + self.start_mute(config)
        command = command + self.start_conections(config)
        # print(command)
        os.popen(command)

    def get_correct_device(self, config, index, conn_type):
        if index[0] == 'vi':
            name = config[index[0]][index[1]]['name']
            if conn_type == "source":
                return name + ".monitor"
            else:
                return name

        if index[0] == 'hi':
            if config[index[0]][index[1]]['use_rnnoise'] == True:
                name = config[index[0]][index[1]]['rnnoise_name']
                return name + ".monitor"
            else:
                name = config[index[0]][index[1]]['name']
                return name

        if index[0] == 'a':
            if config[index[0]][index[1]]['use_eq'] == True:
                name = config[index[0]][index[1]]['eq_name']
                return name
            else:
                name = config[index[0]][index[1]]['name']
                return name

        if index[0] == 'b':
            if config[index[0]][index[1]]['use_eq'] == True:
                name = config[index[0]][index[1]]['eq_name']
                if conn_type == 'source':
                    name = name + ".monitor"
                return name
            else:
                name = config[index[0]][index[1]]['name'] + "_sink"
                if conn_type == 'source':
                    name = name + ".monitor"
                return name


    def start_sinks(self, config):
        command = ''
        sink_list = cmd("pactl list sinks short")
        for i in range(1, len(config['vi']) + 1):
            if(config['vi'][str(i)]['name'] != ''):
                if not re.search(config['vi'][str(i)]['name'], sink_list):
                    sink = config['vi'][str(i)]['name']
                    command = command + f"pmctl init sink {sink}\n"
        return command

    def start_sources(self, config):
        command = ''
        source_list = cmd("pactl list sources short")
        for i in range(1, len(config['b']) + 1):
            if(config['b'][str(i)]['name'] != ''):
                if not re.search(config['b'][str(i)]['name'], source_list):
                    source = config['b'][str(i)]['name']
                    command = command + f"pmctl init source {source}\n"
        return command

    def start_eqs(self, config):
        command = ''
        for i in ['a','b']:
            for j in range(1, 4):
                if config[i][str(j)]['use_eq'] == True:
                    command = command + self.apply_eq(config, [i, str(j)], config[i][str(j)]['eq_name'], config[i][str(j)]['eq_control'], 'init')

        return command

    def start_rnnoise(self, config):
        command = ''
        for j in range(1, 4):
            if config['hi'][str(j)]['use_rnnoise'] == True:
                source_index = ['hi', str(j)]
                sink_name = config['hi'][str(j)]['rnnoise_name']
                command = command + self.rnnoise(config, source_index, sink_name, "connect", 'init')
        return command

    def start_conections(self, config):
        command = ''
        for i in ['vi', 'hi']:
            for j in ['1', '2', '3']:
                source = self.get_correct_device(config, [i, j], 'source')

                for sink_num in ['a1', 'a2', 'a3', 'b1', 'b2', 'b3']:
                    sink_list = list(sink_num)

                    sink = self.get_correct_device(config, [sink_list[0], sink_list[1]], 'sink') 

                    if config[i][j][sink_num] == True:
                        latency = config[i][j][sink_num + "_latency"]
                        command = command +  f"pmctl connect {source} {sink} {latency}\n"
        return command

    def start_mute(self, config):
        command = ''
        for i in ['a', 'b']:
            for j in ['1', '2', '3']:
                if config[i][j]['mute'] == True:
                    device = 'sink' if i == 'a' else 'source'
                    command = command + self.mute(config, [i, j], device, 1, 'init')

        return command

    def rnnoise(self, config, source_index, sink_name, stat, init=''):
        source = config[source_index[0]][source_index[1]]['name']
        control = config[source_index[0]][source_index[1]]['rnnoise_control']
        latency = config[source_index[0]][source_index[1]]['rnnoise_latency']
        config[source_index[0]][source_index[1]]['use_rnnoise'] = True if stat == 'connect' else False
        config[source_index[0]][source_index[1]]['rnnoise_name'] = sink_name
        command = f'pmctl rnnoise {sink_name} {source} {control} {stat} {latency}\n'

        if init != 'init':
            for i in ['a1','a2','a3','b1','b2','b3']:
                if config[source_index[0]][source_index[1]][i] == True:
                    output = list(i)
                    output_dev = self.get_correct_device(config, [output[0], output[1]], 'sink') 
                    latency = config[source_index[0]][source_index[1]][i + "_latency"]
                    if stat == 'connect':
                        command = command + f'pmctl disconnect {source} {output_dev}\n'
                        command = command + f'pmctl connect {sink_name}.monitor {output_dev} {latency}\n'
                    else:
                        command = command + f'pmctl connect {source} {output_dev} {latency}\n'
            if init != 'cmd_only':
                os.popen(command)

        # print(command)
        return command
        
    def reconnect(self, config, device, number, init=''):
        sink_sufix = '' if device == 'hi' else '.monitor'
        command = ''
        for output in ['a1','a2','a3','b1','b3','b3']:
            dev = list(output)
            source_index = [device, str(number)]
            sink_index = [dev[0], dev[1]]
            if config[device][str(number)][output] == True:
                command = command + self.connect(config, "connect", source_index, sink_index, init)
        return command

    def connect(self, config, state, source_index, sink_index, init=''):
        config[source_index[0]][source_index[1]][sink_index[0] + sink_index[1]] = True if state == "connect" else False
        source = self.get_correct_device(config, source_index, 'source')
        sink = self.get_correct_device(config, sink_index, 'sink')
        latency = config[source_index[0]][source_index[1]][sink_index[0] + sink_index[1] + "_latency"]
        command = f"pmctl {state} {source} {sink} {latency}\n"
        # print(command)
        if init != 'init':
            os.popen(command)
        return command

    def volume(self, config, device_type, index, val):
        config[index[0]][index[1]]['vol'] = val
        name = config[index[0]][index[1]]['name']

        if (name == '' or device_type == ''):
            return
        command = f"pmctl volume {device_type} {name} {val}"
        # print(command)
        os.popen(command)

    def rename(self, config, device_index, new_name):
        old_name = config[device_index[0]][device_index[1]]['name']
        if new_name == old_name:
            return False

        if old_name != '':
            command = f'pmctl remove {old_name}'
            # print(command)
            os.popen(command)

        if new_name != '':
            config[device_index[0]][device_index[1]]['name'] = new_name
            command = f'pmctl init sink {new_name}\n'
            command = command + self.reconnect(config, device_index[0], device_index[1], 'init')
            # print(command)
            os.popen(command)

        return True


    def get_hardware_devices(self, kind):
        command = f"pmctl list {kind}"
        devices = cmd(command).split('\n')
        devices_concat = []
        for i in range(0, len(devices)-1, 2):
            devices_concat.append([devices[i], devices[i + 1]])
        return devices_concat

    def mute(self, config, index, device, state, init=''):
        name = config[index[0]][index[1]]['name']
        config[index[0]][index[1]]['mute'] = True if state == 1 else False
        if name == '':
            return

        command = f"pmctl mute {device} {name} {state}\n"
        if init != 'init':
            os.popen(command)
        # print(command)
        return command

    def apply_eq(self, config, index, name, control, status=''):
        master = config[index[0]][index[1]]['name']

        config[index[0]][index[1]]['eq_control'] = control
        config[index[0]][index[1]]['use_eq'] = True
        config[index[0]][index[1]]['eq_name'] = name

        if index[0] == 'b':
            master = master + "_sink"

        command = f'pmctl eq {name} {master} {control}\n'
        if status != 'init':
            output = index[0] + index[1]
            for i in ['hi', 'vi']:
                for j in range (1, 4):
                    if config[i][str(j)][output] == True:
                        vi = config[i][str(j)]['name']

                        if i == 'hi' and config[i][str(j)]['use_rnnoise'] == True:
                            vi = config[i][str(j)]['rnnoise_name'] + '.monitor'

                        command = command + f'pmctl disconnect {vi} {master}\n'

                        vi = vi + '.monitor' if i == 'vi' else vi
                        command = command + f'pmctl connect {vi} {name}\n'

            os.popen(command)

        # print(command)
        return command

    def remove_eq(self, config, master, name, output, index):
        config[index[0]][index[1]]['use_eq'] = False
        command = f'pmctl eq {name} remove\n'

        for i in ['hi', 'vi']:
            for j in range (1, 4):
                if config[i][str(j)][output] == True:
                    vi = config[i][str(j)]['name']
                    if i == 'hi' and config[i][str(j)]['use_rnnoise'] == True:
                        vi = config[i][str(j)]['rnnoise_name'] + '.monitor'

                    if i == 'vi':
                        vi = vi + '.monitor'
                    elif list(output)[0] == 'b':
                        master = master + '_sink'
                    command = command + f'pmctl connect {vi} {master}\n'

        os.popen(command)

def cmd(command):
    sys.stdout.flush()
    MyOut = subprocess.Popen(command.split(' '), 
        stdout=subprocess.PIPE, 
        stderr=subprocess.STDOUT)
    stdout,stderr = MyOut.communicate()
    return stdout.decode()

def get_config_path(glade=False):
    config_path = os.getenv('XDG_CONFIG_HOME')
    if config_path == None:
        config_path = os.getenv('HOME')
        config_path = os.path.join(config_path,'.config')
    config_path = os.path.join(config_path,'pulsemeeter')
    Path(config_path).mkdir(parents=True, exist_ok=True)
    config_file = os.path.join(config_path,'config.json')
    glade_file = os.path.join(config_path,'Interface.glade')
    if glade == True:
        return glade_file
    return config_file
