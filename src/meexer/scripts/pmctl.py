import logging
import sys
import subprocess
import pulsectl

LOG = logging.getLogger('generic')
PULSE = pulsectl.Pulse('pmctl')


# TODO: channel mapping
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

    return ret


def connect(input_name: str, output: str, status: bool, latency: bool = 200, port_map=None):
    '''
    Connect two devices (pulse or pipewire)
        "input_name" is the name of the input_name device
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
        command = f'pmctl {conn_status} {input_name} {output} {latency}'

    # manual port mapping
    else:
        command = f'pmctl {conn_status} {input_name} {output} {port_map}'

    ret = runcmd(command, 4)

    return ret


def ladspa(status, device_type, name, sink_name, label, plugin, control,
        chann_or_lat):

    status = 'connect' if status else 'disconnect'

    command = f'pmctl ladspa {status} {device_type} {name} {sink_name} {label} {plugin} {control} {chann_or_lat}'

    runcmd(command)


def rnnoise(status, name, sink_name, control,
        chann_or_lat):

    status = 'connect' if status else 'disconnect'

    command = f'pmctl rnnoise {sink_name} {name} {control} {status} "{chann_or_lat}"'

    runcmd(command)


def mute(device_type: str, device_name: str, state: bool, pulse=None):
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


def set_primary(device_type: str, device_name: str, pulse=None):
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


def set_volume(device_type: str, device_name: str, val: int, selected_channels: list = None):
    '''
    Change device volume
        "device_type" either sink or source
        "device_name" device name
        "val" new volume level
        "selected_channels" the channels that will have the volume changed
    '''

    val = min(max(0, val), 153)

    # get device info from pulsectl
    if device_type == 'sink':
        device = PULSE.get_sink_by_name(device_name)
    else:
        device = PULSE.get_source_by_name(device_name)

    # set the volume
    volume_value = device.volume

    # set by channel
    channels = len(device.volume.values)
    volume_list = []

    # change specific channels
    if selected_channels is not None:
        for channel in range(channels):

            # change volume for selected channel
            if selected_channels[channel] is True:
                volume_list.append(val / 100)

            # channels that are not selected don't have their volume changed
            else:
                volume_list.append(device.volume.values[channel])

        volume_value = pulsectl.PulseVolumeInfo(volume_list)

    # all channels
    else:
        volume_value.value_flat = val / 100

    PULSE.volume_set(device, volume_value)
    return 0


def app_mute(app_type: str, index: int, state: bool):
    '''
    Mute an app by their type and index
        "app_type" is either sink_input or source_output
        "index" is the index of the app in pulse
        "state" True is mute and False is unmute
    '''

    if app_type == 'sink_input':
        app = PULSE.sink_input_info(index)
    else:
        app = PULSE.source_output_info(index)

    PULSE.mute(app, state)

    return 0


def app_volume(app_type: str, index: int, val: int):

    # limit volume at 153
    if val > 153:
        val = 153
    elif val < 0:
        val = 0

    # set volume object
    try:
        if app_type == 'sink_input':
            device = PULSE.sink_input_info(index)
            chann = len(device.volume.values)
            volume = pulsectl.PulseVolumeInfo(val / 100, chann)
            PULSE.sink_input_volume_set(index, volume)
        else:
            device = PULSE.source_output_info(index)
            chann = len(device.volume.values)
            volume = pulsectl.PulseVolumeInfo(val / 100, chann)
            PULSE.source_output_volume_set(index, volume)

    # trying to change volume of a device that just desapears
    # better to just ignore it, nothing bad comes from doing so
    except pulsectl.PulseIndexError:
        LOG.debug('App #%d already removed', index)

    return 0


def move_app_device(app_type: str, index: int, device_name: str):
    try:
        if app_type == 'sink_input':
            sink = PULSE.get_sink_by_name(device_name)
            PULSE.sink_input_move(index, sink.index)
        else:
            source = PULSE.get_source_by_name(device_name)
            PULSE.source_output_move(index, source.index)

    # some apps have DONT MOVE flag, the app will crash
    except pulsectl.PulseOperationFailed:
        LOG.debug('App #%d device cant be moved', index)

    return 0


def list_devices(device_type):
    pulse = pulsectl.Pulse()
    list_pa_devices = pulse.sink_list if device_type == 'sink' else pulse.source_list
    device_list = []
    for device in list_pa_devices():

        # pa_sink_hardware = 0x0004
        # if device.flags & pa_sink_hardware:

        if (device.proplist['factory.name'] != 'support.null-audio-sink' and
                device.proplist['device.class'] != "monitor"):
            device_list.append(device)

    return device_list


def list_sinks(hardware=False):
    pulse = pulsectl.Pulse()
    device_list = []
    if hardware is True:
        for device in pulse.sink_list():

            pa_sink_hardware = 0x0004
            if device.flags & pa_sink_hardware:
                device_list.append(device)

    return device_list


def list_sources(hardware=False, virtual=False):
    pulse = pulsectl.Pulse()
    pulse_devices = pulse.source_list()
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


def filter_results(app):
    '''
    Filter pavu and pm peak sinks
    '''
    assert 'application.name' in app.proplist
    assert '_peak' not in app.proplist['application.name']
    assert app.proplist.get('application.id') != 'org.PulseAudio.pavucontrol'


def app_by_id(index: int, app_type: str):
    '''
    Return a specific app
        "index" is the index of the desidered app
        "app_type" is sink_input or source_output
    '''
    app_info = PULSE.sink_input_info if app_type == 'sink_input' else PULSE.source_output_info
    app = app_info(index)

    if app_type == 'sink_input':
        app.device_name = PULSE.sink_info(app.sink).name
    else:
        app.device_name = PULSE.source_info(app.sink).name

    return app


def list_apps(app_type: str):
    app_list = []

    if app_type == 'sink_input':
        full_app_list = PULSE.sink_input_list()

    elif app_type == 'source_output':
        full_app_list = PULSE.source_output_list()

    for app in full_app_list:

        # filter pavu and pm peak sinks
        try:
            filter_results(app)
        except AssertionError:
            continue

        if app_type == 'sink_input':
            app.device_name = PULSE.sink_info(app.sink).name
        else:
            app.device_name = PULSE.source_info(app.sink).name

        app_list.append(app)
    return app_list


def get_pactl_version():
    return int(cmd('pmctl get-pactl-version'))


def cmd(command):
    sys.stdout.flush()
    with subprocess.Popen(command.split(' '), stdout=subprocess.PIPE) as proc:
        stdout, stderr = proc.communicate()
        if proc.returncode:
            LOG.warning('%s \ncmd "%s" returned %d', stderr, command, proc.returncode)
    return stdout.decode()


def runcmd(command: str, split_size: int = -1):
    LOG.debug(command)
    command = command.split(' ', split_size)
    with subprocess.Popen(command) as process:
        process.wait()
        return_code = process.returncode

    return return_code
