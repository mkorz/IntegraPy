# -*- coding: UTF-8 -*-
from binascii import unhexlify


def test_checksum():
    from ..integra import checksum

    assert checksum(b'\x09') == 0xD7EB
    assert checksum(b'\x1C') == 0xD7FE


def test_prepare_frame():
    from ..integra import prepare_frame

    assert prepare_frame('09') == unhexlify('FEFE09D7EBFE0D')
    assert prepare_frame('1C') == unhexlify('FEFE1CD7FEF0FE0D')


def test_parse_event():
    from ..integra import parse_event
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
