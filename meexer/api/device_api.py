from meexer.ipc.server import Server as ipc
from meexer.schemas import ipc_schema
from meexer.schemas.ipc_schema import SubscriptionFlags as sflags
from meexer.schemas import requests_schema as requests
from meexer.model.device_model import DeviceModel
from meexer.model.config_model import ConfigModel
from pydantic.error_wrappers import ValidationError

CONFIG = ConfigModel()


@ipc.command('create_device', sflags.DEVICE_NEW | sflags.DEVICE)
def create_device(req: requests.CreateDevice) -> DeviceModel:
    '''
    Recives a devices index and a device
    '''

    config = CONFIG.__dict__

    # request validation
    try:
        create_device_req = requests.CreateDevice(**req)
    except ValidationError:
        return ipc_schema.StatusCode.INVALID

    # create device model without running validation, since it
    # was already validated by the CreateDevice schema
    device = DeviceModel.construct(create_device_req.device)

    # get device new index and store device in config
    device_type = device.get_type()
    device_id = max(config[device_type], key=int, default='0')
    config[device_type][device_id] = device

    return ipc_schema.StatusCode.OK


# @ipc.command('edit_device', sflags.DEVICE_CHANGED | sflags.DEVICE)
# def edit_device(device: requests.RemoveEdit):
    # '''
    # Recives a device index
    # '''
    # pass


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
        return ipc_schema.StatusCode.INVALID


    CONFIG.remove_device(req.index.device_index, req.index.device_index)


@ipc.command('connect', sflags.CONNECTION | sflags.DEVICE)
def connect(connection: requests.Connect) -> int:
    '''
    Recives a connection, and connects devices
    '''
    state = connection.state
    source_index = connection.source
    output_index = connection.output
    source = CONFIG.get_device(source_index.device_type, source_index.device_id)
    output = CONFIG.get_device(output_index.device_type, output_index.device_id)
    source.connect(output_index.output_type, output_index.output_id, output.name, state)


@ipc.command('mute', sflags.DEVICE, save_config=False)
def mute(mute: requests.Mute):
    '''
    Recives a connection, and connects devices
    '''
    mute = requests.Mute(**mute)
    device = CONFIG.get_device(mute.index.device_type, mute.index.device_id)
    device.set_mute(mute.state)


@ipc.command('default', sflags.DEVICE, save_config=False)
def default(default: requests.Default):
    '''
    Recives an index, sets device as default, only works for virtual devices
    '''
    default = requests.Default(**default)
    device = CONFIG.get_device(default.index.device_type, default.index.device_id)
    device.set_default()


@ipc.command('volume', sflags.VOLUME | sflags.DEVICE, save_config=False)
def volume(volume: requests.Volume):
    '''
    Recives a volume request
    '''
    volume = requests.volume(**volume)
    device = CONFIG.get_device(volume.index.device_type, volume.index.device_type)
    device.set_volume(volume.volume)
