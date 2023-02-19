from pydantic import BaseModel, validator
from typing import Literal


class AppSchema(BaseModel):
    '''
    Schema for sink_inputs and source_outputs
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
    device: str

    @validator('icon')
    def set_icon(cls, icon):
        return icon or 'audio-card'
