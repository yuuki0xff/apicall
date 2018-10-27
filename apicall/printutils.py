import sys
import tempfile
import subprocess
import typing
import json
import contextlib


class SubprocessError(Exception):
    pass


def _run(args, stdin):
    """ Run the process.

    contextlibでstdout/stderrをリダイレクトしている状況下で
    サブプロセスを起動した場合、サブプロセスの出力はリダイレクト前の
    fdに出力される。
    この関数は、この問題へのワークアラウンドを提供する。 """
    return subprocess.run(
        args, stdin=stdin, stdout=sys.stdout, stderr=sys.stderr)


def is_unicode_string(data: bytes) -> bool:
    try:
        data.decode()
        return True
    except UnicodeDecodeError:
        return False


def is_json(data: bytes) -> bool:
    try:
        json.loads(data.decode())
        return True
    except json.JSONDecodeError:
        return False


def print_hex(data: bytes):
    with tempfile.TemporaryFile() as f:
        f.write(data)
        f.seek(0)
        result = _run(['od', '-t', 'x1'], stdin=f)
        if result.returncode != 0:
            raise SubprocessError()


def print_json(data: bytes):
    """ Print JSON to terminal through jq command. """
    with tempfile.TemporaryFile() as f:
        f.write(data)
        f.seek(0)
        result = _run(['jq'], stdin=f)
        if result.returncode != 0:
            raise SubprocessError()


def pprint(data: typing.Union[bytes, str], raw: bool = False, file=None):
    # convert data to bytes.
    if isinstance(data, str):
        data = data.encode()

    context = contextlib.nullcontext()  # type: ignore
    if file is not None:
        context = contextlib.redirect_stdout(file)

    with context:
        if raw or not sys.stdout.isatty():
            sys.stdout.buffer.write(data)
            return

        if is_unicode_string(data):
            if is_json(data):
                print_json(data)
                return
            sys.stdout.buffer.write(data)
            return

        # Attempt to write binary data to terminal !
        # Show warning messages and writes data in hex representation.
        sys.stderr.write(
            'WARNING: The response body is displayed in hex representation\n'
            '         because it is binary data.\n')
        print_hex(data)
