# Agent Guidelines

Code generator that produces typed HTTPX clients from OpenAPI 3.x specs. Built on [datamodel-code-generator](https://github.com/koxudaxi/datamodel-code-generator) for schema parsing and type generation. The public API is two things: a `Config` Pydantic model + a `generate()` function in `__init__.py`, and an `openapi-httpx` CLI in `__main__.py`.

## Running Commands

All commands from the repo root. Uses **Poetry** with **poe** as task runner — never use pip, venv, or other package managers.

- `poetry install` — install all dependencies (dev group is included by default)
- `poetry test` — run tests
- `poetry typecheck` — type check (pyright, targeting 3.11)
- `poetry lint` / `poetry format` — ruff
- Dependencies: `poetry add <package>`, `poetry lock`, `poetry install`

## Architecture

`__init__.py` exposes `Config` and `generate()`. `generate()` wires up `datamodel-code-generator`'s type system and delegates to `OpenAPIHttpxParser` in `httpx_parser.py`.

The parser extends `datamodel-code-generator`'s `OpenAPIParser`. It overrides `parse_operation()` to collect `HttpxOperationModel` instances (one per path+method), tracking request params, body types, and response types. After the base parser finishes, `render_client()` emits a class extending `httpx.Client` (or `AsyncClient`) with `@overload`-decorated methods for each operation. `parse()` stitches the base output (TypedDicts, type aliases) with the rendered client into a single string.

The generated code must always `compile()` — `test_generated_code_compiles` enforces this.

## Code Style

- Python 3.11+ — use `list`, `dict`, `X | None` (not `List`, `Dict`, `Optional`, `Union`)
- Use relative imports within the package (`from .httpx_parser import ...`) and put all imports at top of file, no inline imports
- Prefer inlining over helper functions — don't extract unless the same logic repeats three or more times
- Don't add indirection (wrapper functions, intermediate variables, opts objects) without a concrete reason
- Google style docstrings. Docstrings are for callers (behavior, args, returns), comments are for maintainers (why, trade-offs). Be sparse with both.
- `datamodel-code-generator` is loosely pinned `<1.0`. The `pydantic` module at `datamodel_code_generator.model.pydantic` was removed in 0.55 in favor of `pydantic_v2`; `httpx_parser.py` imports the new module with a fallback to the old one to support both.

## Testing

- Run `poetry typecheck` and `poetry test` after each significant change
- Tests live in `tests/`, fixtures in `tests/fixtures/` — kept out of the published wheel
- `tests/httpx_parser_test.py` — unit tests for parser internals (operations, params, response types)
- `tests/generate_test.py` — integration tests for `generate()`, CLI, async mode, closed TypedDict, and the petstore fixture
- `tests/fixtures/petstore.json` — realistic multi-endpoint spec used by integration tests and as a CLI fixture
- Plain functions (`def test_...():`), no test classes, no docstrings on tests
- Use When/Then/And comments to structure test cases. Add Given only when there's a non-obvious prerequisite (e.g. a specific fixture property the test depends on).
- Use `tmp_path` for CLI tests that write output files
- Extend existing tests before adding new ones — new test cases are for genuinely distinct scenarios
- Only test logic we own, not library passthrough behavior
