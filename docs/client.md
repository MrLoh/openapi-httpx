# Using the client

The generator emits a subclass of `httpx.Client` (or `httpx.AsyncClient`). For each operation in your spec, the class gets one `@overload` method keyed on the HTTP verb and path literal, with `TypedDict`s for inputs and a typed return for the parsed body.

In practice, that means you call `client.GET("/path/{id}", ...)`, `client.POST("/path", ...)`, and so on — and your type checker knows the exact shape of every argument and result.

## Path and query parameters

Path parameters go in the `params` dict, alongside query parameters:

```python
client.GET("/users/{id}", params={"id": "abc", "include": "profile"})
```

Behind the scenes, the client splits them: keys that match `{placeholders}` in the path are interpolated into the URL, and the rest become query string params. If a required placeholder is missing, you'll get a `ValueError` at call time and a type error at edit time.

!!! warning "Don't use f-strings"

    `client.GET(f"/users/{user_id}")` will break type inference — the path is no longer a literal, so the overload can't resolve. Always pass path params through `params={}`.

## Request bodies

Request bodies follow HTTPX's convention: one of `json`, `data`, `content`, or `files`, depending on the content type declared in the spec.

| Content type                        | Argument                                |
| ----------------------------------- | --------------------------------------- |
| `application/json`                  | `json=` (typed as a `TypedDict`)        |
| `application/x-www-form-urlencoded` | `data=`                                 |
| `multipart/form-data`               | `data=` for fields, `files=` for uploads |
| Anything else                       | `content=` (raw bytes)                  |

The overload for each operation sets the correct argument as required and the others as `None`, so the type checker will tell you if you mix them up.

## Response parsing

Unlike plain HTTPX, methods don't return a [`Response`](https://www.python-httpx.org/api/#response) — they return the parsed body. `parse_as` controls the parsing, and defaults based on the response content type declared in the spec:

| `parse_as` | Returns                  |
| ---------- | ------------------------ |
| `"json"`   | the parsed JSON, typed   |
| `"text"`   | `str` (the raw response) |
| `None`     | `bytes`                  |

A `204 No Content` response always returns `None` regardless of `parse_as`.

## Error handling

The client calls [`raise_for_status()`](https://www.python-httpx.org/quickstart/#response-status-codes) on every response, so any 4xx/5xx raises `httpx.HTTPStatusError`. To customize error handling — e.g. map specific status codes to domain-specific exceptions — pass [`event_hooks`](https://www.python-httpx.org/advanced/event-hooks/) when you construct the client:

```python
def on_response(response):
    if response.status_code == 429:
        raise RateLimited(response.headers.get("Retry-After"))

client = OpenApiClient(
    base_url="https://api.example.com",
    event_hooks={"response": [on_response]},
)
```

## Additional request kwargs

Every operation accepts the standard HTTPX per-request options via `**kwargs`:

```python
client.GET(
    "/users/{id}",
    params={"id": "abc"},
    headers={"X-Request-Id": "..."},
    timeout=5.0,
)
```

The accepted keys are `headers`, `cookies`, `auth`, `follow_redirects`, `timeout`, and `extensions` — identical to `httpx.Client.request()`.

## Async clients

Generate an async client with `--async-client`. The shape is identical, but the client subclasses `httpx.AsyncClient` and every method is a coroutine:

```python
from demo_client import OpenApiClient

async with OpenApiClient(base_url="https://api.example.com") as client:
    user = await client.GET("/users/{id}", params={"id": "abc"})
```

## Example: what the generated code looks like

Given a spec with three operations — a `GET /user/{id}`, a JSON `POST /user`, and a multipart `POST /file` — the generator produces something like this:

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
        **kwargs: Unpack[RequestKwargs],
    ) -> User:
        """Get a user by ID"""
        ...

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
        **kwargs: Unpack[RequestKwargs],
    ) -> User:
        """Create a user"""
        ...

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
        **kwargs: Unpack[RequestKwargs],
    ) -> None:
        """Upload a file"""
        ...
```

Each overload is keyed on the `(method, path)` literal pair. When you call `client.POST("/user", json={...})`, the type checker picks the matching overload, types `json` as `User`, and infers the return type — while rejecting anything that doesn't match.
