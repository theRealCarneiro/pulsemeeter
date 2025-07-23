from typing import Literal
from pydantic import validator, BaseModel
from pulsemeeter.scripts import pmctl
from pulsemeeter.schemas.typing import Volume
from pulsemeeter.model.signal_model import SignalModel


class AppModel(BaseModel):
    '''
    Model for sink_inputs and source_outputs
        "index" is the app index in pulse
        "label" is the app name
        "icon" is name of the icon of the app
        "volume" is the app volume in pulse
        "device" is the sink or source it's bound into
    '''
    app_type: Literal['sink_input', 'source_output']
    index: int
    label: str
    icon: str | None
    volume: int
    mute: bool
    device: str

    @validator('icon')
    def set_icon(cls, icon):
        '''
        Some applications don't have an icon name in pulse so we set a default one
        '''
        return icon or 'audio-card'

    def set_volume(self, val: Volume):
        self.volume = val
        # pmctl.app_volume(self.app_type, self.index, val)

    def set_mute(self, state: bool):
        self.mute = state
        # pmctl.app_mute(self.app_type, self.index, state)

    def change_device(self, device_name: str):
        self.device = device_name
        # print(self)
        # pmctl.move_app_device(self.app_type, self.index, device_name)

    @classmethod
    def pa_to_app_model(cls, app, app_type: str):
        '''
        Returns an AppModel of an app
            "app" is the pulsectl object of the app
            "app_type" is either 'sink_input' or 'source_output'
        '''

        app = cls(
            app_type=app_type,
            index=app.index,
            label=app.proplist['application.name'],
            icon=app.proplist.get('application.icon_name'),
            volume=int(app.volume.values[0] * 100),
            mute=bool(app.mute),
            device=app.device_name
        )

        return app

    @classmethod
    def get_app_by_id(cls, index: str, app_type: str):
        '''
        Returns an AppModel of an app with specific index
            "index" is the index of the app
            "app_type" is either 'sink_input' or 'source_output'
        '''
        app = pmctl.app_by_id(index, app_type)
        app_model = cls.pa_to_app_model(app, app_type)
        return app_model

    @classmethod
    def list_apps(cls, app_type: str, pa_app_list: list):
        '''
        Returns a list of AppModels
            "index" is the index of the app
            "app_type" is either 'sink_input' or 'source_output'
        '''
        app_list = []
        for app in pa_app_list:
            app = cls.pa_to_app_model(app, app_type)
            app_list.append(app)
        return app_list
