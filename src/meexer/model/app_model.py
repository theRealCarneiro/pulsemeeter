from meexer.scripts import pmctl
from meexer.schemas.app_schema import AppSchema


class AppModel(AppSchema):
    '''
    Not sure yet if there should be an app model, or an app_list model
    '''

    def set_volume(self, val: int):
        pmctl.app_volume(self.app_type, self.index, val)

    def set_mute(self, state: bool):
        pmctl.app_mute(self.app_type, self.index, state)

    def change_device(self, device_name: str):
        print(self)
        pmctl.move_app_device(self.app_type, self.index, device_name)

    @staticmethod
    def set_volume_by_index(index: int, app_type: str, volume: int):
        '''
        Set an app volume by the app's index
        '''
        pmctl.app_volume(app_type, index, volume)

    @staticmethod
    def set_mute_by_index(index: int, app_type: str, state: bool):
        '''
        Set an app mute state by the app's index
        '''
        pmctl.app_mute(app_type, index, state)

    @staticmethod
    def change_device_by_index(app_index: int, app_type: str, device: str):
        '''
        Change an app output by the app's index
        '''
        pmctl.move_app_device(app_type, app_index, device)

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
    def list_apps(cls, app_type: str):
        '''
        Returns a list of AppModels
            "index" is the index of the app
            "app_type" is either 'sink_input' or 'source_output'
        '''
        app_list = []
        for app in pmctl.list_apps(app_type):
            app = cls.pa_to_app_model(app, app_type)
            app_list.append(app)
        return app_list
