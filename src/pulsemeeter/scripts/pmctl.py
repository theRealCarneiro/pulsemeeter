import re
import time
import shutil
import logging
import pulsectl
import subprocess

from pulsectl import PulseSinkInfo, PulseSourceInfo, PulseSinkInputInfo, PulseSourceOutputInfo

LOG = logging.getLogger('generic')
PULSE = pulsectl.Pulse('pmctl')


def create_device(device_type: str, name: str, channels: int, position: list[str]) -> bool:
    '''
    Create a PipeWire device.
    Args:
        device_type (str): 'sink' or 'source'.
        name (str): Name of the device.
        channels (int): Number of audio channels.
        position (list[str]): Channel map positions.
    Returns:
        bool: True on success, raises on failure.
    '''

    class_map = {'sink': 'Sink', 'source': 'Source/Virtual'}

    data = f'''{{
        factory.name=support.null-audio-sink
        node.name="{name}"
        node.description="{name}"
        media.class=Audio/{class_map[device_type]}
        audio.channels={channels}
        audio.position="{' '.join(position)}"
        monitor.channel-volumes=true
        object.linger=true
    }}'''
    command = ['pw-cli', 'create-node', 'adapter', data]
    ret, stdout, stderr = run_command(command, split=False)
    if ret != 0:
        raise RuntimeError(f"Failed to create device: {stderr}")
    return True


def remove_device(name: str) -> bool:
    '''
    Remove a PipeWire device by name.
    Args:
        name (str): Name of the device to remove.
    Returns:
        bool: True on success, raises on failure.
    '''
    command = ['pw-cli', 'destroy', name]
    ret, stdout, stderr = run_command(command)
    if ret != 0:
        raise RuntimeError(f"Failed to remove device: {stderr}")
    return True


def link(input_name: str, output_name: str, state: bool = True) -> bool:
    '''
    Link or unlink two PipeWire devices (all channels).
    Args:
        input_name (str): Name of the input device.
        output_name (str): Name of the output device.
        state (bool): True to link, False to unlink.
    Returns:
        bool: True on success, raises on failure.
    '''
    operation = [] if state else ['-d']
    command = ['pw-link', input_name, output_name, *operation]
    ret, stdout, stderr = run_command(command)
    #if ret != 0:
        #raise RuntimeError(f"Failed to {'link' if state else 'unlink'} devices: {stderr}")
    return True


def link_channels(input_name: str, output_name: str, channel_map: str, state: bool = True) -> bool:
    '''
    Link or unlink two PipeWire devices using a channel map string (e.g. '0:0 1:1').
    Args:
        input_name (str): Name of the input device.
        output_name (str): Name of the output device.
        channel_map (str): Channel map string, e.g. '0:0 1:1'.
        state (bool): True to link, False to unlink.
    Returns:
        bool: True on success, raises on failure.
    '''
    if not channel_map:
        return True

    input_ports = get_ports('output', input_name)
    output_ports = get_ports('input', output_name)

    if not input_ports or not output_ports:
        raise RuntimeError(f'Ports not found for devices {input_name} {output_name}')

    for pair in channel_map.split(' '):
        input_id, output_id = pair.split(':')
        input_port = f'{input_name}:{input_ports[int(input_id)]}'
        output_port = f'{output_name}:{output_ports[int(output_id)]}'
        link(input_port, output_port, state=state)

    return True


def make_loopback_name(input_name: str, output_name: str) -> str:
    '''
    Generate a deterministic loopback name for a connection.
    Sanitizes to alphanumeric, underscores, hyphens, and dots only.
    Args:
        input_name (str): Name of the input device.
        output_name (str): Name of the output device.
    Returns:
        str: Sanitized loopback name.
    '''
    raw = f'pm_route_{input_name}_to_{output_name}'
    return re.sub(r'[^a-zA-Z0-9._-]', '_', raw)


def make_intermediate_sink_name(loopback_name: str) -> str:
    '''
    Generate a deterministic intermediate sink name for a b-type loopback connection.
    Args:
        loopback_name (str): The loopback name from make_loopback_name().
    Returns:
        str: The intermediate sink name ({loopback_name}_bridge).
    '''
    return f'{loopback_name}_bridge'


