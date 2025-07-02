'''
Schemas for the ipc
'''

import threading
import socket
from enum import Enum
from typing import Callable, Any
from pydantic import BaseModel, Field


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
    IGNORE = 5  # internal error


class Route(BaseModel):
    command: Callable[[Any], Any]
    schema_hint: Any
    notify: bool
    save_config: bool
    flags: int = 0


class Task(BaseModel):
    command: Callable[[Any], Any]
    # schema_hint: Any
    # notify: bool
    # save_config: bool
    # flags: int = 0


class Client(BaseModel):
    conn: socket.socket
    id: int
    flags: int
    thread: threading.Thread | None = Field(...)

    class Config:
        arbitrary_types_allowed = True


class Event(BaseModel):
    '''
    Schema for events
        "command" is the name of the command/route
        "sender_id" is the id of the client who sent the msg
        "data" is a dict containing the actual request
        "id" is a integer used by the client to know if it's own request when answerd
        "run" is a bool, True means run the request,
            False means don't run it
    '''
    command: str
    sender_id: int
    data: dict
    id: int
    run: bool = True


class Request(BaseModel):
    '''
    Schema for requests
        "command" is the name of the command/route
        "sender_id" is the id of the client who sent the msg
        "data" is a dict containing the actual request
        "id" is a integer used by the client to know if it's own request when answerd
        "run" is a bool, True means run the request,
            False means don't run it
    '''
    command: str
    sender_id: int
    data: dict
    run: bool = True

    def encode(self) -> bytes:
        return self.json().encode('utf-8')


class Response(BaseModel):
    '''
    Schema for requests
        "status" is the Enum StatusCode
        "sender_id" is the id of the client who sent the msg
        "data" is a dict containing the actual request
        "id" is a integer used by the client to know if it's own request when answerd
    '''
    status: StatusCode
    data: Any | None

    def encode(self) -> bytes:
        return self.json().encode('utf-8')
