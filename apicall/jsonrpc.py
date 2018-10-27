import typing
from dataclasses import dataclass
from . import config
import requests
import jsonrpcclient  # type: ignore
import jsonrpcclient.exceptions  # type: ignore
from jsonrpcclient.requests import Request  # type: ignore
from jsonrpcclient.exceptions import ReceivedErrorResponseError, ReceivedNon2xxResponseError as InvalidResponseError  # type: ignore


class ConnectionError(Exception):
    pass


@dataclass(frozen=True)
class Endpoint:
    urls: typing.Tuple[str, ...]
    headers: typing.Tuple[config.HttpHeader, ...]
    basic: typing.Optional[config.BasicAuth]

    def send(self, req):
        for url in self.urls:
            try:
                return jsonrpcclient.send(url, req)
            except requests.ConnectionError:
                # Maybe... hostname or port is incorrect.
                # Try to other urls.
                continue
        raise ConnectionError()
