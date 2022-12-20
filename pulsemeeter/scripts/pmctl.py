import subprocess
import pulsectl
import logging
import sys

LOG = logging.getLogger('generic')


# todo: channel mapping
def init(device_type, device, channel_map=None):
    command = f'pmctl init {device_type} {device} {channel_map}'

    ret = runcmd(command)

    if ret == 126:
        LOG.error('Could not create %s %s', device_type, device)

    return ret


def remove(device):
    command = f'pmctl remove {device}'

    ret = runcmd(command)

    if ret:
        LOG.error('Could not remove %s', device)


def connect(input, output, status=True, latency=200, port_map=None):

    command = ''
    conn_status = 'connect' if status else 'disconnect'

    # auto port mapping
    if port_map is None:
        command = f'pmctl {conn_status} {input} {output} {latency}'

    # manual port mapping
    else:
        command = f'pmctl {conn_status} {input} {output} {port_map}'

    ret = runcmd(command, 4)

    return ret


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
        chann_or_lat, channel_map=None):

    status = 'connect' if status else 'disconnect'

    command = f'pmctl ladspa {status} {device_type} {name} {sink_name} {label} {plugin} {control} {chann_or_lat}'

    runcmd(command)


def rnnoise(status, name, sink_name, control,
        chann_or_lat):

    status = 'connect' if status else 'disconnect'

    command = f'pmctl rnnoise {sink_name} {name} {control} {status} "{chann_or_lat}"'

    runcmd(command)


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


def runcmd(command: str, split_size: int = -1):
    LOG.debug(command)
    command = command.split(' ', split_size)
    process = subprocess.Popen(command)
    process.wait()
    return process.returncode


# def main():
    # print(get_app_list('sink-inputs'))
    # return 0


# if __name__ == '__main__':
    # sys.exit(main())
