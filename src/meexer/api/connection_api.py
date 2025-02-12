from pydantic import ValidationError
from meexer.ipc.router import Blueprint
from meexer.schemas import device_schema, ipc_schema, requests_schema as requests
from meexer.schemas.ipc_schema import SubscriptionFlags as sflags
# from meexer.model.device_model import DeviceModel
from meexer.model.config_model import ConfigModel
# from meexer.scripts import pmctl_async as pmctl

CONFIG = ConfigModel()

ipc = Blueprint('connection')


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

    source.connect(output_index.device_type, output_index.device_id,
                   output, state)

    return ipc_schema.StatusCode.OK, None


# @ipc.command('reconnect', sflags.CONNECTION | sflags.DEVICE, False, False)
# def reconnect() -> int:
    # pass