def create_intermediate_sink(loopback_name: str, channels: int, position: list[str]) -> str:
    '''
    Create a temporary intermediate sink for b-type loopback routing.
    Args:
        loopback_name (str): The loopback name from make_loopback_name().
        channels (int): Number of audio channels.
        position (list[str]): Channel map positions.
    Returns:
        str: The intermediate sink name.
    '''
    sink_name = make_intermediate_sink_name(loopback_name)
    create_device('sink', sink_name, channels, position)
    return sink_name


def remove_intermediate_sink(loopback_name: str):
    '''
    Remove a temporary intermediate sink for b-type loopback routing.
    Args:
        loopback_name (str): The loopback name from make_loopback_name().
    '''
    sink_name = make_intermediate_sink_name(loopback_name)
    try:
        remove_device(sink_name)
    except RuntimeError:
        LOG.warning('Failed to remove intermediate sink %s', sink_name)


def wait_for_device(device_type: str, device_name: str, timeout: float = 2.0, interval: float = 0.05) -> bool:
    '''
    Poll until a device appears in PulseAudio.
    Args:
        device_type (str): 'sink' or 'source'.
        device_name (str): Name of the device.
        timeout (float): Maximum time to wait in seconds.
        interval (float): Polling interval in seconds.
    Returns:
        bool: True if found, False if timed out.
    '''
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if get_device_by_name(device_type, device_name) is not None:
            return True
        time.sleep(interval)
    return False


def get_device_serial(device_type: str, device_name: str) -> str:
    '''
    Get the PipeWire object.serial for a device.
    Args:
        device_type (str): 'sink' or 'source'.
        device_name (str): Name of the device.
    Returns:
        str: The object.serial, or empty string if not found.
    '''
    device = get_device_by_name(device_type, device_name)
    if device:
        return device.proplist.get('object.serial', '')
    return ''


def create_loopback(name: str, capture_serial: str, playback_serial: str, channels: int) -> subprocess.Popen:
    '''
    Spawn a pw-loopback subprocess for per-route volume control.
    Targets devices by PipeWire object.serial for unambiguous routing.
    Args:
        name (str): Unique loopback name.
        capture_serial (str): PipeWire object.serial of the capture device.
        playback_serial (str): PipeWire object.serial of the playback device.
        channels (int): Number of audio channels.
    Returns:
        subprocess.Popen: The loopback subprocess handle.
    '''
    command = [
        'pw-loopback',
        '--name', name,
        '--channels', str(channels),
        '--capture-props', f'target.object={capture_serial}',
        '--playback-props', f'target.object={playback_serial}',
    ]

    LOG.debug('Creating loopback: %s', command)
    proc = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return proc


def destroy_loopback(proc: subprocess.Popen):
    '''
    Terminate a pw-loopback subprocess.
    Args:
        proc (subprocess.Popen): The loopback process to terminate.
    '''
    if proc and proc.poll() is None:
        proc.terminate()
        try:
            proc.wait(timeout=3)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait()
    LOG.debug('Loopback destroyed (pid=%s)', proc.pid if proc else None)


def set_route_volume(loopback_name: str, volume: int) -> bool:
    '''
    Set the volume of a pw-loopback sink-input by its loopback name.
    Args:
        loopback_name (str): The loopback name used when creating.
        volume (int): Volume value (0-153).
    Returns:
        bool: True on success, False if sink-input not found.
    '''
    volume = min(max(0, volume), 153)
    try:
        for si in PULSE.sink_input_list():
            if loopback_name in si.name:
                channels = len(si.volume.values)
                vol = pulsectl.PulseVolumeInfo(volume / 100, channels)
                PULSE.volume_set(si, vol)
                return True
    except pulsectl.PulseError:
        LOG.error('Failed to set route volume for %s', loopback_name)
    return False


