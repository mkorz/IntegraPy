from binascii import unhexlify


def test_checksum():
    from ..integra import checksum

    assert checksum(b'\x09') == 0xD7EB
    assert checksum(b'\x1C') == 0xD7FE


def test_prepare_frame():
    from ..integra import prepare_frame

    assert prepare_frame('09') == unhexlify('FEFE09D7EBFE0D')
    assert prepare_frame('1C') == unhexlify('FEFE1CD7FEF0FE0D')
