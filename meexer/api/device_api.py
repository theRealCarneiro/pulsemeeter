from meexer.ipc.server import Server as ipc
from meexer.schemas import ipc_schema, requests_schema as requests
from meexer.schemas.ipc_schema import SubscriptionFlags as sflags
from meexer.model.device_model import DeviceModel
from meexer.model.config_model import ConfigModel
from pydantic.error_wrappers import ValidationError

CONFIG = ConfigModel()


@ipc.command('create_device', sflags.DEVICE_NEW | sflags.DEVICE)
def create_device(req: requests.CreateDevice) -> DeviceModel:
    '''
    Recives a devices index and a device
    '''

    # validate request
    try:
        create_device_req = requests.CreateDevice(**req)
    except ValidationError:
        return ipc_schema.StatusCode.INVALID, None

    device = DeviceModel.construct(create_device_req.device)
    CONFIG.insert_device(device)

    return ipc_schema.StatusCode.OK, None


@ipc.command('update_device', sflags.DEVICE_CHANGED | sflags.DEVICE)
def update_device(req: requests.UpdateDevice):
    '''
    Recives a device index and a device
    '''

    try:
        update_device_req = requests.UpdateDevice(**req)
    except ValidationError:
        return ipc_schema.StatusCode.INVALID, None

    device_type = update_device_req.index.device_type
    device_id = update_device_req.index.device_id
    new_device = update_device_req.device

    device = CONFIG.get_device(device_type, device_id)
    device.update_device_settings(new_device)

    return ipc_schema.StatusCode.OK, None


@ipc.command('remove_device', sflags.DEVICE_REMOVE | sflags.DEVICE)
def remove_device(req: requests.RemoveDevice):
    '''
    Recives a device index
    '''

    config = CONFIG.__dict__

    # request validation
    try:
        remove_device_req = requests.RemoveDevice(**req)
    except ValidationError:
        return ipc_schema.StatusCode.INVALID, None, None

    device_type = remove_device_req.index.device_index.device_type
    device_id = remove_device_req.index.device_index.device_id
    device = config.remove_device(device_type, device_id)
    device.destroy()

    return ipc_schema.StatusCode.OK, None


@ipc.command('reconnect', sflags.CONNECTION | sflags.DEVICE, False, False)
def reconnect() -> int:
    pass


@ipc.command('connect', sflags.CONNECTION | sflags.DEVICE)
def connect(req: requests.Connect) -> int:
    '''
    Recives a connection, and connects devices
    '''

    try:
        connection_req = requests.Connect(**req)
    except ValidationError:
        return ipc_schema.StatusCode.INVALID, None, None

    state = connection_req.state
    source_index = connection_req.source
    output_index = connection_req.output

    source = CONFIG.get_device(source_index.device_type, source_index.device_id)
    output = CONFIG.get_device(output_index.device_type, output_index.device_id)

    source.connect(output_index.output_type, output_index.output_id,
                   output.get_correct_name(), state)

    return ipc_schema.StatusCode.OK, None


@ipc.command('mute', sflags.DEVICE, save_config=False)
def mute(req: requests.Mute):
    '''
    Recives a connection, and connects devices
    '''
    try:
        mute_req = requests.Mute(**req)
    except ValidationError:
        return ipc_schema.StatusCode.INVALID, None, None

    device = CONFIG.get_device(mute_req.index.device_type, mute_req.index.device_id)
    device.set_mute(mute_req.state)
    return ipc_schema.StatusCode.OK, None


@ipc.command('default', sflags.DEVICE, save_config=False)
def default(req: requests.Default):
    '''
    Recives an index, sets device as default, only works for virtual devices
    '''
    try:
        default_req = requests.Default(**req)
    except ValidationError:
        return ipc_schema.StatusCode.INVALID, None, None

    device = CONFIG.get_device(default_req.index.device_type, default_req.index.device_id)
    device.set_default()
    return ipc_schema.StatusCode.OK, None


@ipc.command('volume', sflags.VOLUME | sflags.DEVICE, save_config=False)
def volume(req: requests.Volume):
    '''
    Recives a volume request
    '''
    try:
        volume_req = requests.volume(**req)
    except ValidationError:
        return ipc_schema.StatusCode.INVALID, None, None

    device = CONFIG.get_device(volume_req.index.device_type, volume_req.index.device_type)
    device.set_volume(volume_req.volume)
    return ipc_schema.StatusCode.OK, None


@ipc.command('list_devices', flags=0, notify=False, save_config=False)
def list_devices(req: requests.DeviceList):

    try:
        device_list_req = requests.DeviceList(**req)
    except ValidationError:
        return ipc_schema.StatusCode.INVALID, None, None

    device_list = DeviceModel.list_devices(device_list_req.device_type)

    return ipc_schema.StatusCode.OK, device_list
