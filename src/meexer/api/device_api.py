from meexer.ipc.router import Blueprint
from meexer.schemas import device_schema, requests_schema as requests
from meexer.schemas.ipc_schema import SubscriptionFlags as sflags
from meexer.schemas import ipc_schema
from meexer.model.device_model import DeviceModel
from meexer.model.config_model import ConfigModel
from meexer.scripts import pmctl_async as pmctl

CONFIG = ConfigModel()

ipc = Blueprint('device')


@ipc.command('create_device', sflags.DEVICE_NEW | sflags.DEVICE)
async def create_device(create_device_req: requests.CreateDevice) -> None:
    '''
    Recives a devices index and a device
    '''

    device = DeviceModel(**create_device_req.device.dict())
    CONFIG.insert_device(device)

    if (device.device_class == 'virtual' and not
            device.flags & device_schema.DeviceFlags.EXTERNAL):
        await pmctl.init(device.device_type, device.name)
    return ipc_schema.StatusCode.OK, None


@ipc.command('update_device', sflags.DEVICE_CHANGED | sflags.DEVICE)
async def update_device(update_device_req: requests.UpdateDevice) -> None:
    '''
    Recives a device index and a device
    '''

    device_type = update_device_req.index.device_type
    device_id = update_device_req.index.device_id
    new_device = update_device_req.device

    device: DeviceModel = CONFIG.get_device(device_type, device_id)
    device.update_device_settings(new_device)


@ipc.command('remove_device', sflags.DEVICE_REMOVE | sflags.DEVICE)
async def remove_device(remove_device_req: requests.RemoveDevice) -> None:
    '''
    Recives a device index
    '''

    # request validation
    device_type = remove_device_req.index.device_index.device_type
    device_id = remove_device_req.index.device_index.device_id
    device: DeviceModel = CONFIG.remove_device(device_type, device_id)
    # device.destroy()

    # TODO: remove connections
    # TODO: remove plugins
    if (device.device_class == 'virtual' and not
            device.flags & device_schema.DeviceFlags.EXTERNAL):
        await pmctl.remove(device.name)


# @ipc.command('reconnect', sflags.CONNECTION | sflags.DEVICE, False, False)
# def reconnect() -> int:
    # pass


@ipc.command('connect', sflags.CONNECTION | sflags.DEVICE)
async def connect(connection_req: requests.Connect) -> int:
    '''
    Recives a connection, and connects devices
    '''

    state = connection_req.state
    source_index = connection_req.source
    output_index = connection_req.output

    source = CONFIG.get_device(source_index.device_type, source_index.device_id)
    output = CONFIG.get_device(output_index.device_type, output_index.device_id)

    source.connect(output_index.device_type, output_index.device_id,
                   state, output.nick)

    str_port_map = source.str_port_map(output_index.device_type, output_index.device_id, output)

    await pmctl.connect(source.get_correct_name(), output.get_correct_name(),
                        state, port_map=str_port_map)


@ipc.command('mute', sflags.DEVICE, save_config=False)
async def mute(mute_req: requests.Mute) -> None:
    '''
    Recives a connection, and connects devices
    '''
    device = CONFIG.get_device(mute_req.index.device_type, mute_req.index.device_id)
    device.set_mute(mute_req.state)
    await pmctl.mute(device.device_type, device.name, mute_req.state)


@ipc.command('default', sflags.DEVICE, save_config=False)
async def default(default_req: requests.Default) -> None:
    '''
    Recives an index, sets device as default, only works for virtual devices
    '''
    device = CONFIG.get_device(default_req.index.device_type, default_req.index.device_id)

    if device.device_class == 'virtual':
        device.set_default()
        await pmctl.set_primary(device.device_type, device.name)


@ipc.command('volume', sflags.VOLUME | sflags.DEVICE, save_config=False)
async def volume(volume_req: requests.Volume) -> None:
    '''
    Recives a volume request
    '''
    device = CONFIG.get_device(volume_req.index.device_type, volume_req.index.device_id)
    device.set_volume(volume_req.volume)
    await pmctl.set_volume(device.device_type, device.name, device.volume)


@ipc.command('list_devices', flags=0, notify=False, save_config=False)
async def list_devices(device_list_req: requests.DeviceList) -> list:
    '''
    Returns a list of device schemas
    '''

    pa_device_list = await pmctl.list_devices(device_list_req.device_type)
    device_list = DeviceModel.list_devices(pa_device_list, device_list_req.device_type)

    return device_list
