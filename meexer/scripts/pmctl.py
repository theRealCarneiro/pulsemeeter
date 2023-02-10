import subprocess
import pulsectl
import logging
import sys

LOG = logging.getLogger('generic')

PULSE = pulsectl.Pulse('pmctl')


# todo: channel mapping
def init(device_type: str, device_name: str, channel_num: int = 2):
    '''
    Create a device in pulse
        "device_type" is either sink or source
        "device_name" is the device name
        "channel_num" is the number of channels
    '''
    command = f'pmctl init {device_type} {device_name} {channel_num}'

    ret = runcmd(command)

    if ret == 126:
        LOG.error('Could not create %s %s', device_type, device_name)

    return ret


def remove(device_name: str):
    '''
    Destroy a device in pulse
        "device_name" is the device name
    '''
    command = f'pmctl remove {device_name}'

    ret = runcmd(command)

    # if ret:
        # LOG.error('Could not remove %s', device_name)

    return ret


def connect(input: str, output: str, status: bool, latency: bool = 200, port_map=None):
    '''
    Connect two devices (pulse or pipewire)
        "input" is the name of the input device
        "output" is the name of the output device
        "status" is a bool, True means connect, False means disconnect
        "latency" is the latency of the connection (pulseaudio only)
        "port_map" is a list of channels that will be connected,
            leave empty to let pipewire decide
    '''

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


def mute(device_type: DeviceType, device_name: str, state: bool, pulse=None):
    '''
    Change mute state of a device
        "device_type" is the enum DeviceType
        "device_name" is the device name
        "state" is bool, True means mute, False means unmute
    '''

    if pulse is None:
        pulse = PULSE

    info = pulse.get_sink_by_name if device_type == 'sink' else pulse.get_source_by_name
    device = info(device_name)
    pulse.mute(device, state)

    return 0


def set_primary(device_type: DeviceType, device_name: str, pulse=None):
    '''
    Change mute state of a device
        "device_type" is the enum DeviceType
        "device_name" is the device name
    '''

    if pulse is None:
        pulse = PULSE

    info = pulse.get_sink_by_name if device_type == 'sink' else pulse.get_source_by_name
    device = info(device_name)
    pulse.default_set(device)

    return 0


def volume(device_type: str, device_name: str, val: int, selected_channels: list = None):
    '''
    Change device volume
        "device_type" either sink or source
        "device_name" device name
        "val" new volume level
        "selected_channels" the channels that will have the volume changed
    '''

    # limit volume at 153
    if val > 153:
        val = 153

    # limit volume at 0
    elif val < 0:
        val = 0

    # get device info from pulsectl
    if device_type == 'sink':
        device = PULSE.get_sink_by_name(device_name)
    else:
        device = PULSE.get_source_by_name(device_name)

    # set the volume
    volume = device.volume

    # set by channel
    nchan = len(device.volume.values)
    vollist = device.volume.values
    v = []
    if selected_channels is not None:
        for c in range(nchan):
            v.append(val / 100 if selected_channels[c] is True else vollist[c])
        volume = pulsectl.PulseVolumeInfo(v)
    else:
        volume.value_flat = val / 100

    PULSE.volume_set(device, volume)
    return 0


def list_sinks(hardware=False, virtual=False, all=False):
    PULSE = pulsectl.Pulse()
    device_list = []
    if hardware is True:
        for device in PULSE.sink_list():

            pa_sink_hardware = 0x0004
            if device.flags & pa_sink_hardware:
                device_list.append(device)

    return device_list


def list_sources(hardware=False, virtual=False):
    PULSE = pulsectl.Pulse()
    pulse_devices = PULSE.source_list()
    device_list = []
    if hardware is True or virtual is True:
        for device in pulse_devices:

            pa_sink_hardware = 0x0004
            if device.flags & pa_sink_hardware:
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
