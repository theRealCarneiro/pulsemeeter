from pydantic import BaseModel, Field
from typing import Callable
from enum import Enum
import threading
import socket


class SubscriptionFlags:
    NO_LISTEN = 0
    ALL = 1 << 0
    DEVICE = 1 << 1
    CONNECTION = 1 << 2
    VOLUME = 1 << 3
    APP = 1 << 4
    RNNOISE = 1 << 5
    EQ = 1 << 6
    DEVICE_NEW = 1 << 7
    DEVICE_REMOVE = 1 << 8
    DEVICE_CHANGED = 1 << 9


class StatusCode(Enum):
    OK = 0  # succefull
    INVALID = 1  # invalid input from client
    ERROR = 2  # internal error


class Route(BaseModel):
    command: Callable[[any], any]
    notify: bool
    save_config: bool
    flags: int = 0


class Client(BaseModel):
    conn: socket.socket
    id: int
    flags: int
    thread: threading.Thread | None = Field(...)

    class Config:
        arbitrary_types_allowed = True


class Request(BaseModel):
    command: str
    sender_id: str
    data: dict
    flags: int = 0


class Response(BaseModel):
    status: StatusCode
    sender_id: str
    data: dict | None = Field(...)
