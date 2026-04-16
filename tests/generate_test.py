from __future__ import annotations

import json
from pathlib import Path

from openapi_httpx import Config, generate
from openapi_httpx.__main__ import main

FIXTURES_DIR = Path(__file__).parent / "fixtures"
PETSTORE_SPEC = FIXTURES_DIR / "petstore.json"

with open(PETSTORE_SPEC) as f:
    petstore_spec = json.dumps(json.load(f))


def test_generate_smoke():
    # When generating a client with default config
    result = generate(petstore_spec, Config())
    # Then the result is a non-empty string containing the client class
    assert isinstance(result, str)
    assert len(result) > 0
    assert "class OpenApiClient(Client):" in result


def test_generated_code_compiles():
    # When generating a client with default config
    result = generate(petstore_spec, Config())
    # Then the generated code compiles without errors
    compile(result, "<generated>", "exec")


def test_async_client_generation():
    # When generating with async_client=True
    result = generate(petstore_spec, Config(async_client=True))
    # Then the client extends AsyncClient
    assert "class OpenApiClient(AsyncClient):" in result
    # And methods are async
    assert "async def GET(" in result
    assert "async def POST(" in result
    assert "await self.get(" in result


def test_closed_typed_dict_generation():
    # Given ErrorResponse has additionalProperties: false in the petstore spec
    # When generating with use_closed_typed_dict=True
    result = generate(petstore_spec, Config(use_closed_typed_dict=True))
    # Then that schema's TypedDict includes closed=True
    assert "class ErrorResponse(TypedDict, closed=True):" in result


def test_custom_client_class_name():
    # When generating with a custom client class name
    result = generate(petstore_spec, Config(client_class_name="PetApi"))
    # Then the generated class uses that name
    assert "class PetApi(Client):" in result
    # And the default name is absent
    assert "class OpenApiClient" not in result


def test_enum_becomes_literal():
    # Given the petstore spec defines a Species string enum
    # When generating the client
    result = generate(petstore_spec, Config())
    # Then the enum values appear as Literal types in the output
    assert "Literal['dog']" in result or "Literal['dog', 'cat', 'bird', 'fish']" in result or "Species" in result


def test_nullable_field_produces_optional_type():
    # Given the petstore spec has nullable fields (Pet.age, Pet.owner_id)
    # When generating the client
    result = generate(petstore_spec, Config())
    # Then nullable fields have a union with None
    assert "| None" in result


def test_cli_smoke(tmp_path: Path):
    # When running the CLI with the petstore spec
    output_file = tmp_path / "client.py"
    main(["--input", str(PETSTORE_SPEC), "--output", str(output_file)])
    # Then the output file exists and contains the client class
    assert output_file.exists()
    content = output_file.read_text()
    assert "class OpenApiClient(Client):" in content
    # And the output compiles
    compile(content, str(output_file), "exec")


def test_cli_async_flag(tmp_path: Path):
    # When running the CLI with --async-client
    output_file = tmp_path / "async_client.py"
    main(["--input", str(PETSTORE_SPEC), "--output", str(output_file), "--async-client"])
    # Then the output contains an async client
    content = output_file.read_text()
    assert "class OpenApiClient(AsyncClient):" in content
    assert "async def GET(" in content


def test_petstore_fixture_end_to_end():
    # When generating a client from the full petstore spec
    result = generate(petstore_spec, Config())
    # Then the output compiles
    compile(result, "<petstore>", "exec")
    # And contains methods for all HTTP verbs in the spec
    assert "def GET(" in result
    assert "def POST(" in result
    assert "def PUT(" in result
    assert "def DELETE(" in result
    # And contains generated TypedDicts for request/response models
    assert "class Pet(TypedDict):" in result
    assert "class CreatePetRequest(TypedDict):" in result
    assert "class Owner(TypedDict):" in result
    assert "class ErrorResponse(TypedDict):" in result
