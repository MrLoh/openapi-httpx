# Reference

## CLI

```bash
openapi-httpx --input <OpenAPI yaml/json/url> --output client.py
```

| Flag                      | Description                                                   |
| ------------------------- | ------------------------------------------------------------- |
| `--input`                 | OpenAPI specification file path or URL (required)             |
| `--output`                | Output file path (required)                                   |
| `--target-python-version` | Target Python version (default: `3.11`)                       |
| `--client-class-name`     | Name of the generated client class (default: `OpenApiClient`) |
| `--async-client`          | Generate an async client based on `httpx.AsyncClient`         |
| `--use-closed-typed-dict` | Generate closed TypedDicts (PEP 728, `closed=True`)           |

## Python API

For programmatic use — e.g. generating clients in a build script or custom plugin — call `generate()` with a `Config`:

```python
from openapi_httpx import Config, generate

source = generate(
    "path/to/openapi.yaml",
    Config(async_client=True, client_class_name="MyApiClient"),
)

with open("client.py", "w") as f:
    f.write(source)
```

`generate()` accepts a file path, URL, or parsed URL as its source, and returns the generated source as a string.

### Config

The `Config` model exposes a subset of [`datamodel-code-generator`](https://koxudaxi.github.io/datamodel-code-generator/#all-command-options)'s options plus a few specific to this library.

| Field                     | Default         | Description                                                                              |
| ------------------------- | --------------- | ---------------------------------------------------------------------------------------- |
| `target_python_version`   | `3.11`          | Python version to generate code for                                                      |
| `client_class_name`       | `OpenApiClient` | Name of the HTTPX client class                                                           |
| `async_client`            | `False`         | Generate on top of `httpx.AsyncClient` instead of `httpx.Client`                         |
| `additional_imports`      | `None`          | Extra imports to add to the generated code                                               |
| `use_union_operator`      | `True`          | Use `X \| Y` instead of `Union[X, Y]`                                                    |
| `use_standard_collections`| `True`          | Use `list` / `dict` instead of `List` / `Dict`                                           |
| `use_field_description`   | `True`          | Populate docstrings from OpenAPI `description` fields                                    |
| `collapse_root_models`    | `False`         | Inline nested root models into their parent (can lead to duplication)                    |
| `collapse_response_models`| `True`          | Skip type aliases for simple response types like `list[Model]`                           |
| `use_closed_typed_dict`   | `False`         | Emit `TypedDict`s with [PEP 728](https://peps.python.org/pep-0728/) `closed=True`        |
