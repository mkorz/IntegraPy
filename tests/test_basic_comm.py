from . import INTEGRA_HOST, INTEGRA_PORT, INTEGRA_USER_CODE


def test_get_version():
    from ..integra import Integra

    i = Integra(INTEGRA_USER_CODE, INTEGRA_HOST, INTEGRA_PORT)
    assert i.get_version() == 'ETHM1'
