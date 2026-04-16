# OpenAPI HTTPX

Generate a typed [HTTPX](https://www.python-httpx.org) client from an OpenAPI specification.

`openapi-httpx` is a thin wrapper around the HTTPX [`Client`](https://www.python-httpx.org/advanced/clients/) class. For each operation in your OpenAPI spec it emits an `@overload` on the client and `TypedDict`s for the parameters, request body, and response — so your editor and type checker know exactly which paths, params, and payloads are valid.

!!! info "Prior art"

    Inspired by [`openapi-fetch`](https://openapi-ts.dev/openapi-fetch/) for TypeScript.

    Built on [`datamodel-code-generator`](https://github.com/koxudaxi/datamodel-code-generator), which does the heavy lifting of parsing the spec and emitting types. `openapi-httpx` extends it with an `httpx.Client` subclass and per-operation `@overload`s.

## Install

=== "pip"

    ```bash
    pip install openapi-httpx
    ```

=== "uv"

    ```bash
    uv add openapi-httpx
    ```

=== "Poetry"

    ```bash
    poetry add openapi-httpx
    ```

??? note "`httpx` is a runtime dependency"

    The generated client imports `httpx` when you run it, but `openapi-httpx` doesn't pull it in for you (it's only needed at generation time on the dev side). Make sure any environment that runs the client has `httpx` installed: `pip install httpx` (or `uv add httpx` / `poetry add httpx`).

## Quick start

Start with an OpenAPI spec:

```yaml title="demo.yaml"
openapi: 3.1.0
info: { title: Demo, version: 0.1.0 }
paths:
  /users/{id}:
    get:
      operationId: getUserById
      parameters:
        - { name: id, in: path, required: true, schema: { type: string } }
      responses:
        "200":
          description: OK
          content:
            application/json:
              schema:
                type: object
                required: [id, name]
                properties:
                  id: { type: string }
                  name: { type: string }
```

Generate a client:

```bash
openapi-httpx --input demo.yaml --output demo_client.py
```

Use it like `httpx.Client`, but with full type inference on every call:

```python
from demo_client import OpenApiClient

with OpenApiClient(base_url="https://api.example.com") as client:
    user = client.GET("/users/{id}", params={"id": "abc"})
    print(user["name"])  # str
```

That's it. The client is a regular `httpx.Client`, so everything you already know about HTTPX (timeouts, auth, event hooks, retries, custom transports) still applies.

## Where to next

- **[Using the client](client.md)** — how the generated methods differ from plain HTTPX: path params, request bodies, response parsing, errors, async.
- **[Reference](reference.md)** — every CLI flag and the Python API for programmatic use.
