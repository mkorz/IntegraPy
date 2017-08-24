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
