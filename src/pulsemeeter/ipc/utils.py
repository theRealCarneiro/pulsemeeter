import logging
from pulsemeeter.settings import CLIENT_ID_LEN, REQUEST_SIZE_LEN


def id_to_bytes(client_id: int) -> bytes:
    return str(client_id).zfill(CLIENT_ID_LEN).encode('utf-8')
    # return str.encode(encoding='utf-8', str(client_id).zfill(CLIENT_ID_LEN))


def msg_len_to_bytes(msg_len: int) -> bytes:
    return str(msg_len).zfill(REQUEST_SIZE_LEN).encode('utf-8')
    # return str.encode(encoding='utf-8', str(msg_len).zfill(REQUEST_SIZE_LEN))
