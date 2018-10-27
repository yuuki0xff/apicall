from __future__ import annotations
import os
import typing
import dataclasses
from dataclasses import dataclass
from dataclasses_json import dataclass_json  # type: ignore

CONFIG_FILE_LOCATIONS = (
    './.apicall.json',
    '$GIT/.apicall.json',
    '~/.apicall.json',
    '~/.config/apicall.json',
)

# List of default ports.
#  * django: 8000/tcp
#  * bottle: 8080/tcp
#  * rails:  3000/tcp
#  * rack:   9292/tcp
DEFAULT_ENDPOINTS = (
    'http://localhost:8000',
    'http://localhost:8080',
    'http://localhost:3000',
    'http://localhost:9292',
)


class ConfigNotFound(Exception):
    pass


class GitRepositoryNotFound(Exception):
    pass


@dataclass_json
@dataclass(frozen=True)
class HttpHeader:
    name: str
    value: str


@dataclass_json
@dataclass(frozen=True)
class BasicAuth:
    user: str
    password: str


@dataclass_json
@dataclass(frozen=True)
class Config:
    headers: typing.Tuple[HttpHeader, ...] = dataclasses.field(default=tuple())
    basic: typing.Optional[BasicAuth] = dataclasses.field(default=None)
    endpoints: typing.Tuple[str, ...] = dataclasses.field(
        default=DEFAULT_ENDPOINTS)

    def remove_headers(self, names: typing.Iterable[str]) -> Config:
        """ Remove http headers with names.

        NOTE: I recommended to see documentation of add_header().
        """
        names = set(name.lower() for name in names)
        cleaned_headers = tuple(
            filter(lambda h: h.name.lower() not in names, self.headers))
        return dataclasses.replace(self, headers=cleaned_headers)

    def add_header(self, header: HttpHeader) -> Config:
        """ Add a http header.

        Add a http header.  If config already contains the header with the same name, that
        headers will be removed.

        NOTE:
        HTTP 1.1 specification allows same name headers.  But I think duplicate http headers
        are BAD PRACTICE because it can causes issues with some apps.  So I decide that
        duplicate HTTP headers feature does not support.
        https://stackoverflow.com/questions/3241326/set-more-than-one-http-header-with-the-same-name
        """
        cleaned = self.remove_headers([header.name])
        return dataclasses.replace(
            cleaned, headers=cleaned.headers + (header, ))


class FileSearcher:
    def __init__(self,
                 locations: typing.Iterable = CONFIG_FILE_LOCATIONS,
                 base_dir='.'):
        self.locations = locations
        self.base_dir = base_dir

    def find_git_root(self, base: str) -> str:
        p = os.path.abspath(base)
        while True:
            git_dir = os.path.join(p, '.git')
            if os.path.exists(git_dir):
                return p

            parent = os.path.dirname(p)
            if parent == p:
                # p is the root directory.
                break
            p = parent
        raise GitRepositoryNotFound()

    def expand_path(self, path: str) -> str:
        return os.path.abspath(os.path.expanduser(path))

    def search(self) -> str:
        base = os.path.abspath(self.base_dir)

        for pattern in self.locations:
            # Expands file path pattern.
            if pattern.startswith('$GIT/'):
                try:
                    git_root = self.find_git_root(base)
                    filepath = pattern.replace('$GIT/', git_root)
                except GitRepositoryNotFound:
                    continue
            else:
                filepath = self.expand_path(pattern)

            abspath = os.path.join(base, filepath)
            if os.path.exists(abspath):
                return abspath

        # All path patterns are checked.  But file is not found...
        raise ConfigNotFound()

    def default_location(self) -> str:
        base = os.path.abspath(self.base_dir)

        # 1. Git repository root.
        try:
            git_root = self.find_git_root(base)
            return os.path.join(git_root, '.apicall.json')
        except GitRepositoryNotFound:
            pass

        # 2. Home directory.
        return os.path.expanduser('~/.apicall.json')


def default() -> typing.Tuple[str, Config]:
    fname = FileSearcher().default_location()
    obj = Config()
    return fname, obj


def load() -> typing.Tuple[str, Config]:
    fname = FileSearcher().search()
    with open(fname) as f:
        js = f.read()

    # Workaround for an issue that data type of Config.headers[*] is wrong.
    # Expected type is HttpHeader object, but actual type is dict object.
    # This workaround converts the data type from dict to HttpHeader.
    #
    # The cause of this problem is bug of dataclasses_json library...
    # TODO: Bug report to dataclasses_json.
    conf = Config.from_json(js)  # type: ignore
    fixed_conf = dataclasses.replace(
        conf, headers=tuple(HttpHeader(**h) for h in conf.headers))

    return fname, fixed_conf


def load_or_default() -> typing.Tuple[str, Config]:
    try:
        return load()
    except ConfigNotFound:
        return default()


def save(path: str, conf: Config):
    js = conf.to_json()  # type: ignore
    with open(path, 'w') as f:
        f.write(js)
