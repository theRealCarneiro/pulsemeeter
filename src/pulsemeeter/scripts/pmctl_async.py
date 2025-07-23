import asyncio
import logging
import pulsectl
import pulsectl_asyncio

from pulsemeeter.model.types import PulseEvent

LOG = logging.getLogger('generic')
# PULSE = pulsectl.Pulse('pmctl')

# TODO: Use a single PulseAsync object

PULSE = pulsectl_asyncio.PulseAsync('pmctl_async')


async def init(device_type: str, device_name: str, channel_num: int = 2):
    '''
    Create a device in pulse
        "device_type" is either sink or source
        "device_name" is the device name
        "channel_num" is the number of channels
    '''
    command = f'pmctl init {device_type} {device_name} {channel_num}'

    ret = await runcmd(command)

    if ret == 126:
        LOG.error('Could not create %s %s', device_type, device_name)

    return ret


async def remove(device_name: str):
    '''
    Destroy a device in pulse
        "device_name" is the device name
    '''
    command = f'pmctl remove {device_name}'

    ret = await runcmd(command)

    return ret


async def connect(input_name: str, output: str, status: bool, latency: bool = 200, port_map=None):
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

    ret = await runcmd(command, 4)

    return ret


# TODO: do
async def ladspa(status, device_type, name, sink_name, label, plugin, control,
        chann_or_lat):

    status = 'connect' if status else 'disconnect'

    command = f'pmctl ladspa {status} {device_type} {name} {sink_name} {label} {plugin} {control} {chann_or_lat}'

    runcmd(command)


# TODO: do
async def rnnoise(status, name, sink_name, control,
        chann_or_lat):

    status = 'connect' if status else 'disconnect'

    command = f'pmctl rnnoise {sink_name} {name} {control} {status} "{chann_or_lat}"'

    runcmd(command)


async def mute(device_type: str, device_name: str, state: bool):
    '''
    Change mute state of a device
        "device_type" is the enum DeviceType
        "device_name" is the device name
        "state" is bool, True means mute, False means unmute
    '''

    async with pulsectl_asyncio.PulseAsync() as pulse:
        info = pulse.get_sink_by_name if device_type == 'sink' else pulse.get_source_by_name
        device = await info(device_name)
        await pulse.mute(device, state)

    return 0


async def set_primary(device_type: str, device_name: str, pulse=None):
    '''
    Change mute state of a device
        "device_type" is the enum DeviceType
        "device_name" is the device name
    '''

    async with pulsectl_asyncio.PulseAsync() as pulse:
        info = pulse.get_sink_by_name if device_type == 'sink' else pulse.get_source_by_name
        device = await info(device_name)
        await pulse.default_set(device)

    return 0


async def set_volume(device_type: str, device_name: str, volume: list):
    '''
    Change device volume
        "device_type" either sink or source
        "device_name" device name
        "val" new volume level
        "selected_channels" the channels that will have the volume changed
    '''

    # limit volume from 0 to 153
    # val = min(max(0, val), 153)

    # get device info from pulsectl
    async with pulsectl_asyncio.PulseAsync() as pulse:

        # get device info from pulsectl
        info = pulse.get_sink_by_name if device_type == 'sink' else pulse.get_source_by_name
        device = await info(device_name)
        volume = pulsectl.PulseVolumeInfo([x / 100 for x in volume])
        await pulse.volume_set(device, volume)

    return 0


'''
        # set the volume
        volume_value = device.volume
        if selected_channels is None:
            volume_value.value_flat = val / 100

        # set by channel
        else:
            channels = len(device.volume.values)
            volume_list = device.volume.values.copy()
            # change specific channels
            for channel in range(channels):

                # change volume for selected channel
                if selected_channels[channel] is True:
                    volume_list[channel] = val / 100

            volume_value = pulsectl.PulseVolumeInfo(volume_list)
'''


