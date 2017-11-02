# -*- coding: UTF-8 -*-
from binascii import unhexlify


def test_set_bits_positions():
    from .. import set_bits_positions
    assert set_bits_positions(
        b'\x04 \x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x80',
        1
    ) == set([3, 14, 128])


def test_bytes_with_bits_set():
    from .. import bytes_with_bits_set
    assert bytes_with_bits_set(set([3, 14, 128]), 128, 1) == \
        b'\x04 \x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x80'


def test_format_user_code():
    from .. import format_user_code
    assert format_user_code(1234) == b'\x12\x34\xFF\xFF\xFF\xFF\xFF\xFF'
    assert format_user_code(1234, prefix=97) == \
        b'\x97\x12\x34\xFF\xFF\xFF\xFF\xFF'


def test_checksum():
    from .. import checksum

    assert checksum(b'\x09') == 0xD7EB
    assert checksum(b'\x1C') == 0xD7FE


def test_prepare_frame():
    from .. import prepare_frame

    assert prepare_frame('09') == unhexlify('FEFE09D7EBFE0D')
    assert prepare_frame('1C') == unhexlify('FEFE1CD7FEF0FE0D')


def test_parse_event():
    from .. import parse_event
    result = parse_event(b'\x7f\x98\x83\x13]\xa6\n\x02\x06h\xde\xff\xff\xff')

    assert result.year == 2017 % 4
    assert result.not_empty
    assert result.present
    assert result.monitoring_s1 == 'not monitored'
    assert result.monitoring_s2 == 'not monitored'
    assert result.event_class == 'access control'
    assert result.day == 24
    assert result.time == '13:07'
    assert result.month == 8
    assert result.code == 422
    assert result.restore
    assert result.partition == 11
    assert result.source_number == 10
    assert result.object_number == 0
    assert result.user_control_number == 2

    assert result.calling_event_index == b'FFFFFF'
    assert result.event_index == b'0668DE'
