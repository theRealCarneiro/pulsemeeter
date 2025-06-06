from pulsemeeter.schemas.ipc_schema import StatusCode
from pulsemeeter.schemas.ipc_schema import SubscriptionFlags as sflags
from pulsemeeter.ipc.router import Blueprint
from pulsemeeter.model.config_model import ConfigModel

CONFIG = ConfigModel()
ipc = Blueprint('server')


@ipc.command('exit', sflags.APP, True, True)
async def close_server(_):
    '''
    Closes server, saves the config file, and can save
    '''
    return 'exit'
    # return StatusCode.OK, None
    # cleanup


@ipc.command('save', 0, False, save_config=True)
async def save_config(_):
    '''
    Saves the current configuration to file by signaling the
    server that we want to save, and avoid having to call the
    actual saving function
    '''
    CONFIG.write()


@ipc.command('get_config', 0, False, save_config=False)
async def get_config(_):
    '''
    Returns the config
    '''
    return CONFIG.__dict__
