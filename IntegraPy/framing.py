# -*- coding: UTF-8 -*-
'''
Protocol framing
'''
try:
    from itertools import zip_longest
except ImportError:
    from itertools import izip_longest as zip_longest


from ctypes import (
    LittleEndianStructure,
    c_uint8,
    c_char,
    memmove,
    sizeof,
    addressof
)
from binascii import hexlify, unhexlify


from .constants import (
    HEADER, FOOTER, EVENT_MONITORING, EVENT_CLASSES, EVENT_DESCRIPTIONS,
    OBJECT_KINDS
)

from bitarray import bitarray


def set_bits_positions(data, offset=1):
    '''
    Returns positions of bits set in a byte array
    '''
    ba = bitarray(endian='little')
    ba.frombytes(bytes(data))

    bits = set(
        idx + 1 for idx, bit in enumerate(ba) if bit
    )
    return bits


def bytes_with_bits_set(positions, length=128, offset=1):
    '''
    Creates a string with bits on selected positions set
    '''
    ba = bitarray(length, endian='little')
    ba.setall(False)

    for pos in positions:
        ba[pos - offset] = True

    return ba.tobytes()


def pairwise(t):
    it = iter(t)
    return zip_longest(it, it, fillvalue='0')


def format_user_code(code, prefix=None):
    '''
    Formats user code (given as an int) to Integra acceptale form
    '''
    def mangle(code):
        return bytearray(
            int(''.join(digits), 16) for digits in pairwise(str(code))
        )

    res = (mangle(prefix) if prefix else bytearray()) + mangle(code)

    if len(res) < 8:
        res += b'\xff' * (8 - len(res))

    return bytes(res)


def checksum(command):
    '''
    Satel communication checksum
    '''
    crc = 0x147A
    for b in bytearray(command):
        # rotate (crc 1 bit left)
        crc = ((crc << 1) & 0xFFFF) | (crc & 0x8000) >> 15
        crc = crc ^ 0xFFFF
        crc = (crc + (crc >> 8) + b) & 0xFFFF

    return crc


def prepare_frame(command):
    '''
    Creates a communication frame (as per Satel manual)
    '''
    data = bytearray(unhexlify(command))
    c = checksum(data)
    data.append(c >> 8)
    data.append(c & 0xFF)
    data = data.replace(b'\xFE', b'\xFE\xF0')

    return HEADER + data + FOOTER


class EventRecord(LittleEndianStructure):
    _fields_ = [
        ('_monitoring_s1', c_uint8, 2),
        ('_monitoring_s2', c_uint8, 2),
        ('present', c_uint8, 1),
        ('not_empty', c_uint8, 1),
        ('_year', c_uint8, 2),
        ('day', c_uint8, 5),
        ('_class', c_uint8, 3),
        ('minutes_high', c_uint8, 4),
        ('month', c_uint8, 4),
        ('minutes_low', c_uint8, 8),
        ('code_high', c_uint8, 2),
        ('restore', c_uint8, 1),
        ('partition', c_uint8, 5),
        ('code_low', c_uint8, 8),
        ('source_number', c_uint8, 8),
        ('user_control_number', c_uint8, 5),
        ('object_number', c_uint8, 3),
        ('_event_index', c_uint8 * 3),
        ('_calling_event_index', c_uint8 * 3)
    ]

    integra = None
    current_year = 0

    @property
    def monitoring_s1(self):
        return EVENT_MONITORING[self._monitoring_s1]

    @property
    def monitoring_s2(self):
        return EVENT_MONITORING[self._monitoring_s2]

    @property
    def event_class(self):
        return EVENT_CLASSES[self._class]

    @property
    def time(self):
        minutes = self.minutes_high * 0x100 + self.minutes_low
        return '{:02d}:{:02d}'.format(
            minutes // 60,
            minutes % 60
        )

    @property
    def year(self):
        return self.current_year // 4 * 4 + self._year

    @property
    def code(self):
        return self.code_high * 0x100 + self.code_low

    @property
    def calling_event_index(self):
        return hexlify(bytearray(self._calling_event_index)).upper()

    @property
    def event_index(self):
        return hexlify(bytearray(self._event_index)).upper()

    @property
    def object_kind(self):
        return OBJECT_KINDS[
            EVENT_DESCRIPTIONS.get(
                (self.code, self.restore), (0, 'UNKNOWN')
            )[0]
        ]

    @property
    def description(self):
        return EVENT_DESCRIPTIONS.get(
            (self.code, self.restore), (0, 'UNKNOWN')
        )[1]

    @property
    def source(self):
        source_kind = EVENT_DESCRIPTIONS.get(
            (self.code, self.restore), (0, 'UNKNOWN')
        )[0]

        if source_kind == 3:
            return self.integra.get_name(2, self.source_number).name
        else:
            return 'Not implemented'

    @property
    def keypad(self):
        source_kind = EVENT_DESCRIPTIONS.get(
            (self.code, self.restore), (0, 'UNKNOWN')
        )[0]

        if source_kind == 3:
            return self.integra.get_name(
                3, 129 + self.restore * 32 + self.partition
            ).name
        else:
            return 'Not implemented'

    def __repr__(self):
        return (
            'Integra event: {0.year:02d}-{0.month:02d}-{0.day:02d} '
            '{0.time}, code: {0.code}, description: {0.description}, '
            'object kind: {0.object_kind}, source number: {0.source_number}'
        ).format(self)


def parse_event(record):
    '''
    Parses an event from 8C command
    '''
    evt = EventRecord()
    fit = min(len(record), sizeof(evt))
    memmove(addressof(evt), bytes(record), fit)

    return evt


class NameRecord(LittleEndianStructure):
    _fields_ = [
        ('_device_type', c_uint8),
        ('device_number', c_uint8),
        ('_device_function', c_uint8),
        ('_device_name', c_char * 16),
        ('serial', c_uint8)
    ]

    encoding = 'cp1250'

    @property
    def device_type(self):
        return OBJECT_KINDS.get(self._device_type, 'Unknown')

    @property
    def device_function(self):
        return self._device_function

    @property
    def name(self):
        return self._device_name.decode(self.encoding).strip()

    def __repr__(self):
        return (
            'Name: {0.name}, type: {0.device_type}'
        ).format(self)


def parse_name(record):
    '''
    Parses a name from EE command
    '''
    nme = NameRecord()
    fit = min(len(record), sizeof(nme))
    memmove(addressof(nme), bytes(record), fit)

    return nme
