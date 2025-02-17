# import asyncio
# import threading
import logging

# import pulsectl_asyncio
from meexer.ipc.router import Blueprint
from meexer.model.config_model import ConfigModel
from meexer.model.device_model import DeviceModel
from meexer.scripts import pmctl_async as pmctl
from meexer.ipc.client_async import Client
from meexer.schemas import ipc_schema, requests_schema

# CONFIG = ConfigModel()
task = Blueprint('Pulse Events')


@task.create_task('event_listen')
async def event_listen(callback_function):
    client = Client()
    async for event in pmctl.pulse_listener():

        if event.facility in ('sink', 'source'):
            if event.t == 'change':
                pulsectl_device = await pmctl.get_device_by_id(event.facility, event.index)
                device_type, device_id, pm_device = CONFIG.find_device(event.facility, pulsectl_device.name)
                if pm_device is None:
                    continue

                pa_to_pm_device = DeviceModel.pa_to_device_model(pulsectl_device, event.facility)

                # if volume changed
                if pm_device is None or not pm_device.check_volume_changes(pa_to_pm_device.volume):
                    continue

                data = {'index': {'device_type': device_type, 'device_id': device_id}, 'volume': pm_device.get_volume()}

                req = ipc_schema.Request(command='volume', sender_id=0, data=data, run=False)
                print(req)
                await callback_function(req)

                # print(pa_to_pm_device.volume)
                # pm_device.check_mute_changes(pulsectl_device.mute)
