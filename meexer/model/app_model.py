from meexer.scripts import pmctl
from meexer.schemas.app_schema import AppSchema


class AppModel(AppSchema):
    '''
    Not sure yet if there should be an app model, or an app_list model
    '''

    def __init__(self, **kwargs):
        super.__init__(**kwargs)

    def set_volume(self, val: int):
        pmctl.app_volume(self.app_type, self.index, val)

    def change_device(self, device_name: str):
        print(self)
        pmctl.move_app_device(self.app_type, self.index, device_name)

    @classmethod
    def list_apps(app_type):
        app_list_full = pmctl.list_apps(app_type)
        app_list = []
        for index, label, icon, volume, device in app_list_full:
            app = AppModel(
                app_type=app_type,
                index=index,
                label=label,
                icon=icon,
                volume=volume,
                device=device
            )
            app_list.append(app)
        return app_list
