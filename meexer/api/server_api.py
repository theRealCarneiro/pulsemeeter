from meexer.schemas.ipc_schema import StatusCode
from meexer.schemas.ipc_schema import SubscriptionFlags as sflags
from meexer.ipc.router import Router as ipc
from meexer.model.config_model import ConfigModel

CONFIG = ConfigModel()


@ipc.command('exit', sflags.APP, True, True)
def close_server(req):
    '''
    Closes server, saves the config file, and can save
    '''
    print('exit')
    return StatusCode.OK, None
    # CONFIG.write()
    # cleanup


@ipc.command('save', 0, False, save_config=True)
def save_config():
    '''
    Saves the current configuration to file by signaling the
    server that we want to save, and avoid having to call the
    actual saving function
    '''
    pass


@ipc.command('get_config', 0, False, save_config=False)
def get_config(req: dict):
    '''
    Returns the config
    '''
    return StatusCode.OK, CONFIG.__dict__
