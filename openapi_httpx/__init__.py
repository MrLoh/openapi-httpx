from __future__ import annotations

from pathlib import Path
from urllib.parse import ParseResult

from datamodel_code_generator import DataModelType, LiteralType, PythonVersion
from datamodel_code_generator.model import get_data_model_types
from pydantic import BaseModel

from .httpx_parser import OpenAPIHttpxParser


class Config(BaseModel):
    """
    Configuration options for the client generator.

    Note:
        This contains a subset of the options available in the datamodel-code-generator.
        See https://koxudaxi.github.io/datamodel-code-generator/#all-command-options for details.
        It also contains some additional options specific to this library.
    """

    target_python_version: PythonVersion = PythonVersion.PY_311
    """The Python version to generate code for"""
    additional_imports: list[str] | None = None
    """Additional imports to add to the generated code"""
    client_class_name: str = "OpenApiClient"
    """Name of the HTTPX client class"""
    use_union_operator: bool = True
    """Whether to use the union `|` operator for optional fields"""
    use_standard_collections: bool = True
    """Whether to use standard collections (e.g. `list` instead of `List`)"""
    use_field_description: bool = True
    """Whether to populate docstrings from OpenAPI description"""
    collapse_root_models: bool = False
    """Whether to collapse nested models into their parent, this can lead to duplication"""
    collapse_response_models: bool = True
    """Whether to forgo declaring type aliases for simple response models like `list[Model]`"""
    async_client: bool = False
    """Generate methods on top of `httpx.AsyncClient` returning awaitables instead of synchronous responses"""
    use_closed_typed_dict: bool = False
    """Whether to use closed typed dicts (i.e. `TypedDict, closed=True`)"""


def generate(source: str | Path | ParseResult, config: Config):
    data_model_types = get_data_model_types(
        data_model_type=DataModelType.TypingTypedDict,
        target_python_version=config.target_python_version,
    )

    parser = OpenAPIHttpxParser(
        source=source,
        data_model_type=data_model_types.data_model,
        data_model_root_type=data_model_types.root_model,
        data_type_manager_type=data_model_types.data_type_manager,
        data_model_field_type=data_model_types.field_model,
        enum_field_as_literal=LiteralType.All,
        use_union_operator=config.use_union_operator,
        use_standard_collections=config.use_standard_collections,
        keep_model_order=False,
        use_field_description=config.use_field_description,
        collapse_root_models=config.collapse_root_models,
        collapse_response_models=config.collapse_response_models,
        target_python_version=config.target_python_version,
        additional_imports=config.additional_imports,
        client_class_name=config.client_class_name,
        async_client=config.async_client,
        use_closed_typed_dict=config.use_closed_typed_dict,
    )
    result = parser.parse()
    assert isinstance(result, str)
    return result