async def app_mute(app_type: str, index: int, state: bool):
    '''
    Mute an app by their type and index
        "app_type" is either sink_input or source_output
        "index" is the index of the app in pulse
        "state" True is mute and False is unmute
    '''

    async with pulsectl_asyncio.PulseAsync() as pulse:
        if app_type == 'sink_input':
            app = await pulse.sink_input_info(index)
        else:
            app = await pulse.source_output_info(index)

        await pulse.mute(app, state)

    return 0


async def app_volume(app_type: str, index: int, val: int):
    '''
    Set an app volume by their type and index
        "app_type" is either sink_input or source_output
        "index" is the index of the app in pulse
        "val" is an int from 0 to 153
    '''

    # limit volume from 0 to 153
    val = min(max(0, val), 153)

    # get device info from pulsectl
    async with pulsectl_asyncio.PulseAsync() as pulse:

        # set volume object
        try:
            if app_type == 'sink_input':
                device = await pulse.sink_input_info(index)
                chann = len(device.volume.values)
                volume = pulsectl.PulseVolumeInfo(val / 100, chann)
                await pulse.sink_input_volume_set(index, volume)
            else:
                device = await pulse.source_output_info(index)
                chann = len(device.volume.values)
                volume = pulsectl.PulseVolumeInfo(val / 100, chann)
                await pulse.source_output_volume_set(index, volume)

        # trying to change volume of a device that just desapears
        # better to just ignore it, nothing bad comes from doing so
        except pulsectl.PulseIndexError:
            LOG.debug('App #%d already removed', index)

    return 0


async def move_app_device(app_type: str, index: int, device_name: str):
    '''
    Set an app output by their type and index
        "app_type" is either sink_input or source_output
        "index" is the index of the app in pulse
        "device_name" is is the name of the new master device
    '''

    async with pulsectl_asyncio.PulseAsync() as pulse:
        try:
            if app_type == 'sink_input':
                sink = await pulse.get_sink_by_name(device_name)
                await pulse.sink_input_move(index, sink.index)
            else:
                source = await pulse.get_source_by_name(device_name)
                await pulse.source_output_move(index, source.index)

        # some apps have DONT MOVE flag, the app will crash
        except pulsectl.PulseOperationFailed:
            LOG.debug('App #%d device cant be moved', index)

    return 0


async def list_devices(device_type):
    '''
    List devices by their type
        "device_type" is either sink or source
    '''
    async with pulsectl_asyncio.PulseAsync() as pulse:
        list_pa_devices = pulse.sink_list if device_type == 'sink' else pulse.source_list
        device_list: list = []
        # pa_sink_hardware: hex = 0x0004
        for device in await list_pa_devices():

            if (device.proplist['factory.name'] != 'support.null-audio-sink' and
                    device.proplist['device.class'] != "monitor"):
                device_list.append(device)

    return device_list


async def get_device(device_type: str, device_name: str):
    '''
    Get a specific device by their name
        "device_type" is either sink or source
        "device_name" is the name of the device
    '''
    async with pulsectl_asyncio.PulseAsync() as pulse:
        device = None
        if device_type == 'sink':
            device = pulse.get_sink_by_name(device_name)
        elif device_type == 'source':
            device = pulse.get_source_by_name(device_name)

        return device


async def get_device_by_id(device_type: str, device_id: int):
    async with pulsectl_asyncio.PulseAsync() as pulse:
        info = pulse.sink_info if device_type == 'sink' else pulse.source_info
        device = await info(int(device_id))
        return device


async def filter_results(app):
    '''
    Filter pavu and pm peak sinks
    '''
    assert 'application.name' in app.proplist
    assert '_peak' not in app.proplist['application.name']
    assert app.proplist.get('application.id') != 'org.PulseAudio.pavucontrol'

    # if ('application.name' not in app.proplist
    #         or '_peak' in app.proplist['application.name']
    #         or app.proplist.get('application.id') == 'org.PulseAudio.pavucontrol'):
    #     return False
    #
    # return True

