from meexer.schemas.ipc_schema import SubscriptionFlags as sflags
from meexer.ipc.server import Server as ipc
from meexer.model.config_model import ConfigModel

CONFIG = ConfigModel()


@ipc.command('exit', sflags.MUTE | sflags.APP, True, True)
def close_server(self):
    '''
    Closes server, saves the config file, and can save
    '''
    CONFIG.write()
    # cleanup


@ipc.command('save', 0, False, save_config=True)
def save_config(self):
    '''
    Saves the current configuration to file by signaling the
    server that we want to save, and avoid having to call the
    actual saving function
    '''
    pass
