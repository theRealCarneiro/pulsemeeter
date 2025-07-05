import os
import logging
import json
from pulsemeeter.model.signal_model import SignalModel
from pulsemeeter.model.device_manager_model import DeviceManagerModel
from pulsemeeter.settings import CONFIG_DIR, CONFIG_FILE
# CONFIG_FILE += '.test.json'

LOG = logging.getLogger("generic")


# def singleton(class_):
#     instances = {}
#
#     def get_instance(*args, **kwargs):
#         if class_ not in instances:
#             instances[class_] = class_(*args, **kwargs)
#         return instances[class_]
#
#     return get_instance
#
#
# @singleton
class ConfigModel(SignalModel):
    '''
    Model for the config file, has functions to load and write the file
    '''

    device_manager: DeviceManagerModel = DeviceManagerModel()
    vumeters: bool = True
    cleanup: bool = False
    tray: bool = False
    layout: str = 'blocks'
    # connection_manager: ConnectionManagerModel

    def model_post_init(self, _):
        self.device_manager.connect('connect', self.device_manager_callbacks)
        self.device_manager.connect('device_new', self.device_manager_callbacks)
        self.device_manager.connect('device_remove', self.device_manager_callbacks)

    def device_manager_callbacks(self, *args):
        self.write()

    def write(self):
        '''
        Write configuration to file
        '''
        if not os.path.isdir(CONFIG_DIR):
            os.mkdir(CONFIG_DIR)
        LOG.debug("Writing config")
        with open(CONFIG_FILE, 'w', encoding='utf-8') as outfile:
            json.dump(self.dict(), outfile, indent='\t', separators=(',', ': '))

    @classmethod
    def load_config(cls):
        '''
        Load config from file
        '''
        if not os.path.exists(CONFIG_FILE):
            return cls()

        with open(CONFIG_FILE, 'r', encoding='utf-8') as outfile:
            config = json.load(outfile)

        instance = cls(**config)
        return instance

    # def get_device(self, dtype: str, did: str):
    #     '''
    #     Get a device by it's id
    #     '''
    #     return self.__dict__[dtype][did]

    # def get_primary(self, device_type: str):
    #     '''
    #     Get a device by it's id
    #     '''
    #     for _, item in self.__dict__['vi' if device_type == 'sink' else 'b'].items():
    #         if item.primary is True:
    #             return item.name
    #
    #     return None

    # def find_device(self, device_type, name):
    #     dtypes = ('a', 'vi') if device_type == 'sink' else ('b', 'hi')
    #     for dtype in dtypes:
    #         for did, item in self.__dict__[dtype].items():
    #             if item.name == name:
    #                 return dtype, did, item
    #
    #     return None, None, None

    # def get_max_id(self, device_type: str):
    #     pass

    # def create_device(self, data: dict ):
    #     '''
    #     Insert a device into config
    #     '''
    #
    #     device = DeviceModel(**data)
    #     device_type, device_id, device = self.device_manager.create_device(device)
        # Create Connection Models
        # Insert Connection Models on Connection Manager

        # device_type = device.get_type()
        #
        # # get max id
        # device_id = max(self.__dict__[device_type], key=int, default='0')
        #
        # # get new id
        # device_id = str(int(device_id) + 1)
        #
        # # add device to dict
        # self.__dict__[device_type][device_id] = device
        #
        # # new output added
        # if device_type in ('a', 'b'):
        #     for ndev_type in ('vi', 'hi'):
        #         for ndev_id in self.__dict__[ndev_type]:
        #             conn = ConnectionSchema(nick=device.nick)
        #             self.__dict__[ndev_type][ndev_id].connections[device_type][device_id] = conn.__dict__
        #
        # # new input added
        # else:
        #     for ndev_type in ('a', 'b'):
        #         for ndev_id in self.__dict__[ndev_type]:
        #             target_device = self.__dict__[ndev_type][ndev_id]
        #             conn = ConnectionSchema(nick=target_device.nick)
        #             self.__dict__[device_type][device_id].connections[ndev_type][ndev_id] = conn

    # def remove_device(self, device_type: str, device_index: str):
    #     '''
    #     Remove a device from config
    #     '''
    #     return self.__dict__[device_type].pop(device_index)
