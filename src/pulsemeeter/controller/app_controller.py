# from typing import Literal
# from pydantic import validator, root_validator
# from pulsemeeter.model.config_model import ConfigModel
from pulsemeeter.scripts import pmctl
from pulsemeeter.schemas.typing import Volume
from pulsemeeter.model.signal_model import SignalModel
from pulsemeeter.model.app_model import AppModel


class AppController(SignalModel):
    '''
    '''
    # sink_input: dict[int, AppModel]
    # source_output: dict[int, AppModel]
    # config_model: ConfigModel

    # @root_validator(pre=True)
    # def load_app_list(cls, values):
    #     for app_type in ('sink_input', 'source_output'):
    #         # print(cls.list_apps(app_type))
    #         values[app_type] = cls.list_apps(app_type)
    #
    #     return values

    def set_volume(self, app_type, app_index, val: Volume):
        pmctl.app_volume(app_type, app_index, val)
        self.emit('app_volume', app_type, app_index, val)

    def set_mute(self, app_type, app_index, state: bool):
        pmctl.app_mute(app_type, app_index, state)
        self.emit('app_mute', app_type, app_index, state)

    def change_device(self, app_type, app_index, device_name: str):
        if not device_name:
            device_name = pmctl.get_default_device_name(app_type)
        pmctl.move_app_device(app_type, app_index, device_name)
        self.emit('app_device_change', app_type, app_index, device_name)

    def get_app_by_id(self, index: str, app_type: str):
        '''
        Returns an AppModel of an app with specific index
            "index" is the index of the app
            "app_type" is either 'sink_input' or 'source_output'
        '''
        app = pmctl.app_by_id(index, app_type)
        app_model = AppModel.pa_to_app_model(app, app_type)
        return app_model

    @classmethod
    def list_apps(cls, app_type: str) -> dict[str, AppModel]:
        '''
        Returns a list of AppModels
            "index" is the index of the app
            "app_type" is either 'sink_input' or 'source_output'
        '''
        pa_app_list = pmctl.list_apps(app_type)

        app_dict = {}
        for app in pa_app_list:
            app = AppModel.pa_to_app_model(app, app_type)
            app_dict[app.index] = app

        return app_dict