def wait_for_loopback(loopback_name: str, timeout: float = 2.0, interval: float = 0.05) -> bool:
    '''
    Poll until the pw-loopback sink-input appears in PulseAudio.
    Args:
        loopback_name (str): The loopback name to wait for.
        timeout (float): Maximum time to wait in seconds.
        interval (float): Polling interval in seconds.
    Returns:
        bool: True if found, False if timed out.
    '''
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            for si in PULSE.sink_input_list():
                if loopback_name in si.name:
                    return True
        except pulsectl.PulseError:
            pass
        time.sleep(interval)
    return False


def loopback_exists(loopback_name: str) -> bool:
    '''
    Check if a pw-loopback sink-input with the given name already exists.
    Args:
        loopback_name (str): The loopback name to check for.
    Returns:
        bool: True if found.
    '''
    try:
        for si in PULSE.sink_input_list():
            if loopback_name in si.name:
                return True
    except pulsectl.PulseError:
        pass
    return False


def get_ports(port_type: str, device_name: str) -> list[str]:
    '''
    Get ports for a device in PipeWire.
    Args:
        port_type (str): 'input' or 'output'.
        device_name (str): Name of the device.
    Returns:
        list[str]: list of port names.
    '''
    command = ['pmctl', 'get_ports', port_type, device_name]
    ret, stdout, stderr = run_command(command)
    if ret != 0:
        raise RuntimeError(f"Failed to get ports: {stderr}")

    ports = stdout.split()
    if not ports or ports[0] == '':
        return []

    return ports


def mute(device_type: str, device_name: str, state: bool, pulse=None) -> int:
    '''
    Change mute state of a device.
    Args:
        device_type (str): 'sink' or 'source'.
        device_name (str): Name of the device.
        state (bool): True to mute, False to unmute.
        pulse: Optional Pulse object. If None, PULSE is used.
    Returns:
        int: 0 on success, -1 on failure.
    '''
    if pulse is None:
        pulse = PULSE

    device = get_device_by_name(device_type, device_name)

    if device is None:
        LOG.error('Device not found %s', device_name)
        return False

    pulse.mute(device, state)
    return True


def set_primary(device_type: str, device_name: str, pulse=None) -> bool:
    '''
    Set a device as primary.
    Args:
        device_type (str): 'sink' or 'source'.
        device_name (str): Name of the device.
        pulse: Optional Pulse object. If None, PULSE is used.
    Returns:
        int: 0 on success, -1 on failure.
    '''
    if pulse is None:
        pulse = PULSE

    device = get_device_by_name(device_type, device_name)

    if device is None:
        LOG.error('Device not found %s', device_name)
        return False

    pulse.default_set(device)

    return True


def set_volume(device_type: str, device_name: str, val: int, selected_channels: list[bool] = None) -> bool:
    '''
    Change device volume.
    Args:
        device_type (str): 'sink' or 'source'.
        device_name (str): Name of the device.
        val (int): Volume value (0-153).
        selected_channels (list): List of booleans indicating which channels to change.
    Returns:
        int: 0 on success, -1 on failure.
    '''
    val = min(max(0, val), 153)

    device = get_device_by_name(device_type, device_name)

    if device is None:
        LOG.error('Device not found %s', device_name)
        return False

    # set the volume
    volume_value = device.volume

    # set by channel
    channels = len(device.volume.values)
    volume_list = []

    if selected_channels is None:
        volume_value.value_flat = val / 100
        PULSE.volume_set(device, volume_value)
        return True

    for channel in range(channels):

        # change volume for selected channel
        if selected_channels[channel] is True:
            volume_list.append(val / 100)

        # channels that are not selected don't have their volume changed
        else:
            volume_list.append(device.volume.values[channel])

    volume_value = pulsectl.PulseVolumeInfo(volume_list)

    PULSE.volume_set(device, volume_value)
    return True


def device_exists(device_name: str) -> bool:
    '''
    Check if a device exists by name (sink or source).
    Args:
        device_name (str): The name of the device to check.
    Returns:
        bool: True if the device exists, False otherwise.
    '''
    source_exists = get_device_by_name('source', device_name)
    sink_exists = get_device_by_name('sink', device_name)
    return source_exists is not None or sink_exists is not None


