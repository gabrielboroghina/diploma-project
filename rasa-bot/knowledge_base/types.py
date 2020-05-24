from enum import Enum


class InfoType(Enum):
    LOC = 'LOC'
    VAL = 'VAL'
    TIME_POINT = 'TIME_POINT'
    TIME_START = 'TIME_START'
    TIME_END = 'TIME_END'
    TIME_RANGE = 'TIME_RANGE'
    TIME_DURATION = 'TIME_DURATION'
