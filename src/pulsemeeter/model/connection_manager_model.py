import logging

from pydantic import BaseModel
# from pulsemeeter.model.device_model import DeviceModel
from pulsemeeter.model.connection_model import ConnectionModel
from pulsemeeter.model.signal_model import SignalModel

LOG = logging.getLogger("generic")


class ConnectionManagerModel(SignalModel):
    '''
    Model for the config file, has functions to load and write the file
    '''

    # a: dict[str, ConnectionModel] = {}
    # b: dict[str, ConnectionModel] = {}

    vi: dict[str, dict[str, ConnectionModel]] = {}
    hi: dict[str, dict[str, ConnectionModel]] = {}

    def model_post_init(self, _):
        for input_type, input_model_dict in self.__dict__.items():
            for input_id, input_model in input_model_dict.items():
                for output_type, output_model_dict in input_model:
                    for output_id, output_model in input_model_dict.items():
                        output_model.connect('connection', self.propagate, device_type, device_id)


        for device_type, connections in self.__dict__.items():
            for device_id, connection_model in connections.items():
                connection_model.connect('connection', self.propagate, device_type, device_id)

    def remove_device(self, device_type, device_id):

        device_dict = self.__dict__.get(device_type)

        # means that the removed device is either vi or hi
        if device_dict is not None:
            device_dict.pop(device_id)
            return

        # means that the removed device is either a or b
        # so we remove them from all input devices
        for _, device_dict in self.__dict__.items():
            for input_id, input_dict in device_dict.items():
                input_dict.pop(input_id)

    # def propagate(self, state, device_type, device_id):
    #     print(state, device_type, device_id)

    # def connect_devices(self, output_device: DeviceModel, state: bool):
        # pass

    # def get_connection(self, dtype: str, did: str):
    #     '''
    #     Get a device by it's id
    #     '''
    #     return self.__dict__[dtype][did]
