from meexer.settings import CLIENT_ID_LEN, REQUEST_SIZE_LEN


def id_to_str(client_id: int) -> str:
    return str.encode(str(client_id).rjust(CLIENT_ID_LEN, '0'))


def msg_len_to_str(msg_len: int) -> str:
    return str.encode(str(msg_len).rjust(REQUEST_SIZE_LEN, '0'))
