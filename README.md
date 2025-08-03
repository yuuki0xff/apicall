# apicall - User-friendly RESTful API & JSON-RPC Client

Apicall is a useful API client. It will realize easy to calling API compared to the curl command in 90% of use case.


## Features
- **URL prefix omission**:  
  You can omit some URL components like schema, hostname, part of path.
- **Git integration**:  
  The apicall locates a configuration file on the git root directory. So settings will change for each git repositories.
- **Formatted and colored JSON response**:  
  All JSON response is formatted and colored by the jq command by default. You can reduce of work of reading minified
  JSON.
- **Useful query string builder**:  
  Remaining positional arguments of the `restcall` command regard as key-value pairs of query string parameters. Keys
  and values applies URL escape. So you don't need to assemble of URL-encoded query string. See the usage section and
  the tutorial section for detail.
- **Default authentication headers**:  
  The apicall sets authentication headers on all requests if header setting exists. You can easily call APIs that
  require an authentication token.
- **Automatic endpoint discovery**:  
  If the endpoint is not specified, the apicall discovers famous HTTP ports in the localhost and tries to request.
- **Binary safe**:  
  The apicall converts response in hex representation when writing binary response into a terminal.


## Usage
```bash
$ apicall endpoint https://example.com/rest-api/v1
$ restcall post /users -d '{"name": "bob"}'
$ restcall get /users/10
$ restcall get /users/search 'name=bob'
$ restcall delete /users/10
$ restcall get https://example.com/api

$ apicall endpoint https://example.com/json-rpc/v1
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
$ python3 -m pip install apicall                                    # Install stable version from pypi.
   or
$ python3 -m pip install git+https://github.com/yuuki0xff/apicall   # Install latest version from github.

$ sudo apt install jq   # Debian, Ubuntu
$ brew install jq       # Mac
```


## Tutorial
The `apicall` provides all features in a command. Also, some alias commands exist. The original command name is too
long. We recommend that you use alias commands.

```
restcall      # The alias command of `apicall rest`.
jsonrpccall   # The alias command of `apicall jsonrpc`.
```

Before calling API, you should check the setting of the apicall. Most important is endpoint setting. It displays and
changes by `apicall endpoint` command. When multiple endpoints are specified, the apicall tries sending a request to
the first destination. If connection error occurred, it tries sending a request to the second destination. The
default endpoint setting is localhost addresses with some famous HTTP ports like http://localhost:8080,
http://localhost:3000, and so on. So if you need to send requests to the local development server, you can use it
without setting changes. 

```bash
# Show endpoints.
apicall endpoint
# Set endpoint.
apicall endpoint http://localhost:8080/api/v1
```

The apicall setting is complete. Let send requests to the server.

```bash
# Send a GET request to http://localhost:8080/api/v1/users.
# Command syntax: restcall METHOD URL [QUERY_STRING ...]
restcall get /users
# Same as above.
restcall get users

# With query string.
# http://localhost:8080/users?name=alice&age=%3E20
restcall get /users name=alice 'age=>20'

# With complex query string.
# http://localhost:8080/items?q=bulk%20%22apple%20juice%22
restcall get /items 'q=bulk "apple juice"'
# Of course, you can send a request without using the query string builder.
restcall get '/items?q=bulk+%22apple+juice%22'
# You can also use both the hand-assembled query string and the query string builder.
# http://localhost:8080/items?q=bulk+%22apple+juice%22&sort=price&order=asc
restcall get '/items?q=bulk+%22apple+juice%22' sort=price order=asc

# Send a DELETE request.
restcall delete /items/25

# Send a POST request. The content type is automatically detected and implicitly added to request headers. You can
# override this value by the --type option.
restcall post /user/alice -d '{"age":28, "email": "alice@example.com"}'
restcall post /user/alice/message -d 'Hello!'
restcall post /user/alice/icon -d @./Pictures/my-icon.jpg --type image/jpeg

# When the server sends a binary response... Don't worry! The apicall converts response in hex representation.
restcall get https://github.com/favicon.ico
# If stdout is not terminal, the apicall doesn't convert response. So you can save original binary data to the file.
restcall get https://github.com/favicon.ico >favicon.ico

# If the -v option specified, you can see request/response headers.
restcall get /users -v
```


## Quick reference
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
$ python3 -m pip install -e '.[dev]'
```

## TODO
* Improve help messages and documentation.
* Support gRPC protocol.
