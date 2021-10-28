import os
import json
import re
import sys
import subprocess
 
from .settings import CONFIG_DIR, CONFIG_FILE, ORIG_CONFIG_FILE, __version__

class Pulse:

    def __init__(self, init=None):
        self.read_config()
        if init == 'cmd': return
        command = ''
        command = command + self.start_sinks()
        command = command + self.start_sources()
        command = command + self.start_eqs()
        command = command + self.start_rnnoise()
        command = command + self.start_mute()
        command = command + self.start_conections()
        # print(command)
        os.popen(command)

    def get_correct_device(self, index, conn_type):
        if index[0] == 'vi':
            name = self.config[index[0]][index[1]]['name']
            if conn_type == "source":
                return name + ".monitor"
            else:
                return name

        if index[0] == 'hi':
            if self.config[index[0]][index[1]]['use_rnnoise'] == True:
                name = self.config[index[0]][index[1]]['rnnoise_name']
                return name + ".monitor"
            else:
                name = self.config[index[0]][index[1]]['name']
                return name

        if index[0] == 'a':
            if self.config[index[0]][index[1]]['use_eq'] == True:
                name = self.config[index[0]][index[1]]['eq_name']
                return name
            else:
                name = self.config[index[0]][index[1]]['name']
                return name

        if index[0] == 'b':
            if self.config[index[0]][index[1]]['use_eq'] == True:
                name = self.config[index[0]][index[1]]['eq_name']
                if conn_type == 'source':
                    name = name + ".monitor"
                return name
            else:
                name = self.config[index[0]][index[1]]['name'] + "_sink"
                if conn_type == 'source':
                    name = name + ".monitor"
                return name


    def start_sinks(self):
        command = ''
        sink_list = cmd("pactl list sinks short")
        for i in range(1, len(self.config['vi']) + 1):
            if(self.config['vi'][str(i)]['name'] != ''):
                if not re.search(self.config['vi'][str(i)]['name'], sink_list):
                    sink = self.config['vi'][str(i)]['name']
                    command = command + f"pmctl init sink {sink}\n"
        return command

    def start_sources(self):
        command = ''
        source_list = cmd("pactl list sources short")
        for i in range(1, len(self.config['b']) + 1):
            if(self.config['b'][str(i)]['name'] != ''):
                if not re.search(self.config['b'][str(i)]['name'], source_list):
                    source = self.config['b'][str(i)]['name']
                    command = command + f"pmctl init source {source}\n"
        return command

    def start_eqs(self):
        command = ''
        for i in ['a','b']:
            for j in range(1, 4):
                if self.config[i][str(j)]['use_eq'] == True:
                    command = command + self.apply_eq( [i, str(j)], status='init')

        return command

    def start_rnnoise(self):
        command = ''
        for j in range(1, 4):
            if self.config['hi'][str(j)]['use_rnnoise'] == True:
                source_index = ['hi', str(j)]
                sink_name = self.config['hi'][str(j)]['rnnoise_name']
                command = command + self.rnnoise( source_index, sink_name, "connect", 'init')
        return command

    def start_conections(self):
        command = ''
        for i in ['vi', 'hi']:
            for j in ['1', '2', '3']:
                source = self.get_correct_device( [i, j], 'source')

                for sink_num in ['a1', 'a2', 'a3', 'b1', 'b2', 'b3']:
                    sink_list = list(sink_num)

                    sink = self.get_correct_device( [sink_list[0], sink_list[1]], 'sink') 

                    if self.config[i][j][sink_num] == True:
                        latency = self.config[i][j][sink_num + "_latency"]
                        command = command +  f"pmctl connect {source} {sink} {latency}\n"
        return command

    def start_mute(self):
        command = ''
        for i in ['a', 'b']:
            for j in ['1', '2', '3']:
                if self.config[i][j]['mute'] == True:
                    command = command + self.mute([i, j], 1, 'init')

        return command

    def rnnoise(self, source_index, sink_name, stat, init=None):

        source = self.config[source_index[0]][source_index[1]]['name']
        control = self.config[source_index[0]][source_index[1]]['rnnoise_control']
        latency = self.config[source_index[0]][source_index[1]]['rnnoise_latency']

        self.config[source_index[0]][source_index[1]]['use_rnnoise'] = True if stat == 'connect' else False
        self.config[source_index[0]][source_index[1]]['rnnoise_name'] = sink_name

        command = f'pmctl rnnoise {sink_name} {source} {control} {stat} {latency}\n'

        # if != init it wont try to load the connections
        if init != 'init':
            for i in ['a1','a2','a3','b1','b2','b3']:
                if self.config[source_index[0]][source_index[1]][i] == True:
                    output = list(i)
                    output_dev = self.get_correct_device( [output[0], output[1]], 'sink') 
                    latency = self.config[source_index[0]][source_index[1]][i + "_latency"]
                    if stat == 'connect':
                        command = command + f'pmctl disconnect {source} {output_dev}\n'
                        command = command + f'pmctl connect {sink_name}.monitor {output_dev} {latency}\n'
                    else:
                        command = command + f'pmctl connect {source} {output_dev} {latency}\n'
            if init != 'cmd_only':
                os.popen(command)

        # print(command)
        return command
        
    def reconnect(self, device, number, init=None):
        sink_sufix = '' if device == 'hi' else '.monitor'
        command = ''
        for output in ['a1','a2','a3','b1','b3','b3']:
            dev = list(output)
            source_index = [device, str(number)]
            sink_index = [dev[0], dev[1]]
            if self.config[device][str(number)][output] == True:
                command = command + self.connect( "connect", source_index, sink_index, init)
        return command

    def connect(self, state, source_index, sink_index, init=None):
        self.config[source_index[0]][source_index[1]][sink_index[0] + sink_index[1]] = True if state == "connect" else False
        source = self.get_correct_device( source_index, 'source')
        sink = self.get_correct_device( sink_index, 'sink')
        latency = self.config[source_index[0]][source_index[1]][sink_index[0] + sink_index[1] + "_latency"]
        command = f"pmctl {state} {source} {sink} {latency}\n"
        # print(command)
        if init != 'init':
            os.popen(command)
        return command

    def volume(self, index, val):
        device_type = 'sink' if index[0] == 'a' or index[0] == 'vi' else 'source'
        self.config[index[0]][index[1]]['vol'] = val
        name = self.config[index[0]][index[1]]['name']

        if (name == '' or device_type == ''):
            return
        command = f"pmctl volume {device_type} {name} {val}"
        # print(command)
        os.popen(command)

    def rename(self, device_index, new_name):
        old_name = self.config[device_index[0]][device_index[1]]['name']
        if new_name == old_name:
            return False

        if old_name != '':
            command = f'pmctl remove {old_name}'
            os.popen(command)

        self.config[device_index[0]][device_index[1]]['name'] = new_name
        if new_name != '':
            command = f'pmctl init sink {new_name}\n'
            command = command + self.reconnect( device_index[0], device_index[1], 'init')
            os.popen(command)

        return True

    def get_hardware_devices(self, kind):
        command = f"pmctl list {kind}"
        devices = cmd(command).split('\n')
        devices_concat = []
        for i in range(0, len(devices)-1, 2):
            devices_concat.append([devices[i], devices[i + 1]])
        return devices_concat

    def mute(self, index, state=None, init=None):
        name = self.config[index[0]][index[1]]['name']
        if name == '': return

        device = 'sink' if index[0] == 'a' else 'source'

        if state == None:
            state = 1 if self.config[index[0]][index[1]]['mute'] == False else 0
        self.config[index[0]][index[1]]['mute'] = True if state == 1 else False
            

        command = f"pmctl mute {device} {name} {state}\n"
        if init == None:
            os.popen(command)

        # print(command)
        return command

    def apply_eq(self, index, name=None, control=None, status=None):
        master = self.get_correct_device([index[0], index[1]], 'sink')
        name = index[0].upper() + index[1] + '_EQ' if name == None else name
        self.config[index[0]][index[1]]['use_eq'] = True
        self.config[index[0]][index[1]]['eq_name'] = name

        if control == None:
            control = self.config[index[0]][index[1]]['eq_control']
            control = '0,0,0,0,0,0,0,0,0,0,0,0,0,0,0' if control == '' else control

        self.config[index[0]][index[1]]['eq_control'] = control

        command = f'pmctl eq {name} {master} {control}\n'
        if status != 'init':
            output = index[0] + index[1]
            for i in ['hi', 'vi']:
                for j in ['1', '2', '3']:
                    if self.config[i][j][output] == True:
                        vi = self.get_correct_device([i, j], 'source')
                        command = command + f'pmctl disconnect {vi} {master}\n'
                        command = command + f'pmctl connect {vi} {name}\n'

            os.popen(command)

        # print(command)
        return command

    def remove_eq(self, index, name=None):
        output = index[0] + index[1]
        name = output.upper() + '_EQ' if name == None else name
        master = self.config[index[0]][index[1]]['name']
        self.config[index[0]][index[1]]['use_eq'] = False
        command = f'pmctl eq {name} remove\n'

        for i in ['hi', 'vi']:
            for j in ['1', '2', '3']:
                if self.config[i][j][output] == True:
                    vi = self.get_correct_device([i, j], 'source')
                    command = command + f'pmctl connect {vi} {master}\n'

        # print(command)
        os.popen(command)

    def read_config(self):

        # if config exists XDG_CONFIG_HOME 
        if os.path.isfile(CONFIG_FILE):
            self.config = json.load(open(CONFIG_FILE))

            # if config is outdated
            if not 'version' in self.config or self.config['version'] != __version__:
                config_orig = json.load(open(ORIG_CONFIG_FILE))
                self.config['version'] = __version__
                for i in ['a', 'b', 'vi', 'hi']:
                    for j in ['1', '2', '3']:
                        for k in config_orig[i][j]:
                            if not k in self.config[i][j]:
                                self.config[i][j][k] = self.config_orig[i][j][k]
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
