import tempfile
from contextlib import redirect_stdout, redirect_stderr
from apicall.printutils import is_unicode_string, is_json, pprint

UNICODE_STRING = b'\xe6\x97\xa5\xe6\x9c\xac\xe8\xaa\x9e'
NON_UNICODE_DATA = b'\x93\xfa\x96{\x8c\xea'
NON_UNICODE_DATA_HEX= \
    b'0000000 93 fa 96 7b 8c ea\n' \
    b'0000006\n'


def FakeTerminal(mode: str):
    f = tempfile.TemporaryFile(mode)
    # isatty() method is always returns True.
    f.isatty = lambda: True
    return f


class TestIsUnicodeString:
    def test_zero_length(self):
        assert is_unicode_string(b'')

    def test_unicode_string(self):
        assert is_unicode_string(UNICODE_STRING)

    def test_non_unicode_data(self):
        assert not is_unicode_string(NON_UNICODE_DATA)


class TestIsJson:
    def test_valid_string(self):
        assert is_json(b'{}')
        assert is_json(b'{"name": "foo"}')

    def test_invalid_json(self):
        assert not is_json(b'')
        assert not is_json(b'{')
        assert not is_json(b"{'name': 'foo'}")


class TestWriteBinaryData:
    def test_stdout_is_not_terminal(self):
        out = tempfile.TemporaryFile('w+t')
        err = FakeTerminal('w+t')
        with out, err:
            with redirect_stdout(out), redirect_stderr(err):
                pprint(UNICODE_STRING)

            out.seek(0)
            assert out.buffer.read() == UNICODE_STRING
            err.seek(0)
            assert err.read() == ''

    def test_unicode_string(self):
        out = FakeTerminal('w+t')
        err = FakeTerminal('w+t')
        with out, err:
            with redirect_stdout(out), redirect_stderr(err):
                pprint(UNICODE_STRING)

            out.seek(0)
            assert out.buffer.read() == UNICODE_STRING
            err.seek(0)
            assert err.read() == ''

    def test_non_unicode_data(self):
        out = FakeTerminal('w+t')
        err = FakeTerminal('w+t')
        with out, err:
            with redirect_stdout(out), redirect_stderr(err):
                pprint(NON_UNICODE_DATA)

            out.seek(0)
            assert out.buffer.read() == NON_UNICODE_DATA_HEX
            err.seek(0)
            assert err.read().startswith('WARNING: ')
