import sys
import os
import json
import subprocess
import logging

LOG = logging.getLogger('generic')

# todo: channel mapping
def init(device_type, device, channel_map=None, run_command=False):
    command = f'pmctl init {device_type} {device} "{channel_map}"\n'

    if run_command is True: os.popen(command)
    return command


def remove(device, run_command=False):
    command = f'pmctl remove {device}\n'

    if run_command is True: os.popen(command)
    return command


def connect(input, output, status=True, latency=200, port_map=None,
            input_ports=None, output_ports=None, run_command=False):

    command = ''
    conn_status = 'connect' if status else 'disconnect'

    # auto port mapping
    if port_map is None:
        command = f'pmctl {conn_status} {input} {output} {latency}\n'

    # manual port mapping
    else:
        command = f'pmctl {conn_status} {input} {output} "{port_map}"\n'

    if run_command is True: os.popen(command)
    return command


def disconnect(input, output, run_command=False):

    if type(input) == str:
        input = [input]

    if type(output) == str:
        output = [output]

    command = ''
    for i in input:
        for o in output:
            command += f'pmctl disconnect {i} {o}\n'

    if run_command is True: os.popen(command)
    return command


def mute(device_type, device, state, run_command=False):

    command = f'pmctl mute {device_type} {device} {state}\n'

    if run_command is True: os.popen(command)
    return command


def set_primary(device_type, device_name, run_command=False):

    command = f'pmctl set-primary {device_type} {device_name}\n'

    if run_command: os.popen(command)
    return command


def ladspa(status, device_type, name, sink_name, label, plugin, control,
        chann_or_lat, channel_map=None, run_command=False):

    status = 'connect' if status else 'disconnect'

    command = f'pmctl ladspa {status} {device_type} {name} {sink_name} {label} {plugin} {control} {chann_or_lat}\n'

    if run_command: os.popen(command)
    return command


def list(device_type, device_name=None):
    command = f'pmctl list {device_type}'

    try:
        devices = json.loads(cmd(command))
        if device_name is not None:
            for i in devices:
                if i['name'] == device_name:
                    devices = i
                    break
    except Exception:
        devices = []

    return devices


def get_ports(device, device_type):
    return cmd(f'pmctl get-ports {device_type} {device}').split('\n')

def get_pactl_version():
    return int(cmd('pmctl get-pactl-version'))

def get_stream_volume(stream_type, app_id):
    return cmd(f'pmctl get-{stream_type}-volume {app_id}')


def subscribe():
    command = ['pactl', 'subscribe']
    sys.stdout.flush()
    env = os.environ
    env['LC_ALL'] = 'C'
    sub_proc = subprocess.Popen(command, env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        universal_newlines=True)

    return sub_proc


def cmd(command):
    sys.stdout.flush()
    p = subprocess.Popen(command.split(' '),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT)
    stdout, stderr = p.communicate()
    if p.returncode:
        LOG.warning(f'cmd \'{command}\' returned {p.returncode}')
    return stdout.decode()


# def main():
    # print(get_ports('Main', 'output'))
    # return 0


# if __name__ == '__main__':
    # sys.exit(main())
