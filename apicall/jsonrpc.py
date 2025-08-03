import typing
import json
from dataclasses import dataclass

import jsonrpcclient

from . import config
from . import restapi


class Request(typing.NamedTuple):
    """
    The Request class represents a JSON-RPC v2 request.

    This class is intended to encapsulate data for requests in a structured
    format. It includes a method and optional parameters, which can be used
    to describe the details of a request in various scenarios such as API
    calls or internal command handling.

    :ivar method: Method name for JSON-RPC request.
    :ivar params: Optional parameters for method.
    """
    method: str
    params: typing.Any = None

    def to_json(self):
        return jsonrpcclient.request(self.method, params=self.params)


class ErrorResponse(Exception):
    """
    Represents an error response in the context of an RPC or API request.

    This class is used to encapsulate the details of an error response, providing
    access to both the raw JSON data representing the error and the structured error
    object.

    :ivar json: The raw JSON response representing the error.
    :ivar response: The structured error response object.
    """
    def __init__(self, res_json: typing.Any, res: jsonrpcclient.Error):
        self.json = res_json
        self.response = res


@dataclass(frozen=True)
class Endpoint:
    urls: typing.Tuple[str, ...]
    headers: typing.Tuple[config.HttpHeader, ...]
    basic: typing.Optional[config.BasicAuth]

    def send(self, req: Request)->str:
        req_rpc = req.to_json()
        res_raw = restapi.Request(
            method='POST',
            urls=self.urls,
            headers=self.headers,
            basic=self.basic,
            data=json.dumps(req_rpc).encode('utf8'),
        ).fetch()
        res_rpc = jsonrpcclient.responses.parse(res_raw.json)
        Endpoint._check_response(res_raw.json, res_rpc)
        return res_raw.body

    @staticmethod
    def _check_response(res_json: typing.Any, res_rpc: typing.Any):
        if isinstance(res_rpc, jsonrpcclient.Ok):
            return
        if isinstance(res_rpc, jsonrpcclient.Error):
            raise ErrorResponse(res_json, res_rpc)
        else:
            for r in res_rpc:
                Endpoint._check_response(res_json, r)
