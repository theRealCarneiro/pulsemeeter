import logging
import pulsectl
import pulsectl_asyncio

from pulsemeeter.model.types import PulseEvent

LOG = logging.getLogger('generic')


async def get_device_by_id(device_type: str, device_id: int):
    async with pulsectl_asyncio.PulseAsync() as pulse:
        info = pulse.sink_info if device_type == 'sink' else pulse.source_info
        device = await info(int(device_id))
        return device


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
                app.proplist.get('application.id') == 'org.PulseAudio.pavucontrol' or
                'pm_route_' in app.proplist.get('node.name', '')):
            return None

        return app


async def get_primary(device_type: str):
    async with pulsectl_asyncio.PulseAsync() as pulse:
        if device_type == 'sink':
            return await pulse.sink_default_get()
        return await pulse.source_default_get()


async def subscribe_peak(name, device_type, callback, stream_index=None, rate=30):
    is_device_meter = stream_index is None
    if device_type == 'sink':
        name += '.monitor'
    else:
        stream_index = None

    async with pulsectl_asyncio.PulseAsync(f'{name}_{device_type}_peak') as pulse:
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
    async with pulsectl_asyncio.PulseAsync('pulsemeeter-listener') as pulse:
        async for event in pulse.subscribe_events('sink', 'source', 'sink_input', 'source_output', 'server'):
            pm_event = PulseEvent(type=event.t._value, facility=event.facility._value, index=event.index)
            yield pm_event
