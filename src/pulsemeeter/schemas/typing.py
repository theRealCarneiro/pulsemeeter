from typing import Literal
from pydantic import conint

Volume = conint(ge=0, le=153)

DeviceClass = Literal['virtual', 'hardware']
PaDeviceType = Literal['sink', 'source']
