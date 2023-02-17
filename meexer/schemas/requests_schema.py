from pydantic import BaseModel, Field
from typing import Literal

from meexer.schemas import device_schema, app_schema


class DeviceIndex(BaseModel):
    device_type: str = Field(..., regex='[vi|hi|a|b]')
    device_id: str = Field(..., regex='[1-9]+')


class CreateDevice(BaseModel):
    device: device_schema.DeviceSchema


class RemoveDevice(BaseModel):
    index: DeviceIndex


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


class AppVolume(BaseModel):
    app: app_schema.AppSchema
    volume: int = Field(..., ge=0, le=154)


class AppMove(BaseModel):
    app: app_schema.AppSchema
    device: str
