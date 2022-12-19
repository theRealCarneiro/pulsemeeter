import pulsemeeter.scripts.patojson as patojson
import subprocess
import pulsectl
# import traceback
import logging
import sys
import os

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


def mute(device_type, name, state, pulse=None):

    info = pulse.get_sink_by_name if device_type == 'sink' else pulse.source_by_name
    device = info(name)
    pulse.mute(device, state)

    return 0


def set_primary(device_type, name, pulse=None):

    info = pulse.get_sink_by_name if device_type == 'sink' else pulse.source_by_name
    device = info(name)
    pulse.default_set(device)

    return 0


def ladspa(status, device_type, name, sink_name, label, plugin, control,
        chann_or_lat, channel_map=None, run_command=False):

    status = 'connect' if status else 'disconnect'

    command = f'pmctl ladspa {status} {device_type} {name} {sink_name} {label} {plugin} {control} {chann_or_lat}\n'

    if run_command: os.popen(command)
    return command


def rnnoise(status, name, sink_name, control,
        chann_or_lat, run_command=False):

    status = 'connect' if status else 'disconnect'

    command = f'pmctl rnnoise {sink_name} {name} {control} {status} "{chann_or_lat}"\n'

    if run_command: os.popen(command)
    return command


def list_sinks(hardware=False, virtual=False, all=False):
    PULSE = pulsectl.Pulse()
    device_list = []
    if hardware is True:
        for device in PULSE.sink_list():

            # 0x0004 is PA_SINK_HARDWARE
            if device.flags & 0x0004:
                device_list.append(device)

    return device_list


def list_sources(hardware=False, virtual=False):
    PULSE = pulsectl.Pulse()
    pulse_devices = PULSE.source_list()
    device_list = []
    if hardware is True or virtual is True:
        for device in pulse_devices:

            # 0x0004 is PA_SINK_HARDWARE
            if device.flags & 0x0004:
                if hardware and device.proplist['device.class'] != 'monitor':
                    device_list.append(device)
            elif virtual:
                device_list.append(device)
    else:
        device_list = pulse_devices

    return device_list


def list_sink_inputs(index=None):
    si_list = None
    PULSE = pulsectl.Pulse()
    if index is not None:
        try:
            device = PULSE.sink_input_info(int(index))
        except pulsectl.PulseIndexError:
            return []
        si_list = [device]
    else:
        si_list = PULSE.sink_input_list()

    app_list = []
    for app in si_list:

        # filter pavu and pm peak sinks
        if ('application.name' not in app.proplist or
            '_peak' in app.proplist['application.name'] or
            'application.id' in app.proplist and
                app.proplist['application.id'] == 'org.PulseAudio.pavucontrol'):
            continue

        # some apps don't have icons
        if 'application.icon_name' not in app.proplist:
            app.proplist['application.icon_name'] = 'audio-card'

        index = app.index
        icon = app.proplist['application.icon_name']
        label = app.proplist['application.name']
        volume = int(app.volume.values[0] * 100)
        device = PULSE.sink_info(app.sink)
        app_list.append((index, label, icon, volume, device.name))
    return app_list


def list_source_outputs(index=None):
    PULSE = pulsectl.Pulse()
    if index is not None:
        try:
            device = PULSE.source_output_info(int(index))
        except pulsectl.PulseIndexError:
            return []
        si_list = [device]
    else:
        si_list = PULSE.source_output_list()

    app_list = []
    for app in si_list:

        # filter pavu and pm peak sinks
        if ('application.name' not in app.proplist or
            '_peak' in app.proplist['application.name'] or
            'application.id' in app.proplist and
                app.proplist['application.id'] == 'org.PulseAudio.pavucontrol'):
            continue

        # some apps don't have icons
        if 'application.icon_name' not in app.proplist:
            app.proplist['application.icon_name'] = 'audio-card'

        index = app.index
        icon = app.proplist['application.icon_name']
        label = app.proplist['application.name']
        volume = int(app.volume.values[0] * 100)
        device = PULSE.source_info(app.source)
        app_list.append((index, label, icon, volume, device.name))
    return app_list


def get_pactl_version():
    return int(cmd('pmctl get-pactl-version'))


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
    # print(get_app_list('sink-inputs'))
    # return 0


# if __name__ == '__main__':
    # sys.exit(main())
