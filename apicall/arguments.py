import sys
import io
import contextlib
import argparse
import typing
import os
import abc
import dataclasses
from . import config
from . import restapi
from . import urlutils
from . import printutils
from .printutils import pprint
from . import jsonrpc
from tabulate import tabulate  # type: ignore

# ExitCodes are compatible with curl command.
ExitCode = typing.NewType('ExitCode', int)
ExitOk = ExitCode(0)
ExitFailedToInit = ExitCode(1)
ExitInvalidArgs = ExitFailedToInit
ExitFailedToConnect = ExitCode(7)
ExitInvalidResponse = ExitCode(22)
ExitErrorReponse = ExitCode(254)
ExitSubprocessError = ExitCode(255)


def parse_headers(
        ns: argparse.Namespace) -> typing.Tuple[config.HttpHeader, ...]:
    """ --header引数をパースして、HttpHeaderオブジェクトのタプルを返す """

    def worker():
        for header in ns.header or []:
            name, value = header.split(':', 2)
            yield config.HttpHeader(name=name.rstrip(), value=value.lstrip())

        if ns.accept is not None:
            yield config.HttpHeader('accept', ns.accept)

        if ns.content_type is not None:
            yield config.HttpHeader('content-type', ns.content_type)

    return tuple(worker())


class CommandArgs(typing.NamedTuple):
    ns: argparse.Namespace
    args: typing.List[str]
    conf: config.Config
    conf_file: str


