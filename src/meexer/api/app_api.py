from pydantic import ValidationError
from meexer.schemas import requests_schema as requests
from meexer.schemas import ipc_schema
from meexer.schemas.ipc_schema import SubscriptionFlags as sflags
from meexer.ipc.router import Blueprint
from meexer.model.app_model import AppModel
from meexer.scripts import pmctl_async as pmctl

ipc = Blueprint('app')


@ipc.command('app_move', sflags.APP, save_config=False)
async def app_move(req: requests.AppMove):
    '''
    Recives an AppMove request, changes the device an app is bound into
    '''

    try:
        app_move_req = requests.AppMove(**req)
    except ValidationError:
        return ipc_schema.StatusCode.INVALID, None

    app_index = app_move_req.app_index
    app_type = app_move_req.app_type
    device = app_move_req.device
    await pmctl.move_app_device(app_type, app_index, device)

    return ipc_schema.StatusCode.OK, None


@ipc.command('app_volume', sflags.APP, save_config=False)
async def app_volume(req: requests.AppVolume):
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

    await pmctl.app_volume(app_type, app_index, volume)

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

    pmctl.app_mute(app_type, app_index, state)

    return ipc_schema.StatusCode.OK, None


@ipc.command('app_list', sflags.APP, notify=False, save_config=False)
async def app_list(req: requests.AppList):
    '''
    Recives an AppList request, returns a list of apps of a given type
    '''

    # try:
    #     app_list_req = requests.AppList(**req)
    # except ValidationError:
    #     return ipc_schema.StatusCode.INVALID, None

    pa_app_list = await pmctl.list_apps(req.app_type)
    apps = AppModel.list_apps(req.app_type, pa_app_list)

    return apps


@ipc.command('app_get', 0, notify=False, save_config=False)
async def app_get(req: requests.AppGet):
    '''
    Recives an AppGet request, returns an app of a given type
    '''
    try:
        app_get_req = requests.AppGet(**req)
    except ValidationError:
        return ipc_schema.StatusCode.INVALID, None

    app_index = app_get_req.app_index
    app_type = app_get_req.app_type
    app = pmctl.app_by_id(app_index, app_type)
    app_model = AppModel.pa_to_app_model(app, app_type)
    return ipc_schema.StatusCode.OK, app_model
