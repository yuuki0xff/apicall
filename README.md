# apicall - User-friendly RESTful API & JSON-RPC Client


## Usage
```bash
$ apicall endpoint https://example.com/rest-api/v1
$ restcall post /users -d '{"name": "bob"}'
$ restcall get /users/10
$ restcall get /users/search 'name=bob'
$ restcall delete /users/10

$ apicall endpoint https://example.cmo/json-rpc/v1
$ jsonrpccall create_account 'bob'
$ jsonrpccall get_account 10
$ jsonrpccall search_accounts_by_name 'bob'
$ jsonrpccall delete_account 10
```


## Requirements
* Python 3.7 or later
* [jq command](https://stedolan.github.io/jq/)
* [yapf command](https://github.com/google/yapf) (For development)
* [mypy command](http://mypy-lang.org/) (For development)
* [py.test](https://docs.pytest.org/en/latest/) (For development)


## Installation
_NOTE: If you want develop the apicall, see the "Development" section._

Please run the following command.

```bash
$ python3.7 -m pip install git+https://github.com/yuuki0xff/apicall
```


## Arguments
```
apicall auth header
apicall auth header set NAME VALUE
apicall auth header unset NAME ...
apicall auth basic
apicall auth basic set USER PASSWORD
apicall auth basic unset
apicall endpoint [URLS ...]

restcall METHOD URL [QUERIES ...]
jsonrpccall FUNC [ARGS ...]
```


## Development
Please run the following commands.
When install succeed, apicall commands are installed to your computer.
If you edited some codes under the git repository, changes are applied immediately to the behavior of apicall command.

```bash
$ git clone https://github.com/yuuki0xff/apicall
$ cd apicall
$ python3.7 -m pip install -e '.[dev]'
```

## TODO
* Improve help messages and documentation.
* Support gRPC protocol.
