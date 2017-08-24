from . import INTEGRA_HOST, INTEGRA_PORT, INTEGRA_USER_CODE


def test_get_version():
    from ..integra import Integra

    i = Integra(INTEGRA_USER_CODE, INTEGRA_HOST, INTEGRA_PORT)
    res = i.get_version()
    assert 'INTEGRA' in res['model']
    assert '20' in res['version']