class TopCommand(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def build(self) -> argparse.ArgumentParser:
        pass

    # @abc.abstractmethod
    def __call__(self, ca: CommandArgs) -> ExitCode:
        print(ca.ns.format_help())
        return ExitInvalidArgs


class SubCommand(metaclass=abc.ABCMeta):
    NAME = 'dummy'

    def add_to(self, sp: argparse._SubParsersAction):
        p = sp.add_parser(self.NAME)
        p.set_defaults(fn=self, format_help=p.format_help)
        self.build_in(p)

    @abc.abstractmethod
    def build_in(self, p: argparse.ArgumentParser):
        pass

    # @abc.abstractmethod
    def __call__(self, ca: CommandArgs) -> ExitCode:
        print(ca.ns.format_help())
        return ExitInvalidArgs


################################################################
# Sub commands
class AuthHeaderSet(SubCommand):
    NAME = 'set'

    def build_in(self, p: argparse.ArgumentParser):
        p.add_argument('name')
        p.add_argument('value')

    def __call__(self, ca: CommandArgs) -> ExitCode:
        new_conf = ca.conf.add_header(
            config.HttpHeader(
                name=ca.ns.name,
                value=ca.ns.value,
            ))
        config.save(ca.conf_file, new_conf)
        return ExitOk


class AuthHeaderUnset(SubCommand):
    NAME = 'unset'

    def build_in(self, p: argparse.ArgumentParser):
        p.add_argument('names', nargs='+')

    def __call__(self, ca: CommandArgs) -> ExitCode:
        new_conf = ca.conf.remove_headers(ca.ns.names)
        config.save(ca.conf_file, new_conf)
        return ExitOk


class AuthHeader(SubCommand):
    NAME = 'header'

    def build_in(self, p: argparse.ArgumentParser):
        sp = p.add_subparsers()
        AuthHeaderSet().add_to(sp)
        AuthHeaderUnset().add_to(sp)

    def __call__(self, ca: CommandArgs) -> ExitCode:
        data = tuple((h.name, h.value) for h in ca.conf.headers)
        tabule = tabulate(data, headers=('NAME', 'VALUE'))
        print(tabule)
        return ExitOk


class AuthBasicSet(SubCommand):
    NAME = 'set'

    def build_in(self, p: argparse.ArgumentParser):
        p.add_argument('user')
        p.add_argument('password')

    def __call__(self, ca: CommandArgs) -> ExitCode:
        new_conf = dataclasses.replace(
            ca.conf,
            basic=config.BasicAuth(
                user=ca.ns.user,
                password=ca.ns.password,
            ))
        config.save(ca.conf_file, new_conf)
        return ExitOk


class AuthBasicUnset(SubCommand):
    NAME = 'unset'

    def build_in(self, p: argparse.ArgumentParser):
        pass

    def __call__(self, ca: CommandArgs) -> ExitCode:
        new_conf = dataclasses.replace(ca.conf, basic=None)
        config.save(ca.conf_file, new_conf)
        return ExitOk


class AuthBasic(SubCommand):
    NAME = 'basic'

    def build_in(self, p: argparse.ArgumentParser):
        sp = p.add_subparsers()
        AuthBasicSet().add_to(sp)
        AuthBasicUnset().add_to(sp)

    def __call__(self, ca: CommandArgs) -> ExitCode:
        basic = ca.conf.basic
        if basic is None:
            print('Basic authentication is not configured.')
            return ExitOk
        else:
            print(f'User: {basic.user}')
            print(f'Password: {basic.password}')
            return ExitOk


class Auth(SubCommand):
    NAME = 'auth'

    def build_in(self, p: argparse.ArgumentParser):
        sp = p.add_subparsers()
        AuthHeader().add_to(sp)
        AuthBasic().add_to(sp)


class Endpoint(SubCommand):
    NAME = 'endpoint'

    def build_in(self, p: argparse.ArgumentParser):
        p.add_argument('urls', nargs='*')

    def __call__(self, ca: CommandArgs) -> ExitCode:
        urls = ca.ns.urls
        if urls:
            new_conf = dataclasses.replace(ca.conf, endpoints=tuple(urls))
            config.save(ca.conf_file, new_conf)
            return ExitOk
        else:
            print('\n'.join(ca.conf.endpoints))
            return ExitOk


class Rest(SubCommand):
    NAME = 'rest'

    def build_in(self, p: argparse.ArgumentParser):
        # Options are compatible with curl command.
        # That is better not to override to curl options.
        p.add_argument('-R', '--raw', action='store_true')
        p.add_argument('-v', '--verbose', action='count', default=0)
        p.add_argument('-H', '--header', action='append')
        p.add_argument('--accept')
        p.add_argument('--content-type', '--type')
        p.add_argument('-d', '--data')
        p.add_argument('method')
        p.add_argument('url')
        p.add_argument('queries', nargs='*')

    def __call__(self, ca: CommandArgs) -> ExitCode:
        # 正しいcontent-type headerをつけていないので、アプリケーション側で正しく処理してくれない。
        try:
            data = self.parse_data(ca.ns.data)
            response = restapi.Request(
                method=ca.ns.method,
                urls=urlutils.concat_urls(
                    endpoints=ca.conf.endpoints,
                    url=ca.ns.url,
                    queries=tuple(ca.ns.queries),
                ),
                headers=(self.detect_data_type(data) + ca.conf.headers +
                         parse_headers(ca.ns)),
                basic=ca.conf.basic,
                data=data,
            ).fetch(
                verbose=ca.ns.verbose,
                logging_cb=lambda msg: print(msg),
            )
        except restapi.ConnectionError:
            pprint(
                'ERROR: Could not connect to server.\n'
                'Please check endpoint urls and HTTP server status.',
                file=sys.stderr)
            return ExitFailedToConnect

        try:
            pprint(response.raw_body)
            return ExitOk
        except printutils.SubprocessError:
            return ExitSubprocessError

    def parse_data(self, data: typing.Optional[str]) -> typing.Optional[bytes]:
        if data is None:
            return None
        elif data.startswith('@'):
            fname = data[1:]
            with open(fname, 'rb') as f:
                return f.read()
        else:
            return bytes(data, 'utf8')

    def detect_data_type(self, data: typing.Optional[bytes]
                         ) -> typing.Tuple[config.HttpHeader, ...]:
        """ --data引数で指定したデータのタイプを判別し、適切なcontent-typeヘッダーを返す  """
        if data is None:
            return tuple()
        if printutils.is_unicode_string(data):
            if printutils.is_json(data):
                return config.HttpHeader('content-type', 'application/json'),
            return config.HttpHeader('content-type', 'text/plain'),
        return config.HttpHeader('content-type', 'application/octet-stream'),


class Jsonrpc(SubCommand):
    NAME = 'jsonrpc'

    def build_in(self, p: argparse.ArgumentParser):
        p.add_argument('--raw', action='store_true')
        p.add_argument('--verbose', action='count', default=0)
        p.add_argument('-H', '--header', action='append')
        p.add_argument('--accept')
        p.add_argument('--content-type', '--type')
        p.add_argument('method')
        p.add_argument('args', nargs='*')

    def __call__(self, ca: CommandArgs) -> ExitCode:
        try:
            res = jsonrpc.Endpoint(
                urls=ca.conf.endpoints,
                headers=ca.conf.headers + parse_headers(ca.ns),
                basic=ca.conf.basic,
            ).send(jsonrpc.Request(
                ca.ns.method,
                ca.ns.args,
            ))
        except jsonrpc.ConnectionError:
            print(
                'ERROR: Could not connect to server.\n'
                'Please check endpoint urls and HTTP server status.',
                file=sys.stderr)
            return ExitFailedToConnect
        except jsonrpc.InvalidResponseError as e:
            pprint(str(e).encode())
            return ExitInvalidResponse
        except jsonrpc.ReceivedErrorResponseError as e:
            pprint(str(e.response).encode())
            return ExitErrorReponse

        try:
            pprint(res.text.encode())
            return ExitOk
        except printutils.SubprocessError:
            return ExitSubprocessError


################################################################
# Top level commands
class ApicallCommand(TopCommand):
    def build(self) -> argparse.ArgumentParser:
        p = argparse.ArgumentParser(prog='apicall')
        p.set_defaults(fn=self, format_help=p.format_help)
        sp = p.add_subparsers()
        Auth().add_to(sp)
        Endpoint().add_to(sp)
        Rest().add_to(sp)
        Jsonrpc().add_to(sp)
        return p


class RestcallCommand(TopCommand):
    def build(self) -> argparse.ArgumentParser:
        p = argparse.ArgumentParser(prog='restcall')

        rest = Rest()
        p.set_defaults(fn=rest, format_help=p.format_help)
        rest.build_in(p)
        return p


class JsonrpccallCommand(TopCommand):
    def build(self) -> argparse.ArgumentParser:
        p = argparse.ArgumentParser(prog='jsonrpccall')

        jr = Jsonrpc()
        p.set_defaults(fn=jr, format_help=p.format_help)
        jr.build_in(p)
        return p


################################################################
# Parser
class ParseResult(typing.NamedTuple):
    success: bool
    ns: typing.Optional[argparse.Namespace]
    output: str


def parse(prog, args) -> ParseResult:
    basename = os.path.basename(prog)

    cmd: TopCommand
    if basename == 'restcall':
        cmd = RestcallCommand()
    elif basename == 'jsonrpccall':
        cmd = JsonrpccallCommand()
    else:
        cmd = ApicallCommand()

    ns: typing.Optional[argparse.Namespace] = None
    output = io.StringIO()
    exit_code = None
    try:
        # Redirect stdout/stderr to on-memory buffer.
        with contextlib.redirect_stdout(output), \
             contextlib.redirect_stderr(output):
            ns = cmd.build().parse_args(args)
            success = True
    except SystemExit:
        success = False

    return ParseResult(
        success=success,
        ns=ns,
        output=output.getvalue(),
    )
