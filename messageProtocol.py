from enum import Enum
from json import loads


class Type(Enum):
    REQUEST = 0
    RESPONSE = 1


class Header(Enum):
    PING = 0
    DISCOVER = 1
    PUBLISH = 2
    FETCH = 3
    REGISTER = 4
    RETRIEVE = 5
    INITCON = 6
    LEAVE = 7



class Message:
    def __init__(self, header, type, info, json_string=None):
        if json_string:
            __tmp__ = loads(json_string)
            header = Header(__tmp__['header'])
            type = Type(__tmp__['type'])
            info = __tmp__['info']
        self._header = header
        self._type = type
        self._info = info

    def get_header(self):
        return self._header

    def get_type(self):
        return self._type

    def get_info(self):
        return self._info

    def get_packet(self):
        return {'header': self._header.value, 'type': self._type.value, 'info': self._info}