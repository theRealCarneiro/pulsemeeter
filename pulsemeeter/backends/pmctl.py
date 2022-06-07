import sys
import os
import json
import subprocess


# todo: channel mapping
def init(device_type, device, channel_map=None, run_command=False):
    command = f'pmctl init {device_type} {device} "{channel_map}"\n'

    if run_command is True: os.popen(command)
    return command


def remove(device, run_command=False):
    command = f'pmctl remove {device}\n'

    if run_command is True: os.popen(command)
    return command


def connect(input, output, status=True, latency=200, port_map=None, run_command=False):

    command = ''
    conn_status = 'connect' if status else 'disconnect'

    # command = [[f'pmctl {conn_status} {i} {o} {latency}\n' for o in port_map[i]] for i in port_map]

    # auto port mapping
    if port_map is None:
        command = f'pmctl {conn_status} {input} {output} {latency}\n'

    # manual port mapping
    else:
        for iport in port_map:
            for oport in port_map[iport]:
                command += f'pmctl {conn_status} {input}:{iport} {output}:{oport} {latency}\n'

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

    command = f'pmctl mute {device_type} {device} {state}'

    if run_command is True: os.popen(command)
    return command


def set_primary(device_type, device_name, run_command=False):

    command = f'pmctl set-primary {device_type} {device_name}\n'

    if run_command: os.popen(command)

    return command


def list(device_type):
    command = f'pmctl list {device_type}'

    try:
        devices = json.loads(cmd(command))
    except Exception:
        devices = []

    return devices


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
        raise
    return stdout.decode()


# def main():
    # connect(['a', 'b'], 'ca', True)
    # list('sinks')
    # return 0


# if __name__ == '__main__':
    # sys.exit(main())
