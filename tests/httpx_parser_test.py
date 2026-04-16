from __future__ import annotations

import json

from datamodel_code_generator import DataModelType, LiteralType, PythonVersion
from datamodel_code_generator.model import get_data_model_types

from openapi_httpx.httpx_parser import OpenAPIHttpxParser

spec = {
    "components": {
        "schemas": {
            "DatasourceMetadata": {
                "properties": {
                    "id": {"type": "string", "format": "uuid4", "title": "Id"},
                    "org_id": {"type": "string", "format": "uuid4", "title": "Org Id"},
                    "name": {"type": "string", "pattern": "^[a-zA-Z0-9_\\-]+$", "title": "Name"},
                    "length": {"type": "integer", "minimum": 0.0, "title": "Length"},
                    "created_at": {"type": "string", "format": "date-time", "title": "Created At"},
                },
                "type": "object",
                "required": ["id", "org_id", "name", "created_at"],
                "title": "DatasourceMetadata",
            },
            "Body_post_datasource": {
                "properties": {
                    "files": {"items": {"type": "string", "format": "binary"}, "type": "array", "title": "Files"},
                    "name": {"type": "string", "pattern": "^[a-zA-Z0-9_\\-]+$", "title": "Name"},
                },
                "type": "object",
                "required": ["files", "name"],
                "title": "Body_create_datasource_from_files_datasource_upload_post",
            },
            "InputError": {
                "properties": {"message": {"type": "string", "title": "Message"}},
                "type": "object",
                "required": ["message"],
                "title": "InputError",
            },
        }
    },
    "paths": {
        "/datasource/": {
            "get": {
                "tags": ["datasource"],
                "summary": "List Datasources",
                "description": "List all datasources for the organization.",
                "operationId": "list_datasources_datasource__get",
                "responses": {
                    "200": {
                        "description": "Successful Response",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "items": {"$ref": "#/components/schemas/DatasourceMetadata"},
                                    "type": "array",
                                    "title": "Response List Datasources Datasource  Get",
                                }
                            }
                        },
                    },
                    "400": {
                        "description": "Invalid Input",
                        "content": {"application/json": {"schema": {"$ref": "#/components/schemas/InputError"}}},
                    },
                    "500": {
                        "description": "Invalid Input",
                        "content": {"text/plain": {"schema": {"type": "string"}}},
                    },
                },
            },
            "post": {
                "tags": ["datasource"],
                "summary": "Create Datasource From Files",
                "description": "Create a datasource by uploading files.",
                "operationId": "create_datasource_from_files_datasource_upload_post",
                "requestBody": {
                    "content": {
                        "multipart/form-data": {"schema": {"$ref": "#/components/schemas/Body_post_datasource"}}
                    },
                    "required": True,
                },
                "responses": {
                    "201": {
                        "description": "Successful Response",
                        "content": {
                            "application/json": {"schema": {"$ref": "#/components/schemas/DatasourceMetadata"}}
                        },
                    },
                    "500": {
                        "description": "Invalid Input",
                        "content": {"text/plain": {"schema": {"type": "string"}}},
                    },
                },
            },
        },
        "/datasource/{id}": {
            "delete": {
                "tags": ["datasource"],
                "summary": "Delete Datasource",
                "description": "Delete a datasource by ID.",
                "operationId": "delete_datasource_datasource__id__delete",
                "responses": {
                    "204": {
                        "description": "No Content",
                    },
                },
            },
        },
    },
}


def get_parser(spec: dict, **kwargs):
    data_model_types = get_data_model_types(
        data_model_type=DataModelType.TypingTypedDict,
        target_python_version=PythonVersion.PY_312,
    )
    return OpenAPIHttpxParser(
        source=json.dumps(spec),
        data_model_type=data_model_types.data_model,
        data_model_root_type=data_model_types.root_model,
        data_type_manager_type=data_model_types.data_type_manager,
        data_model_field_type=data_model_types.field_model,
        enum_field_as_literal=LiteralType.All,
        use_union_operator=True,
        use_standard_collections=True,
        keep_model_order=False,
        use_field_description=True,
        **kwargs,
    )