def get_primary(device_type: str, pulse=None) -> PulseSinkInfo | PulseSourceInfo:
    '''
    Get the primary device.
    Args:
        device_type (str): 'sink' or 'source'.
        pulse: Optional Pulse object. If None, PULSE is used.
    Returns:
        Device object or None.
    '''
    if pulse is None:
        pulse = PULSE

    if device_type == 'sink':
        return pulse.sink_default_get()
    return pulse.source_default_get()


def get_device_by_name(device_type: str, device_name: str) -> PulseSinkInfo | PulseSourceInfo:
    '''
    Get a device object by type and name.
    Args:
        device_type (str): 'sink' or 'source'.
        device_name (str): Name of the device.
    Returns:
        Device object or None if not found.
    '''
    try:
        if device_type == 'sink':
            return PULSE.get_sink_by_name(device_name)

        return PULSE.get_source_by_name(device_name)
    except pulsectl.pulsectl.PulseIndexError:
        return None


def get_device_by_index(device_type: str, device_index: str) -> PulseSinkInfo | PulseSourceInfo:
    '''
    Get a device object by type and name.
    Args:
        device_type (str): 'sink' or 'source'.
        device_index (str): Index of the device on pulse.
    Returns:
        Device object or None if not found.
    '''
    try:
        if device_type == 'sink':
            return PULSE.sink_info(device_index)

        return PULSE.source_info(device_index)
    except pulsectl.pulsectl.PulseIndexError:
        return None


def get_app_device(app_type: str, app: PulseSinkInputInfo | PulseSourceOutputInfo) -> PulseSinkInfo | PulseSourceInfo:
    '''
    Get a device object by type and name.
    Args:
        device_type (str): 'sink' or 'source'.
        device_index (str): Index of the device on pulse.
    Returns:
        Device object or None if not found.
    '''
    try:
        if app_type == 'sink_input':
            return PULSE.sink_info(app.sink)

        return PULSE.source_info(app.source)
    except pulsectl.pulsectl.PulseIndexError:
        return None


def app_mute(app_type: str, index: int, state: bool) -> bool:
    '''
    Mute or unmute an application stream by type and index.
    Args:
        app_type (str): 'sink_input' or 'source_output'.
        index (int): Index of the application stream.
        state (bool): True to mute, False to unmute.
    Returns:
        int: 0 on success, -1 on failure.
    '''
    app = app_by_id(index, app_type)
    PULSE.mute(app, state)

    return True


def app_volume(app_type: str, index: int, val: int) -> bool:
    '''
    Set the volume of an application stream by type and index.
    Args:
        app_type (str): 'sink_input' or 'source_output'.
        index (int): Index of the application stream.
        val (int): Volume value (0-153).
    Returns:
        int: 0 on success, -1 on failure.
    '''
    app = app_by_id(index, app_type)
    channels = len(app.volume.values)
    volume = pulsectl.PulseVolumeInfo(val / 100, channels)
    PULSE.volume_set(app, volume)
    return True


def get_default_device_name(app_type: str) -> str:
    '''
    Get the default sink or source device name.
    Args:
        app_type (str): 'sink_input' or 'source_output'.
    Returns:
        str: The default device name.
    '''
    info = PULSE.server_info()
    if app_type == 'sink_input':
        return info.default_sink_name
    return info.default_source_name


def move_app_device(app_type: str, index: int, device_name: str) -> bool:
    '''
    Move an application stream to a different device.
    Args:
        app_type (str): 'sink_input' or 'source_output'.
        index (int): Index of the application stream.
        device_name (str): Name of the new device.
    Returns:
        int: 0 on success, -1 on failure.
    '''
    device_type = 'sink' if app_type == 'sink_input' else 'source'
    device = get_device_by_name(device_type, device_name)
    move = PULSE.sink_input_move if app_type == 'sink_input' else PULSE.source_output_move

    try:
        move(index, device.index)

    # some apps have DONT MOVE flag, the app will crash
    except pulsectl.PulseOperationFailed:
        LOG.debug('App #%d device cant be moved', index)

    return True


