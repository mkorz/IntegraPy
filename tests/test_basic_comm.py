# -*- coding: UTF-8 -*-
import pytest
from . import INTEGRA_HOST, INTEGRA_PORT, INTEGRA_USER_CODE


@pytest.fixture
def integra():
    from ..integra import Integra

    return Integra(INTEGRA_USER_CODE, INTEGRA_HOST, INTEGRA_PORT)


def test_get_version(integra):
    res = integra.get_version()
    assert 'INTEGRA' in res['model']
    assert '20' in res['version']


def test_get_time(integra):
    res = integra.get_time()
    assert res.year >= 2017


def test_get_event(integra):
    res = integra.get_event(b'FFFFFF')
    assert 'Integra event' in repr(res)


def test_get_events(integra):
    event_idx = b'FFFFFF'
    for idx in range(10):
        res = integra.get_event(event_idx)
        print(repr(res))
        event_idx = res.event_index


def test_get_name(integra):
    for nmb in range(1, 31):
        try:
            nme = integra.get_name(3, 129 + nmb)
            print(nme)
        except:
            print('Błąd z ', nmb)

    assert 'Name:' in repr(nme)
