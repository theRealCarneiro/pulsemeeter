from pydantic import BaseModel


class AppModel(BaseModel):
    index: int
    label: str
    icon: str
    volume: int
    device: str
