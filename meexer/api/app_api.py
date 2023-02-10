from pulsemeeter.schemas.config import Config
from pulsemeeter.schemas import requests
from pulsemeeter.schemas.ipc import SubscriptionFlags as sflags
# from pulsemeeter.scripts import pmctl
from pulsemeeter.ipc.server import Server as ipc

config = Config(Config.load_config())
print(config)


@ipc.command('app_move', sflags.MUTE | sflags.APP, True, True)
def app_move(self, mute: requests.AppMove):
    '''
    Recives a connection, and connects devices
    '''
    # pmctl.mute(mute.index.device_type, mute.index.device_id, status=mute.state)


@ipc.command('app_volume', sflags.VOLUME | sflags.APP, True, True)
def app_volume(self, volume: requests.AppVolume):
    '''
    Recives a volume reques
    '''
    # pmctl.mute(mute.index.device_type, mute.index.device_id, status=mute.state)
