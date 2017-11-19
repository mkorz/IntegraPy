# -*- coding: UTF-8 -*-
import pytest
from . import INTEGRA_HOST, INTEGRA_PORT, INTEGRA_USER_CODE


@pytest.fixture
def integra():
    from IntegraPy import Integra

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
        event_idx = res.event_index


def test_get_name(integra):
    nme = integra.get_name(2, 1)
    assert 'Name:' in repr(nme)


def test_get_violated_zones(integra):
    viol = integra.get_violated_zones()
    assert len(viol) > 0


def test_get_active_outputs(integra):
    outputs = integra.get_active_outputs()
    assert type(outputs) == set


def test_get_armed_partitions(integra):
    parts = integra.get_armed_partitions()
    assert type(parts) == set