def is_hardware_device(device: PulseSinkInfo | PulseSourceInfo) -> bool:
    '''
    Determine if a device is a hardware device (not a monitor or null sink).
    Args:
        device: The device object to check.
    Returns:
        bool: True if hardware, False otherwise.
    '''
    is_easy = 'easyeffects_' in device.name
    is_monitor = device.proplist.get('device.class') == "monitor"
    is_null = device.proplist.get('factory.name') == 'support.null-audio-sink'

    if not is_monitor and (not is_null or is_easy):
        return True

    return False


def list_devices(device_type: str) -> list[PulseSinkInfo | PulseSourceInfo]:
    '''
    List all hardware devices of a given type (sink or source).
    Args:
        device_type (str): 'sink' or 'source'.
    Returns:
        list: List of hardware device objects.
    '''
    pulse = pulsectl.Pulse()
    list_pa_devices = pulse.sink_list if device_type == 'sink' else pulse.source_list
    device_list = []
    for device in list_pa_devices():
        if is_hardware_device(device):
            device_list.append(device)

    return device_list


def app_by_id(index: int, app_type: str) -> PulseSinkInputInfo | PulseSourceOutputInfo:
    '''
    Return a specific app by index and type.
    Args:
        index (int): Index of the application stream.
        app_type (str): 'sink_input' or 'source_output'.
    Returns:
        App object.
    '''
    app_info = PULSE.sink_input_info if app_type == 'sink_input' else PULSE.source_output_info
    app = app_info(index)
    device_type = 'sink' if app_type == 'sink_input' else 'source'
    device = get_device_by_index(device_type, app.sink)
    app.device_name = device.name
    return app


def list_apps(app_type: str) -> list[PulseSinkInputInfo | PulseSourceOutputInfo]:
    '''
    List all application streams of a given type, filtering out pavucontrol and peak sinks.
    Args:
        app_type (str): 'sink_input' or 'source_output'.
    Returns:
        list: List of application stream objects.
    '''
    app_list = []
    full_app_list = PULSE.sink_input_list() if app_type == 'sink_input' else PULSE.source_output_list()

    for app in full_app_list:

        hasname = app.proplist.get('application.name', False)
        is_peak = '_peak' in app.proplist.get('application.name', '')
        is_pavucontrol = app.proplist.get('application.id') == 'org.PulseAudio.pavucontrol'
        is_pm_loopback = 'pm_route_' in app.proplist.get('node.name', '')
        if is_peak or is_pavucontrol or is_pm_loopback or not hasname:
            continue

        app.device_name = get_app_device(app_type, app).name
        app_list.append(app)

    return app_list


def is_pipewire() -> bool:
    '''
    Check if pulseaudio is available on the system.
    Returns:
        bool: True if pulseaudio is available, False otherwise.
    '''
    return shutil.which('pipewire-pulse') is not None


def is_pulse() -> bool:
    '''
    Check if pulseaudio is available on the system.
    Returns:
        bool: True if pulseaudio is available, False otherwise.
    '''
    return shutil.which('pulseaudio') is not None


def decode_event(event: pulsectl.PulseEventInfo) -> tuple[str, str, int]:
    '''
    Receives a PulseEventInfo and returns the str version of .t and .facility
    Returns:
        tuple[str, str, int]: facility, event type and object index respectively
    '''
    return str_facility(event.facility), str_event_type(event.t), event.index


def str_facility(facility: pulsectl.PulseEventFacilityEnum) -> str:
    '''
    Receives a PulseEventFacilityEnum and returns the str version
    Returns:
        str: The str name of the facility e.g. sink
    '''
    return getattr(facility, '_value', None)


def str_event_type(event_type: pulsectl.PulseEventFacilityEnum) -> str:
    '''
    Receives a PulseEventFacilityEnum and returns the str version
    Returns:
        str: The str name of the facility e.g. sink
    '''
    return getattr(event_type, '_value', None)


def run_command(command: list[str], split: bool = False) -> tuple[int, str, str]:
    """
    Run a shell command and return (returncode, stdout, stderr).
    If split is True, split the command string into a list.
    """
    if split and isinstance(command, str):
        command = command.split()
    LOG.debug('Running command: %s', command)
    proc = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = proc.communicate()
    return proc.returncode, stdout.decode(), stderr.decode()