async def app_by_id(index: int, app_type: str):
    '''
    Return a specific app
        "index" is the index of the desidered app
        "app_type" is sink_input or source_output
    '''
    async with pulsectl_asyncio.PulseAsync() as pulse:
        if app_type == 'sink_input':
            app = await pulse.sink_input_info(index)
            app.device_name = (await pulse.sink_info(app.sink)).name
        else:
            app = await pulse.source_output_info(index)
            app.device_name = (await pulse.source_info(app.sink)).name

    return app


async def list_apps(app_type: str):
    app_list = []

    async with pulsectl_asyncio.PulseAsync() as pulse:
        if app_type == 'sink_input':
            full_app_list = await pulse.sink_input_list()

        elif app_type == 'source_output':
            full_app_list = await pulse.source_output_list()

        else:
            return app_list

        for app in full_app_list:

            # filter pavu and pm peak sinks
            try:
                await filter_results(app)
            except AssertionError:
                continue

            if app_type == 'sink_input':
                app.device_name = (await pulse.sink_info(app.sink)).name
            else:
                app.device_name = (await pulse.source_info(app.sink)).name

            app_list.append(app)
    return app_list


async def get_app_device_name(app_type: str, device_index: int):
    async with pulsectl_asyncio.PulseAsync() as pulse:
        if app_type == 'sink_input':
            return (await pulse.sink_info(device_index)).name

        return (await pulse.source_info(device_index)).name


async def get_app_by_id(app_type, app_index: int):
    async with pulsectl_asyncio.PulseAsync() as pulse:

        try:
            if app_type == 'sink_input':
                app = await pulse.sink_input_info(int(app_index))
                device = await pulse.sink_info(int(app.sink))
            else:
                app = await pulse.source_output_info(int(app_index))
                device = await pulse.source_info(int(app.source))
        except pulsectl.PulseIndexError:
            return None

        app.device_name = device.name

        if ('application.name' not in app.proplist or
                '_peak' in app.proplist['application.name'] or
                app.name == 'audio-volume-change' or
                app.proplist.get('application.id') == 'org.PulseAudio.pavucontrol'):
            return None

        # try:
        #     await filter_results(app)
        # except AssertionError:
        #     return None

        return app


async def get_primary(device_type: str):
    async with pulsectl_asyncio.PulseAsync() as pulse:
        if device_type == 'sink':
            return await pulse.sink_default_get()
        return await pulse.source_default_get()


def decode_event(event: pulsectl.PulseEventInfo) -> tuple[str, str, int]:
    '''
    Receives a PulseEventInfo and returns the str version of .t and .facility
    Returns:
        tuple[str, str, int]: facility, event type and object index respectively
    '''
    facility = getattr(event.facility, '_value', None)
    event_type = getattr(event.t, '_value', None)
    device_index = event.index

    return facility, event_type, device_index


async def subscribe_peak(name, device_type, callback, stream_index=None, rate=30):
    if device_type == 'sink':
        name += '.monitor'
    else:
        stream_index = None

    async with pulsectl_asyncio.PulseAsync(f'{name}_{device_type}_peak') as pulse:
        async for peak in pulse.subscribe_peak_sample(name, rate, stream_idx=stream_index):
            await callback(peak)


async def pulse_listener():
    async with pulsectl_asyncio.PulseAsync('pulsemeeter-listener') as pulse:
        async for event in pulse.subscribe_events('sink', 'source', 'sink_input', 'source_output', 'server'):
            pm_event = PulseEvent(type=event.t._value, facility=event.facility._value, index=event.index)
            yield pm_event


async def runcmd(command: str, split_size: int = -1) -> int:
    LOG.debug(command)
    command = command.split(' ', split_size)
    process = await asyncio.create_subprocess_exec(*command)
    return_code = await process.wait()
    return return_code
