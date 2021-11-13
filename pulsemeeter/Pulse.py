import os
import shutil
import json
import re
import sys
import subprocess
 
import pulsectl
from .settings import CONFIG_DIR, CONFIG_FILE, ORIG_CONFIG_FILE, __version__

class Pulse:

    def __init__(self, init=None):
        try:
            subprocess.check_call('pmctl')
        except:
            sys.exit(1)

        self.read_config()
        self.pulsectl = pulsectl.Pulse('pulsemeeter')
        if init == 'cmd': return
        command = ''
        command = command + self.start_sinks()
        command = command + self.start_sources()
        command = command + self.start_eqs()
        command = command + self.start_rnnoise()
        # command = command + self.start_mute()
        command = command + self.start_conections()
        # print(command)

        os.popen(command)

        self.vu_list = {}
        for i in ['hi', 'vi', 'a', 'b']:
            self.vu_list[i] = {}


    def get_correct_device(self, index, conn_type):
        if index[0] == 'vi':
            name = self.config[index[0]][index[1]]['name']
            if conn_type == "source":
                return name + ".monitor"
            else:
                return name

        if index[0] == 'hi':
            if self.config[index[0]][index[1]]['use_rnnoise'] == True:
                name = f'{index[0]}{index[1]}_rnnoise'
                return name + ".monitor"
            else:
                name = self.config[index[0]][index[1]]['name']
                return name

        if index[0] == 'a':
            if self.config[index[0]][index[1]]['use_eq'] == True:
                name = f'{index[0]}{index[1]}_eq'
                return name
            else:
                name = self.config[index[0]][index[1]]['name']
                return name

        if index[0] == 'b':
            if self.config[index[0]][index[1]]['use_eq'] == True:
                name = f'{index[0]}{index[1]}_eq'
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
            if self.config['vi'][str(i)]['name'] != '':
                if not re.search(self.config['vi'][str(i)]['name'], sink_list):
                    sink = self.config['vi'][str(i)]['name']
                    command = command + f"pmctl init sink {sink}\n"
        return command

    def start_sources(self):
        command = ''
        source_list = cmd("pactl list sources short")
        for i in range(1, len(self.config['b']) + 1):
            if self.config['b'][str(i)]['name'] != '':
                if not re.search(self.config['b'][str(i)]['name'], source_list):
                    source = self.config['b'][str(i)]['name']
                    command = command + f"pmctl init source {source}\n"
        return command

    def start_eqs(self):
        command = ''
        for i in ['a','b']:
            for j in range(1, 4):
                if self.config[i][str(j)]['use_eq'] == True:
                    command = command + self.apply_eq([i, str(j)], status='init')

        return command

    def start_rnnoise(self):
        command = ''
        for j in range(1, 4):
            if self.config['hi'][str(j)]['use_rnnoise'] == True:
                source_index = ['hi', str(j)]
                sink_name = f'hi{j}_rnnoise'
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

                    if self.config[i][j][sink_num] == True and self.config[i][j]['name'] != '' and  self.config[sink_list[0]][sink_list[1]]['name'] != '':
                        latency = self.config[i][j][sink_num + "_latency"]
                        command = command +  f"pmctl connect {source} {sink} {latency}\n"
        return command

    def rnnoise(self, source_index, sink_name, stat, init=None):

        source = self.config[source_index[0]][source_index[1]]['name']
        control = self.config[source_index[0]][source_index[1]]['rnnoise_control']
        latency = self.config[source_index[0]][source_index[1]]['rnnoise_latency']

        self.config[source_index[0]][source_index[1]]['use_rnnoise'] = True if stat == 'connect' else False

        command = f'pmctl rnnoise {sink_name} {source} {control} {stat} {latency}\n'

        # if != init it wont try to load the connections
        if init != 'init':
            for i in ['a1','a2','a3','b1','b2','b3']:
                if self.config[source_index[0]][source_index[1]][i] == True:
                    output = list(i)
                    output_dev = self.get_correct_device([output[0], output[1]], 'sink') 
                    latency = self.config[source_index[0]][source_index[1]][i + "_latency"]
                    if stat == 'connect':
                        command += f'pmctl disconnect {source} {output_dev}\n'
                        command += f'pmctl connect {sink_name}.monitor {output_dev} {latency}\n'
                    else:
                        command += f'pmctl disconnect {sink_name}.monitor {output_dev} {latency}\n'
                        command += f'pmctl connect {source} {output_dev} {latency}\n'
            if init != 'cmd_only':
                os.popen(command)

        # print(command)
        return command

    def start_sink(self, number):

        command = ''
        if self.config['a'][number]['use_eq'] == True:
            name = f'a{number}_eq'
            master = self.config['a'][number]['name']
            control = self.config['a'][number]['eq_control']
            command += f'pmctl eq init {name} {master} {control}\n'

        for i in ['hi', 'vi']:
            for j in ['1', '2', '3']:
                if self.config[i][j][f'a{number}'] == True:
                    vi = self.get_correct_device([i, j], 'source')
                    master = self.get_correct_device(['a', number], 'sink')
                    command += f'pmctl connect {vi} {master}\n'

        os.popen(command)

    def disable_sink(self, number):

        command = ''
        if self.config['a'][number]['use_eq'] == True:
            name = f'a{number}_eq'
            master = self.config['a'][number]['name']
            control = self.config['a'][number]['eq_control']
            command += f'pmctl eq remove {name} {master} {control}\n'

        for i in ['hi', 'vi']:
            for j in ['1', '2', '3']:
                if self.config[i][j][f'a{number}'] == True:
                    vi = self.get_correct_device([i, j], 'source')
                    master = self.get_correct_device(['a', number], 'sink')
                    command += f'pmctl disconnect {vi} {master}\n'

        # print(command)
        os.popen(command)

    def start_source(self, number):

        command = ''
        if self.config['hi'][number]['use_rnnoise'] == True:
            sink_name = f'hi{number}_rnnoise'

            source = self.config['hi'][number]['name']
            control = self.config['hi'][number]['rnnoise_control']
            latency = self.config['hi'][number]['rnnoise_latency']
            command += f'pmctl rnnoise {sink_name} {source} {control} connect {latency}\n'

        for i in ['a', 'b']:
            for j in ['1', '2', '3']:
                if self.config['hi'][number][f'{i}{j}'] == True:
                    vi = self.get_correct_device(['hi', number], 'source')
                    master = self.get_correct_device([i, j], 'sink')
                    command += f'pmctl connect {vi} {master}\n'

        os.popen(command)


    def disable_source(self, number):

        command = ''

        if self.config['hi'][number]['use_rnnoise'] == True:
            sink_name = f'hi{number}_rnnoise'
            source = self.config['hi'][number]['name']
            command += f'pmctl rnnoise {sink_name} {source} 0 disconnect\n'

        # if not shutil.which('pulseaudio'):
        for i in ['a', 'b']:
            for j in ['1', '2', '3']:
                if self.config['hi'][number][f'{i}{j}'] == True:
                    vi = self.get_correct_device(['hi', number], 'source')
                    master = self.get_correct_device([i, j], 'sink')
                    command += f'pmctl disconnect {vi} {master}\n'

        os.popen(command)
        
    def reconnect(self, device, number, init=None):
        sink_sufix = '' if device == 'hi' else '.monitor'
        command = ''

        for output in ['a1','a2','a3','b1','b3','b3']:

            dev = list(output)
            source_index = [device, str(number)]
            sink_index = [dev[0], dev[1]]
            if self.config[device][str(number)][output] == True and self.config[dev[0]][dev[1]]['name'] != '' :
                command = command + self.connect( "connect", source_index, 
                        sink_index, init)
        return command

    def connect(self, state, source_index, sink_index, init=None):
        if init != 'disconnect':
            self.config[source_index[0]][source_index[1]][sink_index[0] + sink_index[1]] = True if state == "connect" else False
        source = self.get_correct_device(source_index, 'source')
        sink = self.get_correct_device(sink_index, 'sink')
        if source == '' or sink == '':
            return ''
        latency = self.config[source_index[0]][source_index[1]][sink_index[0] + sink_index[1] + "_latency"]
        command = f"pmctl {state} {source} {sink} {latency}\n"
        # print(command)
        if init != 'init':
            os.popen(command)
        return command

    def get_app_stream_volume(self, id, stream_type):
        command = f'pmctl get-{stream_type}-volume {id}'
        return int(cmd(command))

    def get_sink_input_volume(self, id):
        command = f'pmctl get-sink-input-volume {id}'
        return int(cmd(command))

    def get_source_output_volume(self, id):
        command = f'pmctl get-source-output-volume {id}'
        return int(cmd(command))

    def volume(self, index, val, stream_type=None):
        if stream_type == None:
            self.config[index[0]][index[1]]['vol'] = val
            name = self.config[index[0]][index[1]]['name']
            if index[0] == 'a' or index[0] == 'vi':
                device = self.pulsectl.get_sink_by_name(name)
            else:
                device = self.pulsectl.get_source_by_name(name)

            volume = device.volume
            volume.value_flat = val / 100 
            self.pulsectl.volume_set(device, volume)

        elif stream_type == 'sink-input':
            chann = int(cmd(f'pmctl get-sink-input-chann {index}'))
            volume = pulsectl.PulseVolumeInfo(val / 100, chann)
            self.pulsectl.sink_input_volume_set(index, volume)
        else:
            chann = int(cmd(f'pmctl get-source-output-chann {index}'))
            volume = pulsectl.PulseVolumeInfo(val / 100, 2)
            self.pulsectl.source_output_volume_set(index, volume)

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
            command = command + self.reconnect(device_index[0], device_index[1], 'init')
            command = command + self.set_primary(device_index, 'init')
            os.popen(command)

        return True

    def get_virtual_devices(self, kind):
        command = f"pmctl list-virtual-{kind}"
        devices = cmd(command).split('\n')
        devices_concat = []
        if devices[0] != '':
            # print(devices)
            for i in devices:
                jason = json.loads(i)
                devices_concat.append(jason)
        # if kind == 'sources':
            # self.source_list = devices_concat
        # else:
            # self.sink_list = devices_concat
        return devices_concat

    def get_hardware_devices(self, kind):
        command = f"pmctl list {kind}"
        devices = cmd(command).split('\n')
        devices_concat = []
        if devices[0] != '':
            for i in devices:
                jason = json.loads(i)
                devices_concat.append(jason)
        if kind == 'sources':
            self.source_list = devices_concat
        else:
            self.sink_list = devices_concat
        return devices_concat

    def mute(self, index, state=None, init=None):
        name = self.config[index[0]][index[1]]['name']
        if name == '': return

        device = 'sink' if index[0] == 'a' or index[0] == 'vi' else 'source'

        if state == None:
            state = 1 if self.config[index[0]][index[1]]['mute'] == False else 0
        self.config[index[0]][index[1]]['mute'] = True if state == 1 else False
            

        command = f"pmctl mute {device} {name} {state}\n"
        if init == None:
            os.popen(command)

        # print(command)
        return command

    def apply_eq(self, index, name=None, control=None, status=None):
        master = self.config[index[0]][index[1]]['name']
        name = index[0] + index[1] + '_eq' if name == None else name
        self.config[index[0]][index[1]]['use_eq'] = True

        if control == None:
            control = self.config[index[0]][index[1]]['eq_control']
            control = '0,0,0,0,0,0,0,0,0,0,0,0,0,0,0' if control == '' else control

        self.config[index[0]][index[1]]['eq_control'] = control

        command = f'pmctl eq init {name} {master} {control}\n'
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

    def remove_eq(self, index, name=None, init=None):
        output = index[0] + index[1]
        name = output + '_eq' if name == None else name
        master = self.config[index[0]][index[1]]['name']
        command = ''

        command += f'pmctl eq remove {name}\n'

        if init != True:
            self.config[index[0]][index[1]]['use_eq'] = False
            for i in ['hi', 'vi']:
                for j in ['1', '2', '3']:
                    if self.config[i][j][output] == True:
                        vi = self.get_correct_device([i, j], 'source')
                        command += f'pmctl disconnect {vi} {name}\n'
                        command += f'pmctl connect {vi} {master}\n'

        # print(command)
        os.popen(command)

    def set_primary(self, index, init=None):
        name = self.config[index[0]][index[1]]['name']
        for i in ['1', '2', '3']:
            self.config[index[0]][i]['primary'] = False if i != index[1] else True
        device = 'sink' if index[0] == 'vi' else 'source'
        command = f'pactl set-default-{device} {name}'
        if init == None:
            os.popen(command)
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

    def get_app_streams(self, dev_type):
        command = f'pmctl list-{dev_type}s'
        devices = cmd(command).split('\n')
        apps = []
        if devices[0] != '':
            for i in devices:
                if 'name' not in i:
                    continue
                jason = json.loads(i)
                if 'icon' not in jason:
                    jason['icon'] = 'audio-card'
                apps.append(jason)
        return apps

    def move_source_output(self, app, name):
        command = f'pmctl move-source-output {app} {name}'
        os.popen(command)

    def move_sink_input(self, app, name):
        command = f'pmctl move-sink-input {app} {name}'
        os.popen(command)

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

        for stdout_line in iter(self.vu_list[index[0]][index[1]].stdout.readline, ""):
            yield stdout_line 
            
        self.vu_list[index[0]][index[1]].stdout.close()
        return_code = self.vu_list[index[0]][index[1]].wait()
        # if return_code:
            # raise subprocess.CalledProcessError(return_code, command)

    def end_vumeter(self):
        for i in ['hi', 'vi', 'a', 'b']:
            for j in ['1','2','3']:
                if j in self.vu_list[i]:
                    self.vu_list[i][j].terminate()

    def read_config(self):

        # if config exists XDG_CONFIG_HOME 
        if os.path.isfile(CONFIG_FILE):
            self.config = json.load(open(CONFIG_FILE))

            # if config is outdated
            if not 'version' in self.config or self.config['version'] != __version__:
                config_orig = json.load(open(ORIG_CONFIG_FILE))
                self.config['version'] = __version__
                self.config['enable_vumeters'] = True
                for i in ['a', 'b', 'vi', 'hi']:
                    for j in ['1', '2', '3']:
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
