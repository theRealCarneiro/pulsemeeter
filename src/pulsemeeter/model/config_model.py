import logging

from pydantic import BaseModel, field_validator
from pulsemeeter.model.device_model import DeviceModel

LOG = logging.getLogger("generic")


class ConfigModel(BaseModel):
    '''
    Model for the config file, has functions to load and write the file
    '''

    devices: dict[str, dict[str, DeviceModel]] = {'vi': {}, 'hi': {}, 'a': {}, 'b': {}}
    vumeters: bool = True
    cleanup: bool = False
    tray: bool = False
    layout: str = 'Blocks'
    window_width: int = 800

    @field_validator('layout')
    @classmethod
    def capitalize_layout(cls, v):
        return v.capitalize()
    window_height: int = 600
