import asyncio
import threading
import traceback
import logging

import pulsectl
import pulsectl_asyncio

LOG = logging.getLogger("generic")

class PulseSocket():
    '''
    Connects to Pulseaudio/Pipewire using pulsectl and handles every connection of them to Pulsemeeter
    '''
    def __init__(self, command_queue, config):
        self.pulsectl_asyncio = pulsectl_asyncio.PulseAsync('pulsemeeter-listener')
        self.pulsectl = pulsectl.Pulse('pulsemeeter')

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
                pulsem_device = self.config_device_from_name(device.name)
                if pulsem_device is not None:
                    device_config = self.config[pulsem_device["device_type"]][pulsem_device["device_id"]]
                    # read the volume data from config and from pulseaudio
                    config_volume = device_config["vol"]
                    device_volume = int(round(device.volume.value_flat * 100))

                    # compare config value with pulseaudio value
                    if config_volume != device_volume:
                        command = f'volume {pulsem_device["device_type"]} {pulsem_device["device_id"]} {device_volume}'
                        self.command_queue.put(('audio_server', None, command))
                        device_config["vol"] = device_volume
                        return

                    config_mute = device_config["mute"]
                    device_mute = bool(device.mute)

                    if config_mute != device_mute:
                        command = f'mute {pulsem_device["device_type"]} {pulsem_device["device_id"]} {device_mute}'
                        self.command_queue.put(('audio_server', None, command))
                        device_config["mute"] = device_mute
                        return
                    #TODO: Maybe add detection for connection changes

        elif event.t in ['new', 'remove']:
            index = event.index
            facility = self._fa_enum_to_string(event.facility)
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

        # searches for device with name(pulseaudio device) and returns tuple:
    # - device_type
    # - device_id
    def config_device_from_name(self, name):
        for device_type in ['a', 'b', 'hi', 'vi']:
            # iterate through all devices (can scale with device count)
            device_id_range = range(1, len(self.config[device_type])+1)
            for device_id in device_id_range:
                device_id = str(device_id)
                device_config = self.config[device_type][device_id]
                if device_config["name"] == name:
                    return {
                            "device_type": device_type,
                            "device_id": device_id
                            }
        return


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
        for case in case:
            if argument == case: return case

    # It searches in the facility for the specific device with the index and returns this device.
    # (used for listener)
    async def device_from_event(self, event):
        if event.facility == 'sink':
            dev_list = await self.pulsectl_asyncio.sink_list()
        elif event.facility == 'source':
            dev_list = await self.pulsectl_asyncio.source_list()
        else:
            return

        for device in dev_list:
            if device.index == event.index:
                return device
