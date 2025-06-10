from typing import Literal
from pydantic import BaseModel, Field, root_validator

from pulsemeeter.schemas import device_schema


class PulseEvent(BaseModel):
    device_index: int
    device_type: Literal['sink', 'source', 'sink_input', 'source_output', 'server']
    event_type: Literal['change', 'new', 'remove']


class PaDeviceChange(PulseEvent):
    device_type: str
    device_id: str
    device_name: str
    volume: list[int]
    mute: bool


class PaAppChange(PulseEvent):
    device_index: int
    device_type: Literal['sink_input', 'source_output']
    output_name: str  # the name of the source or sink
    volume: list[int]
    mute: bool


class PaServerChange(PulseEvent):
    device_index: int
    device_type: Literal['sink_input', 'source_output']


class DeviceIndex(BaseModel):
    device_type: str = Field(..., pattern='[vi|hi|a|b]')
    device_id: str = Field(..., pattern='[1-9]+')


class CreateDevice(BaseModel):
    device: device_schema.DeviceSchema


class RemoveDevice(BaseModel):
    index: DeviceIndex


class UpdateDevice(BaseModel):
    index: DeviceIndex
    device: device_schema.DeviceSchema


class UpdateConnection(BaseModel):
    index: DeviceIndex
    connection: device_schema.ConnectionSchema


class Connect(BaseModel):
    source: DeviceIndex
    output: DeviceIndex
    state: bool | None = Field(...)


class Mute(BaseModel):
    index: DeviceIndex
    state: bool | None = Field(...)


class Volume(BaseModel):
    index: DeviceIndex
    volume: int = Field(..., ge=0, le=154)


class Default(BaseModel):
    index: DeviceIndex


class Rnnoise(BaseModel):
    index: DeviceIndex
    control: str
    state: bool | None = Field(...)


class Eq(BaseModel):
    index: DeviceIndex
    control: str
    state: bool | None = Field(...)


class DeviceList(BaseModel):
    device_type: Literal['sink', 'source']


class AppList(BaseModel):
    app_type: Literal['sink_input', 'source_output']


class AppGet(BaseModel):
    app_type: Literal['sink_input', 'source_output']
    app_index: int


class AppVolume(BaseModel):
    app_type: Literal['sink_input', 'source_output']
    app_index: int
    volume: int = Field(..., ge=0, le=154)


class AppMute(BaseModel):
    app_type: Literal['sink_input', 'source_output']
    app_index: int
    state: bool


class AppMove(BaseModel):
    app_type: Literal['sink_input', 'source_output']
    app_index: int
    device: str


class AppRemove(BaseModel):
    app_type: Literal['sink_input', 'source_output']
    app_index: int
