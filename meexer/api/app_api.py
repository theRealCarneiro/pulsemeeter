from meexer.schemas import requests_schema as requests
from meexer.schemas import ipc_schema
from meexer.schemas.ipc_schema import SubscriptionFlags as sflags
from meexer.ipc.router import Router as ipc
from meexer.model.app_model import AppModel
from pydantic.error_wrappers import ValidationError


@ipc.command('app_move', sflags.APP, save_config=False)
def app_move(req: requests.AppMove):
    '''
    Recives an AppMove request, changes the device an app is bound into
    '''

    try:
        app_move_req = requests.AppMove(**req)
    except ValidationError:
        return ipc_schema.StatusCode.INVALID, None

    app_model = AppModel.construct(app_move_req.app)
    app_model.change_device(app_move_req.device)


@ipc.command('app_volume', sflags.APP, save_config=False)
def app_volume(req: requests.AppVolume):
    '''
    Recives a volume reques
    '''

    try:
        app_volume_req = requests.AppVolume(**req)
    except ValidationError:
        return ipc_schema.StatusCode.INVALID, None

    app_model = AppModel.construct(app_volume_req.app)
    app_model.set_volume(app_volume_req.volume)


@ipc.command('app_list', sflags.APP, notify=False, save_config=False)
def app_list(req: requests.AppList):
    '''
    Recives an AppList request, returns a list of apps of a given type
    '''

    try:
        app_list_req = requests.AppList(**req)
    except ValidationError:
        return ipc_schema.StatusCode.INVALID, None

    app_list = AppModel.list_apps(app_list_req.app_type)

    return ipc_schema.StatusCode.OK, app_list