def test_method_with_responses():
    # When an operation is parsed
    parser = get_parser(spec)
    parser.parse_raw()
    # Then the operation is added to the operations
    operation = next(o for o in parser.operations if o.path == "/datasource/" and o.method == "get")
    assert operation is not None
    # And the operation has the correct response types
    assert set(operation.response.keys()) == {200, 400, 500}
    assert operation.response[200]["json"] is not None
    assert operation.response[200]["json"].type_hint == "GetDatasourceResponse"
    assert operation.response[500]["text"] is not None
    assert operation.response[500]["text"].type_hint == "str"
    assert operation.response[400]["json"] is not None
    assert operation.response[400]["json"].type_hint == "InputError"
    # And the response types are added to the result types
    success_response_model = next(m for m in parser.results if m.name == "GetDatasourceResponse")
    assert success_response_model is not None
    assert success_response_model.render().strip() == "type GetDatasourceResponse = list[DatasourceMetadata]"
    input_error_model = next(m for m in parser.results if m.name == "InputError")
    assert input_error_model is not None
    assert input_error_model.render().strip() == "class InputError(TypedDict):\n    message: str"


def test_multipart_form_data_requests():
    # When an operation that takes in multipart form data is parsed
    parser = get_parser(spec)
    parser.parse_raw()
    # Then the operation is added to the operations
    operation = next(o for o in parser.operations if o.path == "/datasource/" and o.method == "post")
    assert operation is not None
    # And the operation has a files field
    assert operation.request_params is None
    assert operation.request_body["files"] is not None
    assert (
        operation.request_body["files"].type_hint
        == "dict[Literal['files'], FileTypes] | list[tuple[Literal['files'], FileTypes]]"
    )
    # And the operation has a data field
    assert operation.request_body["data"] is not None
    assert operation.request_body["data"].type_hint == "PostDatasourceRequest"
    # And the data type is added to the result types
    data_model = next(m for m in parser.results if m.name == "PostDatasourceRequest")
    assert data_model is not None
    assert data_model.render().strip() == "class PostDatasourceRequest(TypedDict):\n    name: str"
    # And the original data model is removed from the result types
    assert "Body_post_datasource" not in (m.name for m in parser.results)


def test_method_with_no_success_response():
    # When an operation that returns no content is parsed
    parser = get_parser(spec)
    parser.parse_raw()
    # Then the operation is added to the operations
    operation = next(o for o in parser.operations if o.path == "/datasource/{id}" and o.method == "delete")
    assert operation is not None
    # And the operation has a json None success response
    assert operation.response[204]["json"] is not None
    assert operation.response[204]["json"].type_hint == "None"
    assert operation.response[204]["text"] is None
    assert operation.response[204]["content"] is None


def test_can_collapse_root_models():
    # When parsing with root models collapsed
    parser = get_parser(spec, collapse_root_models=True)
    parser.parse_raw()
    # Then operations that return a root model are collapsed
    operation = next(o for o in parser.operations if o.path == "/datasource/" and o.method == "get")
    assert operation is not None
    assert operation.response[200]["json"] is not None
    assert operation.response[200]["json"].type_hint == "list[DatasourceMetadata]"


spec_with_params = {
    "components": {"schemas": {}},
    "paths": {
        "/items": {
            "get": {
                "summary": "List Items",
                "operationId": "list_items",
                "parameters": [
                    {"name": "limit", "in": "query", "required": False, "schema": {"type": "integer"}},
                    {"name": "offset", "in": "query", "required": False, "schema": {"type": "integer"}},
                ],
                "responses": {
                    "200": {"description": "OK", "content": {"application/json": {"schema": {"type": "array"}}}}
                },
            },
        },
        "/items/{id}": {
            "get": {
                "summary": "Get Item",
                "operationId": "get_item",
                "parameters": [
                    {"name": "id", "in": "path", "required": True, "schema": {"type": "string"}},
                    {"name": "include_details", "in": "query", "required": False, "schema": {"type": "boolean"}},
                ],
                "responses": {
                    "200": {"description": "OK", "content": {"application/json": {"schema": {"type": "object"}}}}
                },
            },
        },
    },
}


def test_all_optional_params_makes_params_optional():
    # When an operation has all optional parameters
    parser = get_parser(spec_with_params)
    parser.parse_raw()
    # Then the params argument is optional
    operation = next(o for o in parser.operations if o.path == "/items")
    assert operation.request_params is not None
    assert operation.request_params.is_optional is True


def test_required_params_keeps_params_required():
    # When an operation has at least one required parameter
    parser = get_parser(spec_with_params)
    parser.parse_raw()
    # Then the params argument is not optional
    operation = next(o for o in parser.operations if o.path == "/items/{id}")
    assert operation.request_params is not None
    assert operation.request_params.is_optional is False
