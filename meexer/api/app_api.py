from pydantic.error_wrappers import ValidationError

from meexer.schemas import requests_schema as requests
from meexer.schemas import ipc_schema
from meexer.schemas.ipc_schema import SubscriptionFlags as sflags
from meexer.ipc.router import Router as ipc
from meexer.model.app_model import AppModel


@ipc.command('app_move', sflags.APP, save_config=False)
def app_move(req: requests.AppMove):
    '''
    Recives an AppMove request, changes the device an app is bound into
    '''

    try:
        app_move_req = requests.AppMove(**req)
    except ValidationError:
        return ipc_schema.StatusCode.INVALID, None

    # app_model = AppModel.construct(app_move_req.app)
    app_index = app_move_req.app_index
    app_type = app_move_req.app_type
    device = app_move_req.device

    AppModel.change_device_by_index(app_index, app_type, device)

    return ipc_schema.StatusCode.OK, None


@ipc.command('app_volume', sflags.APP, save_config=False)
def app_volume(req: requests.AppVolume):
    '''
    Recives a volume reques
    '''

    try:
        app_volume_req = requests.AppVolume(**req)
    except ValidationError:
        return ipc_schema.StatusCode.INVALID, None

    app_index = app_volume_req.app_index
    app_type = app_volume_req.app_type
    volume = app_volume_req.volume

    AppModel.set_volume_by_index(app_index, app_type, volume)

    return ipc_schema.StatusCode.OK, None


@ipc.command('app_mute', sflags.APP, save_config=False)
def app_mute(req: requests.AppMute):
    '''
    Recives a volume reques
    '''

    try:
        app_mute_req = requests.AppMute(**req)
    except ValidationError:
        return ipc_schema.StatusCode.INVALID, None

    app_index = app_mute_req.app_index
    app_type = app_mute_req.app_type
    state = app_mute_req.state

    AppModel.set_mute_by_index(app_index, app_type, state)

    return ipc_schema.StatusCode.OK, None


@ipc.command('app_list', sflags.APP, notify=False, save_config=False)
def app_list(req: requests.AppList):
    '''
    Recives an AppList request, returns a list of apps of a given type
    '''

    try:
        app_list_req = requests.AppList(**req)
    except ValidationError:
        return ipc_schema.StatusCode.INVALID, None

    apps = AppModel.list_apps(app_list_req.app_type)

    return ipc_schema.StatusCode.OK, apps
