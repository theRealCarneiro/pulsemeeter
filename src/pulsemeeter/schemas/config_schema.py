from pydantic import BaseModel
from pulsemeeter.schemas.device_schema import DeviceSchema


class ConfigSchema(BaseModel):
    vi: dict[str, DeviceSchema] = {}
    b: dict[str, DeviceSchema] = {}
    hi: dict[str, DeviceSchema] = {}
    a: dict[str, DeviceSchema] = {}
    vumeters: bool = True
    cleanup: bool = False
    tray: bool = False
    layout: str = 'defaulth'
