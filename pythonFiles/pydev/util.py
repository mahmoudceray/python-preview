import sys
import struct

UNICODE_PREFIX = b'U'
ASCII_PREFIX = b'A'
NONE_PREFIX = b'N'


def to_bytes(cmd_str):
    return cmd_str.encode('ascii')


def to_str(cmd_bytes):
    return cmd_bytes.decode('ascii')


def read_bytes(conn, count):
    b = b''
    while len(b) < count:
        received_data = conn.recv(count - len(b))
        if received_data is None:
            break
        b += received_data
    return b


def write_bytes(conn, b):
    conn.sendall(b)


def read_int(conn):
    return struct.unpack('!q', read_bytes(conn, 8))[0]


def write_int(conn, i):
    write_bytes(conn, struct.pack('!q', i))


def read_string(conn):
    str_len = read_int(conn)
    if not str_len:
        return ''
    res = b''
    while len(res) < str_len:
        res = res + conn.recv(str_len - len(res))
    res = res.decode('utf-8')
    return res


def write_string(conn, s):
    if s is None:
        write_bytes(conn, NONE_PREFIX)
    elif isinstance(s, str):
        b = s.encode('utf-8')
        b_len = len(b)
        write_bytes(conn, UNICODE_PREFIX)
        write_int(conn, b_len)
        if b_len > 0:
            write_bytes(conn, b)
    else:
        s_len = len(s)
        write_bytes(conn, ASCII_PREFIX)
        write_int(conn, s_len)
        if s_len > 0:
            write_bytes(conn, s)
