import asyncio
import threading
import logging

import pulsectl
import pulsectl_asyncio

# from meexer.scripts import pmctl

LOG = logging.getLogger("generic")


class PulseSocket():
    '''
    Connects to Pulseaudio/Pipewire using pulsectl and handles every connection of them to Pulsemeeter
    '''

    def __init__(self, command_queue, config):
        self.pulsectl_asyncio = pulsectl_asyncio.PulseAsync('pulsemeeter-listener')
        self.pulsectl = pulsectl.Pulse('pulse-socket')

        self.command_queue = command_queue
        self.config = config
        self.async_loop = asyncio.get_event_loop()
        self.pulse_listener_thread = threading.Thread(target=self.async_loop.run_forever, daemon=True)

    def start_listener(self):
        '''
        starts the listener for Pulseaudio/Pipewire changes (restarts if ran again)
        '''
        if self.pulse_listener_thread.is_alive():
            LOG.info("restarting listener")
            self.pulse_listener_thread.join()

        self.pulse_listener_task = asyncio.run_coroutine_threadsafe(self._pulse_listener(), self.async_loop)
        # run the async code in thread
        self.pulse_listener_thread.start()

    def stop_listener(self):
        self.pulse_listener_task.cancel()
        self.async_loop.stop()
        self.pulse_listener_thread.join()

    # handles incoming events from the pulseaudio listener
    # (updates config if needed and alerts clients)
    async def _pulse_listener_handler(self, event):
        if event.t == 'change':
            device = await self.device_from_event(event)
            if device is not None:
                pmdevs = self.config_device_from_name(device.name)

                for device_type, device_id in pmdevs:
                    device_config = self.config[device_type][device_id]

                    # read the volume data from config and from pulseaudio
                    config_volume = device_config["vol"]
                    device_volume = int(round(device.volume.value_flat * 100))

                    # compare config value with pulseaudio value
                    # selected channels
                    if 'selected_channels' in device_config:
                        device_volume = config_volume
                        dv = device.volume.values
                        for i in range(len(device_config['selected_channels'])):

                            # check if selected port has updated it's volume
                            if device_config['selected_channels'][i] is True:
                                channel_vol = int(dv[i] * 100)
                                if config_volume != channel_vol:
                                    device_volume = channel_vol

                    if config_volume != device_volume:
                        command = f'volume {device_type} {device_id} {device_volume}'
                        self.command_queue.put(('audio_server', None, command))
                        device_config["vol"] = device_volume
                        return

                    config_mute = device_config["mute"]
                    device_mute = bool(device.mute)

                    if config_mute != device_mute:
                        command = f'mute {device_type} {device_id} {device_mute}'
                        self.command_queue.put(('audio_server', None, command))
                        device_config["mute"] = device_mute
                        return

        elif event.t in ['new', 'remove']:
            index = event.index
            facility = self._fa_enum_to_string(event.facility)
            if facility in ['sink_input', 'source_output']:
                if event.t == 'new':
                    command = f'device-plugged-in {index} {facility}'
                elif event.t == 'remove':
                    command = f'device-unplugged {index} {facility}'

                self.command_queue.put(('audio_server', None, command))

    # listener for pulseaudio events
    async def _pulse_listener(self):
        async with self.pulsectl_asyncio as pulse:
            async for event in pulse.subscribe_events('all'):
                await self._pulse_listener_handler(event)

    def config_device_from_name(self, name):
        """
        searches for device with name(pulseaudio device) and returns tuple:
        - device_type
        - device_id
        """
        devices = []
        for device_type in ['a', 'b', 'hi', 'vi']:
            for device_id, device_config in self.config[device_type].items():
                if device_config["name"] == name:
                    devices.append((device_type, device_id))
        return devices

    # thanks EnumValue
    # facility EnumValue to native string
    def _fa_enum_to_string(self, argument):
        case = {
            'client',
            'sink_input',
            'source_output',
            'module',
            'sink',
            'source'
        }
        for c in case:
            if argument == c: return c

    # It searches in the facility for the specific device with the index and returns this device.
    # (used for listener)
    async def device_from_event(self, event):
        if event.facility == 'sink':
            dev_list = await self.pulsectl_asyncio.sink_list()
        elif event.facility == 'source':
            dev_list = await self.pulsectl_asyncio.source_list()
        else:
            return None

        for device in dev_list:
            if device.index == event.index:
                return device
