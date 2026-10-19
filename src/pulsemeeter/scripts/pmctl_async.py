import logging
from contextlib import asynccontextmanager

import pulsectl
import pulsectl_asyncio

from pulsemeeter.model.types import PulseEvent

LOG = logging.getLogger('generic')


@asynccontextmanager
async def pulse_connection(client_name=None):
    '''
    Drop-in for `async with PulseAsync()` that also closes the connection if
    connect() is interrupted. PulseAsync.__aenter__ raising (e.g. the task is
    cancelled mid-handshake) skips __aexit__, leaving the client connected to
    the pulse server forever.
    '''
    pulse = pulsectl_asyncio.PulseAsync(client_name)
    try:
        await pulse.connect()
        yield pulse
    finally:
        pulse.close()


async def get_device_by_id(device_type: str, device_id: int):
    async with pulse_connection() as pulse:
        info = pulse.sink_info if device_type == 'sink' else pulse.source_info
        device = await info(int(device_id))
        return device


async def get_app_by_id(app_type, app_index: int):
    async with pulse_connection() as pulse:

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
                app.proplist.get('application.id') == 'org.PulseAudio.pavucontrol' or
                'pm_route_' in app.proplist.get('node.name', '')):
            return None

        return app


async def get_primary(device_type: str):
    async with pulse_connection() as pulse:
        try:
            if device_type == 'sink':
                return await pulse.sink_default_get()
            return await pulse.source_default_get()
        except pulsectl.PulseIndexError:
            LOG.debug('No resolvable default %s', device_type)
            return None


async def subscribe_peak(name, device_type, callback, stream_index=None, rate=30):
    '''
    Feed peaks of a device, or of one playback stream (by index) on a sink, to `callback`.
    '''
    is_device_meter = stream_index is None
    if device_type == 'sink':
        name += '.monitor'

    async with pulse_connection(f'{name}_{device_type}_peak') as pulse:
        if is_device_meter:
            try:
                await pulse.get_source_by_name(name)
            except pulsectl.PulseError:
                LOG.debug('Peak source %s not present, idling vumeter', name)
                await callback(0.0)
                return

        async for peak in pulse.subscribe_peak_sample(name, rate, stream_idx=stream_index):
            await callback(peak)


async def pulse_listener():
    async with pulse_connection('pulsemeeter-listener') as pulse:
        async for event in pulse.subscribe_events('sink', 'source', 'sink_input', 'source_output', 'server'):
            pm_event = PulseEvent(type=event.t._value, facility=event.facility._value, index=event.index)
            yield pm_event
