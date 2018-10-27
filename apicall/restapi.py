import typing
from dataclasses import dataclass
from . import config
import requests

SHOW_HEADERS = 1


class ConnectionError(Exception):
    pass


@dataclass(frozen=True)
class Request:
    method: str
    urls: typing.Tuple[str, ...]
    headers: typing.Tuple[config.HttpHeader, ...]
    basic: typing.Optional[config.BasicAuth]
    data: typing.Optional[bytes]

    @property
    def dict_headers(self):
        return {h.name: h.value for h in self.headers}

    def fetch(
            self,
            verbose: int = 0,
            logging_cb: typing.Optional[typing.Callable[[str], None]] = None):
        for url in self.urls:
            try:
                res = requests.request(
                    self.method,
                    url,
                    headers=self.dict_headers,
                    data=self.data,
                )

                self.logging_request(verbose, logging_cb, res)

                # The request is successful.  Return the response object.
                return Response(
                    request=self,
                    _result=res,
                )
            except requests.ConnectionError:
                # Maybe... hostname or port is incorrect.
                # Try to other urls.
                continue

        # Tried all urls, but I could not connect them all.
        raise ConnectionError()

    def logging_request(self, verbose: int,
                        cb: typing.Optional[typing.Callable[[str], None]],
                        res: requests.Response):
        if cb is None:
            return
        if verbose < SHOW_HEADERS:
            return

        first = True
        for r in res.history + [res]:  # type: requests.Response
            if not first:
                cb('')
            first = False

            cb(f'> {r.request.method} {r.request.url}')
            for header, value in r.request.headers.items():
                cb(f'> {header}: {value}')
            cb('')
            cb(f'< {r.status_code} {r.reason}')
            for header, value in r.headers.items():
                cb(f'< {header}: {value}')


@dataclass(frozen=True)
class Response:
    request: Request
    _result: requests.Response

    @property
    def body(self) -> str:
        return self._result.text

    @property
    def raw_body(self) -> bytes:
        return self._result.content

    @property
    def turnaround_time(self):
        return self._result.elapsed

    @property
    def content_type(self) -> typing.Optional[str]:
        if 'content-type' not in self._result.headers:
            return None

        h = self._result.headers['content-type']
        if ';' in h:
            # Strip MIME directives.
            h, _ = h.split(';', 1)
        return h
