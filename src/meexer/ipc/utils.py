import asyncio
import json
import logging
from meexer.settings import CLIENT_ID_LEN, REQUEST_SIZE_LEN
from meexer.schemas import ipc_schema

LOG = logging.getLogger("generic")


async def get_message(reader: asyncio.StreamReader) -> str:
    '''
    Get a message
    '''

    msg_len: bytes = await reader.readexactly(REQUEST_SIZE_LEN)
    LOG.debug(msg_len.decode('utf-8'))
    msg: bytes = await reader.readexactly(int(msg_len))
    if not msg:
        raise ConnectionAbortedError()

    return msg.decode('utf-8')


async def send_message(msg: bytes, writer: asyncio.StreamWriter) -> None:
    '''
    Send a msg
        "req" is the req object
    '''

    LOG.debug(msg_len_to_str(len(msg)))
    writer.write(msg_len_to_str(len(msg)))
    await writer.drain()
    LOG.debug(msg)
    writer.write(msg)
    await writer.drain()


async def get_response(reader: asyncio.StreamReader = None) -> ipc_schema.Response:
    '''
    Read msg from client and convert to Request
    '''

    msg = await get_message(reader)
    msg_dict = json.loads(msg)
    res: ipc_schema.Response = ipc_schema.Response(**msg_dict)
    return res


async def get_request(reader: asyncio.StreamReader = None) -> ipc_schema.Request:
    '''
    Read msg from client and convert to Request
    '''

    msg = await get_message(reader)
    msg_dict = json.loads(msg)
    req: ipc_schema.Request = ipc_schema.Request(**msg_dict)
    return req


async def send_response(writer: asyncio.StreamWriter, res: ipc_schema.Response):
    msg = res.json().encode('utf-8')
    await send_message(msg, writer)


async def send_request(writer: asyncio.StreamWriter, reader: asyncio.StreamReader,
                       command: str, data: dict, sender_id: int) -> ipc_schema.Response:
    '''
    Send a request to the server
        "req" is the req object
    '''

    req = ipc_schema.Request(
        command=command,
        sender_id=sender_id,
        data=data
    )

    msg = req.json().encode('utf-8')
    await send_message(msg, writer)
    res = await get_response(reader)
    return res


def id_to_str(client_id: int) -> str:
    return str.encode(str(client_id).zfill(CLIENT_ID_LEN))


def msg_len_to_str(msg_len: int) -> str:
    return str.encode(str(msg_len).zfill(REQUEST_SIZE_LEN))
