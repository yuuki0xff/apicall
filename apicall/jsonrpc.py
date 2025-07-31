import typing
from dataclasses import dataclass
from . import config

import jsonrpcclient  # type: ignore
import jsonrpcclient.client  # type: ignore
import jsonrpcclient.exceptions  # type: ignore
from jsonrpcclient.requests import Request  # type: ignore
from jsonrpcclient.exceptions import ReceivedErrorResponseError, ReceivedNon2xxResponseError as InvalidResponseError  # type: ignore

from . import config
from . import restapi
from .restapi import ConnectionError


@dataclass(frozen=True)
class Endpoint:
    urls: typing.Tuple[str, ...]
    headers: typing.Tuple[config.HttpHeader, ...]
    basic: typing.Optional[config.BasicAuth]

    def send(self, req):
        return JsonRpcClient(self).send(req)


class JsonRpcClient(jsonrpcclient.client.Client):
    def __init__(self, endpoint: Endpoint):
        self.endpoint = endpoint

    def send_message(self, request: str, response_expected: bool, **kwargs) -> jsonrpcclient.Response:
        res = restapi.Request(
            method='POST',
            urls=self.endpoint.urls,
            headers=self.endpoint.headers,
            basic=self.endpoint.basic,
            data=request.encode('utf8'),
        ).fetch()
        return jsonrpcclient.Response(text=res.body, raw=res)
