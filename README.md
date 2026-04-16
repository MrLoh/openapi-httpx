# OpenAPI HTTPX

[![PyPI](https://img.shields.io/pypi/v/openapi-httpx?v=0.1.0)](https://pypi.org/project/openapi-httpx/)
[![Python](https://img.shields.io/pypi/pyversions/openapi-httpx?v=0.1.0)](https://pypi.org/project/openapi-httpx/)
[![License](https://img.shields.io/pypi/l/openapi-httpx)](https://github.com/mrloh/openapi-httpx/blob/main/LICENSE)
[![CI](https://github.com/mrloh/openapi-httpx/actions/workflows/ci.yml/badge.svg)](https://github.com/mrloh/openapi-httpx/actions/workflows/ci.yml)
[![Docs](https://img.shields.io/badge/docs-online-526CFE?logo=materialformkdocs&logoColor=white)](https://mrloh.github.io/openapi-httpx/)

Generate a typed [HTTPX](https://www.python-httpx.org) client from an OpenAPI specification. Provides an extremely thin wrapper around the HTTPX `Client` class that registers `overload`s for each operation and defines `TypedDict`s for parameters, request bodies and response bodies.

## Installation

```bash
pip install openapi-httpx
# or
uv add openapi-httpx
# or
poetry add openapi-httpx
```

The generated client code imports `httpx` at runtime. Make sure to install it in any environment where you run the generated client:

```bash
pip install httpx
```

(or `uv add httpx` / `poetry add httpx`)

## Usage

```bash
openapi-httpx --input <OpenAPI yaml/json/url> --output client.py
```

This produces a client class with overloads for each operation:

```python
class GetUserByIdParams(TypedDict):
    id: str

class User(TypedDict):
    id: str
    name: str
    email: str

class PostFileUploadRequest(TypedDict):
    name: str
    description: str

class OpenApiClient(Client):
    @overload
    def GET(
        self,
        path: Literal["/user/{id}"],
        *,
        params: GetUserByIdParams,
        parse_as: Literal["json"] = "json",
        **kwargs: Unpack[RequestKwargs]
    ) -> User:
        """Get a user by ID"""
        pass

    @overload
    def POST(
        self,
        path: Literal["/user"],
        *,
        params: None = None,
        json: User,
        data: None = None,
        content: None = None,
        files: None = None,
        parse_as: Literal["json"] = "json",
        **kwargs: Unpack[RequestKwargs]
    ) -> User:
        """Create a user"""
        pass

    @overload
    def POST(
        self,
        path: Literal["/file"],
        *,
        params: None = None,
        json: None = None,
        data: PostFileUploadRequest,
        files: dict[Literal["file"], FileTypes] | list[tuple[Literal["file"], FileTypes]],
        content: None = None,
        parse_as: Literal["json"] = "json",
        **kwargs: Unpack[RequestKwargs]
    ) -> None:
        """Upload a file"""
        pass
```

### CLI Options

| Flag                      | Description                                                   |
| ------------------------- | ------------------------------------------------------------- |
| `--input`                 | OpenAPI specification file path or URL (required)             |
| `--output`                | Output file path (required)                                   |
| `--target-python-version` | Target Python version (default: `3.11`)                       |
| `--client-class-name`     | Name of the generated client class (default: `OpenApiClient`) |
| `--async-client`          | Generate an async client based on `httpx.AsyncClient`         |
| `--use-closed-typed-dict` | Generate closed TypedDicts (PEP 728, `closed=True`)           |

### Python API

For more control, use the library directly:

```python
from openapi_httpx import Config, generate

result = generate("path/to/openapi.yaml", Config(
    async_client=True,
    client_class_name="MyApiClient",
))

with open("client.py", "w") as f:
    f.write(result)
```

See the `Config` class for all available options.

### Differences to plain HTTPX

This library is an extremely thin wrapper around the HTTPX Client class. But there are a few notable differences:

- Path parameters are passed to the `params` argument alongside query parameters. You cannot use f-strings to interpolate them, or the type checking will break!
- The methods don't return `[Response](https://www.python-httpx.org/api/#response)`s but instead return the parsed response body. The response is automatically parsed based on the `parse_as` argument which defaults to `'json'`. It can also be set to `'text'` to return a `str` or `None` to return raw `bytes`.
- The library automatically calls `[raise_for_status](https://www.python-httpx.org/quickstart/#response-status-codes)` on the response, which means that any unsuccessful status code will raise an exception. To customize exceptions, you can pass `[event_hooks](https://www.python-httpx.org/advanced/event-hooks/)` at client registration time.

## Prior Art

Inspired by [OpenAPI fetch](https://openapi-ts.dev/openapi-fetch/) for TypeScript.

Built on top of [datamodel-code-generator](https://github.com/koxudaxi/datamodel-code-generator) which handles most of the heavy lifting of parsing the OpenAPI specification.

## Development

See [CONTRIBUTING.md](CONTRIBUTING.md) for development setup and guidelines.
