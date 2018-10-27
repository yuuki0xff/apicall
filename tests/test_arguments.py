"""引数のパース処理のテスト

主要なコマンドに対して、想定されるいくつかのパターンの引数を入力し、
想定通りにパースできているかテストする。
"""
import pytest
import apicall.config as config
import apicall.arguments as arg
from . import command_tester as ct

saved_config = None


def fake_config_save(path: str, conf: config.Config):
    global saved_config
    saved_config = conf


@pytest.fixture(scope='function', autouse=True)
def patch_config():
    """ apicall.config.save()を置き換える

    save_config変数の初期化と、save()関数をfake_config_save()に置き換えをする。
    このパッチを当てると、テストケース実行時に、実際のファイルが作られてしまう問題を解消できる。

    この初期化処理は、テスト関数(メソッド)を呼び出す前に行われる。
    """
    global saved_config
    saved_config = None
    config.save = fake_config_save


class TestApicallCommand:
    def test_apicall_without_args(self):
        pc = ct.StartCondition(
            args=['apicall'],
            config=None,
        ).parse()
        assert pc.success
        assert pc.error_message == ''
        assert isinstance(pc.fn, arg.ApicallCommand)

        ec = pc.exec()
        assert ec.out.startswith('usage: apicall ')
        assert ec.err == ''
        assert ec.exit_code == arg.ExitInvalidArgs

    def test_restcall_without_args(self):
        pc = ct.StartCondition(
            args=['restcall'],
            config=None,
        ).parse()
        assert not pc.success
        assert pc.error_message.startswith('usage: restcall ')

    def test_jsonrpccall_without_args(self):
        pc = ct.StartCondition(
            args=['jsonrpccall'],
            config=None,
        ).parse()
        assert not pc.success
        assert pc.error_message.startswith('usage: jsonrpccall ')

    def test_auth_header_set(self):
        pc = ct.StartCondition(
            args=['apicall', 'auth', 'header', 'set', 'NAME', 'VALUE'],
            config=config.Config(),
        ).parse()
        assert pc.success
        assert pc.error_message == ''
        assert isinstance(pc.fn, arg.AuthHeaderSet)

        ec = pc.exec()
        assert ec.out == ''
        assert ec.err == ''
        assert ec.exit_code == arg.ExitOk
        assert saved_config == config.Config(
            headers=(config.HttpHeader('NAME', 'VALUE'), ), )

    def test_auth_header_unset(self):
        pc = ct.StartCondition(
            args=['apicall', 'auth', 'header', 'unset', 'HEADER2', 'HEADER3'],
            config=config.Config(
                headers=(
                    config.HttpHeader('header1', 'value1'),
                    config.HttpHeader('header2', 'value2'),
                    config.HttpHeader('header3', 'value3'),
                    config.HttpHeader('header4', 'value4'),
                ), ),
        ).parse()
        assert pc.success
        assert pc.error_message == ''
        assert isinstance(pc.fn, arg.AuthHeaderUnset)

        ec = pc.exec()
        assert ec.out == ''
        assert ec.err == ''
        assert ec.exit_code == arg.ExitOk
        assert saved_config == config.Config(
            headers=(
                config.HttpHeader('header1', 'value1'),
                config.HttpHeader('header4', 'value4'),
            ), )

    def test_auth_basic_set(self):
        pc = ct.StartCondition(
            args=['apicall', 'auth', 'basic', 'set', 'User', 'P@ssw0rd'],
            config=config.Config(),
        ).parse()
        assert pc.success
        assert pc.error_message == ''
        assert isinstance(pc.fn, arg.AuthBasicSet)

        ec = pc.exec()
        assert ec.out == ''
        assert ec.err == ''
        assert ec.exit_code == arg.ExitOk
        assert saved_config == config.Config(
            basic=config.BasicAuth(
                user='User',
                password='P@ssw0rd',
            ), )

    def test_auth_basic_unset(self):
        pc = ct.StartCondition(
            args=['apicall', 'auth', 'basic', 'unset'],
            config=config.Config(
                basic=config.BasicAuth(
                    user='User',
                    password='P@ssw0rd',
                ), )).parse()
        assert pc.success
        assert pc.error_message == ''
        assert isinstance(pc.fn, arg.AuthBasicUnset)

        ec = pc.exec()
        assert ec.out == ''
        assert ec.err == ''
        assert ec.exit_code == arg.ExitOk
        assert saved_config == config.Config()

    def test_endpoint_show(self):
        pc = ct.StartCondition(
            args=['apicall', 'endpoint'],
            config=config.Config(
                endpoints=('http://localhost:8080', ), )).parse()
        assert pc.success
        assert pc.error_message == ''
        assert isinstance(pc.fn, arg.Endpoint)

        ec = pc.exec()
        assert ec.out == 'http://localhost:8080\n'
        assert ec.err == ''
        # This operation MUST NOT update config file.
        assert saved_config == None

    def test_endpoint_set(self):
        pc = ct.StartCondition(
            args=['apicall', 'endpoint', 'http://localhost:3333'],
            config=config.Config(),
        ).parse()
        assert pc.success
        assert pc.error_message == ''
        assert isinstance(pc.fn, arg.Endpoint)

        ec = pc.exec()
        assert ec.out == ''
        assert ec.err == ''
        # This operation MUST NOT update config file.
        assert saved_config == config.Config(
            endpoints=('http://localhost:3333', ), )
