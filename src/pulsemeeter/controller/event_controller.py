import time
import asyncio
import logging
import pulsectl
import threading
import traceback
import concurrent
from pydantic import PrivateAttr

from pulsemeeter.scripts import pmctl_async
from pulsemeeter.model.signal_model import SignalModel
from pulsemeeter.repository.device_repository import DeviceRepository
from pulsemeeter.model.app_model import AppModel

LOG = logging.getLogger("generic")


class EventController(SignalModel):
    '''
    EventController listens for PulseAudio/pmctl events and emits signals for application/UI components.

    Signals:
        pa_app_new(app_type: str, app_index: int, app_model: AppModel):
            Emitted when a new application stream is detected.
        pa_app_remove(app_type: str, app_index: int):
            Emitted when an application stream is removed.
        pa_app_change(app_type: str, app_index: int, app_model: AppModel):
            Emitted when an application stream changes.
        pa_device_change(device_type: str, device_id: str, device_model: DeviceModel):
            Emitted when a device changes.
        pa_primary_change(device_type: str, device_id: str | None):
            Emitted when the primary device changes.

    Attributes:
        device_repository (DeviceRepository): The repository managing device data.
    '''
    device_repository: DeviceRepository

    _facility_map: dict[str, str] = {
        'sink': 'device',
        'source': 'device',
        'sink_input': 'app',
        'source_output': 'app',
        'server': 'server',
    }

    _async_loop: asyncio.AbstractEventLoop
    _thread: threading.Thread

    def __init__(self, device_repository):
        super().__init__()
        self.device_repository = device_repository
        self._async_loop = asyncio.new_event_loop()
        self._thread = threading.Thread(target=self._async_loop.run_forever, daemon=True)
        self._thread.start()

    def _handle_listen_error(self, fut):
        try:
            fut.result(timeout=1)

        except asyncio.CancelledError:
            LOG.debug("Listen task canceled")

        except concurrent.futures._base.CancelledError:
            LOG.debug("Listen task canceled")

        except Exception as e:
            tb_str = ''.join(traceback.format_exception(type(e), e, e.__traceback__))
            LOG.error("Listen task error: \n %s", tb_str)

    def start_listen(self):

        future = asyncio.run_coroutine_threadsafe(
            self.event_listen(),
            self._async_loop
        )

        future.add_done_callback(self._handle_listen_error)
        self.listen_task = future
        return future

    def stop_listen(self):
        """Stop the listen task from a different thread"""
        self.listen_task.cancel()
        time.sleep(0.001)

    async def event_listen(self):
        '''
        Listen for and handle events from pmctl_async.pulse_listener().
        '''

        _pa_event_map = {
            ('app', 'new'): self._handle_app_new_event,
            ('app', 'remove'): self._handle_app_remove_event,
            ('app', 'change'): self._handle_app_change_event,
            ('server', 'change'): self._handle_server_change_event,
            ('device', 'change'): self._handle_device_change_event,
        }

        # async for event in pmctl_async.pulse_listener():
        async for event in pmctl_async.pulse_listener():
            pm_facility = self._facility_map.get(event.facility)
            handler = _pa_event_map.get((pm_facility, event.type))
            if handler:
                await handler(event)

    async def _handle_app_new_event(self, event: pulsectl.PulseEventInfo):
        '''
        Handle a new application event.
        Args:
            event: The event object.
            app_type (str): Application type.
        '''
        app_type = event.facility
        app_index = event.index
        app = await pmctl_async.get_app_by_id(app_type, app_index)

        if app is None:
            return

        app_model = AppModel.pa_to_app_model(app, app_type)
        self.emit('pa_app_new', app_type, event.index, app_model)

    async def _handle_app_remove_event(self, event):
        '''
        Handle an application removal event.
        Args:
            event: The event object.
            app_type (str): Application type.
        '''
        app_type = event.facility
        app_index = event.index
        self.emit('pa_app_remove', app_type, app_index)

    async def _handle_app_change_event(self, event):
        '''
        Handle an application change event.
        Args:
            event: The event object.
            app_type (str): Application type.
        '''
        app_type = event.facility
        app_index = event.index
        app = await pmctl_async.get_app_by_id(app_type, app_index)
        if app is None:
            return

        app_model = AppModel.pa_to_app_model(app, app_type)
        self.emit('pa_app_change', app_type, app_index, app_model)

    async def _handle_device_change_event(self, event):
        '''
        Handle a device change event.
        Args:
            event: The event object.
        '''
        pa_device = await pmctl_async.get_device_by_id(event.facility, event.index)
        pm_device_types = ('hi', 'b') if event.facility == 'source' else ('vi', 'a')
        device_search = self.device_repository.find_device_by_key
        search_res = device_search('name', pa_device.name, pm_device_types)

        for device_type, device_id, device_model in search_res:
            if not device_model or not device_model.update_from_pa(pa_device):
                continue

            self.emit('pa_device_change', device_type, device_id, device_model)

    async def _handle_server_change_event(self, _):
        '''
        Handle a server change event.
        Args:
            event: The event object.
        '''
        for pa_device_type in ('sink', 'source'):
            pm_device_type = 'vi' if pa_device_type == 'sink' else 'b'
            primary = await pmctl_async.get_primary(pa_device_type)
            pm_primary_list = self.device_repository.get_primary_device(pm_device_type)

            if pm_primary_list:
                _, _, pm_primary = pm_primary_list[0]

                # if nothing changed just ignore it
                if pm_primary.name == primary.name:
                    continue

                pm_primary.set_primary(False, emit=False)

            search_list = self.device_repository.find_device_by_key('name', primary.name, [pm_device_type])

            # if the primary is not a pm device, emit None
            if not search_list:
                self.emit('pa_primary_change', pm_device_type, None)
                continue

            # if its a pm device, set model as primary
            device_type, device_id, device = search_list[0]
            device.set_primary(True, emit=False)
            self.emit('pa_primary_change', device_type, device_id)
