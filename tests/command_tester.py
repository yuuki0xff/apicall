from __future__ import annotations
import io
import tempfile
import typing
import contextlib
import apicall.config as config
import apicall.arguments as arg


class StartCondition(typing.NamedTuple):
    """ コマンドの実行開始時の条件 """
    args: typing.List[str]
    config: typing.Optional[config.Config]

    def parse(self) -> ParsedCondition:
        result = arg.parse(self.args[0], self.args[1:])
        ca = arg.CommandArgs(
            ns=result.ns,
            args=self.args,
            conf=self.config or config.Config(),
            conf_file='fake',
        )
        return ParsedCondition(
            start_cond=self,
            ca=ca,
            result=result,
        )


class ParsedCondition:
    """ 引数のパース完了時点での条件 """
    def __init__(self, start_cond: StartCondition, ca: arg.CommandArgs,
                 result: arg.ParseResult):
        self.start_cond = start_cond
        self.ca = ca
        self.result = result

    def exec(self) -> StopCondition:
        out = tempfile.TemporaryFile('w+t')
        err = tempfile.TemporaryFile('w+t')
        with out, err:
            with contextlib.redirect_stdout(out), \
                contextlib.redirect_stderr(err):
                exit_code = self.fn(self.ca)

            out.seek(0)
            err.seek(0)
            return StopCondition(
                out=out.read(),
                err=err.read(),
                exit_code=exit_code,
            )

    def __getattr__(self, item):
        try:
            return super().__getattr__(item)
        except AttributeError:
            return getattr(self.start_cond, item)

    @property
    def success(self):
        return self.result.success

    @property
    def error_message(self):
        return self.result.output

    @property
    def fn(self):
        return self.ns.fn

    @property
    def ns(self):
        return self.ca.ns


class StopCondition(typing.NamedTuple):
    """ コマンドの実行終了後の条件 """
    out: str
    err: str
    exit_code: arg.ExitCode
