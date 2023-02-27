import os
import json
from meexer.schemas.config_schema import ConfigSchema
from meexer.model.device_model import DeviceModel
# from meexer.schemas.device_schema import DeviceSchema
from meexer.settings import CONFIG_DIR, CONFIG_FILE
CONFIG_FILE += '.test.json'


def singleton(class_):
    instances = {}

    def get_instance(*args, **kwargs):
        if class_ not in instances:
            instances[class_] = class_(*args, **kwargs)
        return instances[class_]

    return get_instance


@singleton
class ConfigModel(ConfigSchema):
    '''
    '''

    # ensure that we use DeviceModel instead of DeviceSchema so that pmctl works
    vi: dict[str, DeviceModel] = {}
    b: dict[str, DeviceModel] = {}
    hi: dict[str, DeviceModel] = {}
    a: dict[str, DeviceModel] = {}

    def __init__(self, *args, **kwargs):
        config = self.load_config()
        super().__init__(**config)

    def write(self):
        '''
        Write configuration to file
        '''
        if not os.path.isdir(CONFIG_DIR):
            os.mkdir(CONFIG_DIR)
        # LOG.debug("writing config")
        with open(CONFIG_FILE, 'w') as outfile:
            json.dump(self.dict(), outfile, indent='\t', separators=(',', ': '))

    def load_config(self):
        '''
        Load config from file
        '''
        with open(CONFIG_FILE, 'r') as outfile:
            config = json.load(outfile)

        return config

    def get_device(self, dtype: str, did: str):
        '''
        Get a device by it's id
        '''
        return self.__dict__[dtype][did]

    def get_max_id(self, device_type: str):
        pass

    def insert_device(self, device: DeviceModel):
        '''
        Insert a device into config
        '''

        device_type = device.get_type()

        # get max id
        device_id = max(self.__dict__[device_type], key=int, default='0')

        # get new id
        device_id = str(int(device_id) + 1)

        # add device to dict
        self.__dict__[device_type][device_id] = device

    def remove_device(self, device_type: str, device_index: str):
        '''
        Remove a device from config
        '''
        return self.__dict__[device_type].pop(device_index)
