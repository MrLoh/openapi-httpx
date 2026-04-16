from __future__ import annotations

from collections import defaultdict
from pathlib import Path
from textwrap import dedent, indent
from typing import Any, Callable, Iterable, Literal, Mapping, Sequence, get_args
from urllib.parse import ParseResult

from datamodel_code_generator import Error, LiteralType, OpenAPIScope
from datamodel_code_generator.format import (
    DEFAULT_FORMATTERS,
    DatetimeClassType,
    Formatter,
    PythonVersion,
    PythonVersionMin,
)
from datamodel_code_generator.imports import Import
from datamodel_code_generator.model import DataModel, DataModelFieldBase
from datamodel_code_generator.model import pydantic as pydantic_model
from datamodel_code_generator.parser import DefaultPutDict
from datamodel_code_generator.parser.base import Result
from datamodel_code_generator.parser.openapi import (
    OpenAPIParser,
    Operation,
    ReferenceObject,
    RequestBodyObject,
)
from datamodel_code_generator.reference import snake_to_upper_camel
from datamodel_code_generator.types import DataType, DataTypeManager, StrictTypes
from pydantic import BaseModel

HttpxRequestTypes = Literal["json", "data", "files", "content"]
HttpxResponseTypes = Literal["json", "text", "content"]


class HttpxOperationModel(BaseModel):
    method: str
    path: str
    request_params: DataType | None
    request_body: dict[HttpxRequestTypes, DataType | None]
    response: dict[int, dict[HttpxResponseTypes, DataType | None]]
    description: str | None

    @property
    def success_response(
        self,
    ) -> list[tuple[HttpxResponseTypes, DataType]]:
        all_success_responses: dict[HttpxResponseTypes, DataType] = {}
        for status_code, success_responses in self.response.items():
            if status_code < 300:
                for response_type, data_type in success_responses.items():
                    if response_type not in all_success_responses and data_type is not None:
                        all_success_responses[response_type] = data_type
                    elif data_type is not None:
                        all_success_responses[response_type].data_types.append(data_type)
        return list(all_success_responses.items())


METHODS_WITH_BODY = {"POST", "PUT", "PATCH"}


class OpenAPIHttpxParser(OpenAPIParser):
    results: list[DataModel]
    data_model_root_type: type[DataModel]

    def __init__(  # noqa: PLR0913
        self,
        source: str | Path | list[Path] | ParseResult,
        *,
        data_model_type: type[DataModel] = pydantic_model.BaseModel,
        data_model_root_type: type[DataModel] = pydantic_model.CustomRootType,
        data_type_manager_type: type[DataTypeManager] = pydantic_model.DataTypeManager,
        data_model_field_type: type[DataModelFieldBase] = pydantic_model.DataModelField,
        base_class: str | None = None,
        additional_imports: list[str] | None = None,
        custom_template_dir: Path | None = None,
        extra_template_data: defaultdict[str, dict[str, Any]] | None = None,
        target_python_version: PythonVersion = PythonVersionMin,
        dump_resolve_reference_action: Callable[[Iterable[str]], str] | None = None,
        validation: bool = False,
        field_constraints: bool = False,
        snake_case_field: bool = False,
        strip_default_none: bool = False,
        aliases: Mapping[str, str] | None = None,
        allow_population_by_field_name: bool = False,
        allow_extra_fields: bool = False,
        extra_fields: str | None = None,
        apply_default_values_for_required_fields: bool = False,
        force_optional_for_required_fields: bool = False,
        class_name: str | None = None,
        use_standard_collections: bool = False,
        base_path: Path | None = None,
        use_schema_description: bool = False,
        use_field_description: bool = False,
        use_default_kwarg: bool = False,
        reuse_model: bool = False,
        encoding: str = "utf-8",
        enum_field_as_literal: LiteralType | None = None,
        use_one_literal_as_default: bool = False,
        set_default_enum_member: bool = False,
        use_subclass_enum: bool = False,
        strict_nullable: bool = False,
        use_generic_container_types: bool = False,
        enable_faux_immutability: bool = False,
        remote_text_cache: DefaultPutDict[str, str] | None = None,
        disable_appending_item_suffix: bool = False,
        strict_types: Sequence[StrictTypes] | None = None,
        empty_enum_field_name: str | None = None,
        custom_class_name_generator: Callable[[str], str] | None = None,
        field_extra_keys: set[str] | None = None,
        field_include_all_keys: bool = False,
        field_extra_keys_without_x_prefix: set[str] | None = None,
        wrap_string_literal: bool | None = False,
        use_title_as_name: bool = False,
        use_operation_id_as_name: bool = False,
        use_unique_items_as_set: bool = False,
        http_headers: Sequence[tuple[str, str]] | None = None,
        http_ignore_tls: bool = False,
        use_annotated: bool = False,
        use_non_positive_negative_number_constrained_types: bool = False,
        original_field_name_delimiter: str | None = None,
        use_double_quotes: bool = False,
        use_union_operator: bool = False,
        collapse_root_models: bool = False,
        special_field_name_prefix: str | None = None,
        remove_special_field_name_prefix: bool = False,
        capitalise_enum_members: bool = False,
        keep_model_order: bool = False,
        known_third_party: list[str] | None = None,
        custom_formatters: list[str] | None = None,
        custom_formatters_kwargs: dict[str, Any] | None = None,
        use_pendulum: bool = False,
        http_query_parameters: Sequence[tuple[str, str]] | None = None,
        treat_dot_as_module: bool = False,
        use_exact_imports: bool = False,
        default_field_extras: dict[str, Any] | None = None,
        target_datetime_class: DatetimeClassType = DatetimeClassType.Datetime,
        keyword_only: bool = False,
        frozen_dataclasses: bool = False,
        no_alias: bool = False,
        formatters: list[Formatter] = DEFAULT_FORMATTERS,
        parent_scoped_naming: bool = False,
        collapse_response_models: bool = False,
        client_class_name: str = "OpenApiClient",
        async_client: bool = False,
        use_closed_typed_dict: bool = False,
    ) -> None:
        self.client_class_name = client_class_name
        self.async_client = async_client
        self.collapse_response_models = collapse_response_models
        self.client_base_class = "AsyncClient" if async_client else "Client"
        additional_imports = list(additional_imports or [])
        additional_imports += [
            "string.Formatter",
            "typing.Any",
            "typing.Literal",
            "typing.Mapping",
            "typing.overload",
            "httpx.AsyncClient" if async_client else "httpx.Client",
        ]
        self.private_httpx_imports = dedent(
            """
                from httpx._types import AuthTypes  # type: ignore
                from httpx._types import CookieTypes  # type: ignore
                from httpx._types import FileTypes  # type: ignore
                from httpx._types import HeaderTypes  # type: ignore
                from httpx._types import RequestContent  # type: ignore
                from httpx._types import RequestExtensions  # type: ignore
                from httpx._types import TimeoutTypes  # type: ignore
            """
        )

        self.target_python_version_has_unpack_kwargs = target_python_version not in {
            PythonVersion.PY_311,
            PythonVersion.PY_310,
        }
        if self.target_python_version_has_unpack_kwargs:
            additional_imports += ["typing.Unpack", "typing.TypedDict"]
        else:
            additional_imports += ["httpx.USE_CLIENT_DEFAULT"]
            self.private_httpx_imports = (
                "from httpx._client import UseClientDefault  # type: ignore\n" + self.private_httpx_imports
            )

        super().__init__(
            source=source,
            data_model_type=data_model_type,
            data_model_root_type=data_model_root_type,
            data_model_field_type=data_model_field_type,
            data_type_manager_type=data_type_manager_type,
            base_class=base_class,
            additional_imports=additional_imports,
            custom_template_dir=custom_template_dir,
            extra_template_data=extra_template_data,
            target_python_version=target_python_version,
            dump_resolve_reference_action=dump_resolve_reference_action,
            validation=validation,
            field_constraints=field_constraints,
            snake_case_field=snake_case_field,
            strip_default_none=strip_default_none,
            aliases=aliases,
            allow_population_by_field_name=allow_population_by_field_name,
            allow_extra_fields=allow_extra_fields,
            extra_fields=extra_fields,
            apply_default_values_for_required_fields=apply_default_values_for_required_fields,
            force_optional_for_required_fields=force_optional_for_required_fields,
            class_name=class_name,
            use_standard_collections=use_standard_collections,
            base_path=base_path,
            use_schema_description=use_schema_description,
            use_field_description=use_field_description,
            use_default_kwarg=use_default_kwarg,
            reuse_model=reuse_model,
            encoding=encoding,
            enum_field_as_literal=enum_field_as_literal,
            use_one_literal_as_default=use_one_literal_as_default,
            set_default_enum_member=set_default_enum_member,
            use_subclass_enum=use_subclass_enum,
            strict_nullable=strict_nullable,
            use_generic_container_types=use_generic_container_types,
            enable_faux_immutability=enable_faux_immutability,
            remote_text_cache=remote_text_cache,
            disable_appending_item_suffix=disable_appending_item_suffix,
            strict_types=strict_types,
            empty_enum_field_name=empty_enum_field_name,
            custom_class_name_generator=custom_class_name_generator,
            field_extra_keys=field_extra_keys,
            field_include_all_keys=field_include_all_keys,
            field_extra_keys_without_x_prefix=field_extra_keys_without_x_prefix,
            wrap_string_literal=wrap_string_literal,
            use_title_as_name=use_title_as_name,
            use_operation_id_as_name=use_operation_id_as_name,
            use_unique_items_as_set=use_unique_items_as_set,
            http_headers=http_headers,
            http_ignore_tls=http_ignore_tls,
            use_annotated=use_annotated,
            use_non_positive_negative_number_constrained_types=use_non_positive_negative_number_constrained_types,
            original_field_name_delimiter=original_field_name_delimiter,
            use_double_quotes=use_double_quotes,
            use_union_operator=use_union_operator,
            allow_responses_without_content=True,
            collapse_root_models=collapse_root_models,
            special_field_name_prefix=special_field_name_prefix,
            remove_special_field_name_prefix=remove_special_field_name_prefix,
            capitalise_enum_members=capitalise_enum_members,
            keep_model_order=keep_model_order,
            known_third_party=known_third_party,
            custom_formatters=custom_formatters,
            custom_formatters_kwargs=custom_formatters_kwargs,
            use_pendulum=use_pendulum,
            http_query_parameters=http_query_parameters,
            treat_dot_as_module=treat_dot_as_module,
            use_exact_imports=use_exact_imports,
            default_field_extras=default_field_extras,
            target_datetime_class=target_datetime_class,
            keyword_only=keyword_only,
            frozen_dataclasses=frozen_dataclasses,
            no_alias=no_alias,
            formatters=formatters,
            parent_scoped_naming=parent_scoped_naming,
            include_path_parameters=True,
            openapi_scopes=[OpenAPIScope.Schemas, OpenAPIScope.Parameters, OpenAPIScope.Paths],
            use_closed_typed_dict=use_closed_typed_dict,
        )
        self.operations: list[HttpxOperationModel] = []

    @classmethod
    def _get_model_name(cls, path_name: str, method: str, suffix: str) -> str:
        camel_path_name = snake_to_upper_camel(path_name.replace("/", "_").replace("{", "by_"))
        return f"{method.capitalize()}{camel_path_name}{suffix}"

    def tuple_data_type(self, data_types: list[DataType], is_optional: bool = False) -> DataType:
        tuple_ = "tuple" if self.data_type_manager.use_standard_collections else "Tuple"
        return self.data_type(
            type=f"{tuple_}[{', '.join(d.type_hint for d in data_types)}]",
            is_optional=is_optional,
            import_=(
                Import.from_full_path("typing.Tuple") if not self.data_type_manager.use_standard_collections else None
            ),
        )

    def parse_multipart_form_data_request_body(
        self, path: list[str], method: str, data_type: DataType
    ) -> tuple[DataType | None, DataType | None]:
        # httpx expects bytes fields to be passed as files and other fields as data
        data_model = next(m for m in self.results if m.reference == data_type.reference)
        byte_fields = [f.name for f in data_model.fields if ("bytes" in f.data_type.type_hint) and f.name is not None]
        if not byte_fields:
            return None, data_type

        non_byte_fields = [f.name for f in data_model.fields if f.name not in byte_fields]
        reference = self.model_resolver.add(
            [*path, "requestBody", "content"],
            self._get_model_name(path[-2], method, suffix="Request"),
            class_name=True,
            unique=True,
        )
        data_model_without_byte_fields = data_model.__class__(
            reference=reference,
            fields=[f for f in data_model.fields if f.name in non_byte_fields],
            path=data_model.file_path,
            description=data_model.description,
        )
        self.results = [m for m in self.results if m is not data_model] + [data_model_without_byte_fields]

        file_type_type = self.data_type_manager.get_data_type_from_full_path(
            "httpx._types.FileTypes", is_custom_type=True
        )
        file_field_type = self.data_type(literals=byte_fields)
        return (
            # files: dict[Literal[*byte_fields], FileTypes] | list[tuple[Literal[*byte_fields], FileTypes]]
            self.data_type(
                data_types=[
                    self.data_type(is_dict=True, dict_key=file_field_type, data_types=[file_type_type]),
                    self.data_type(is_list=True, data_types=[self.tuple_data_type([file_field_type, file_type_type])]),
                ],
                is_optional=all(f.data_type.is_optional for f in data_model.fields if f.name in byte_fields),
            ),
            # data: reference to the data model without the byte fields
            self.data_type(reference=reference) if non_byte_fields else None,
        )

    def append_operation(
        self,
        method: str,
        path: list[str],
        parameters: DataType | None,
        request_bodies: dict[str, DataType] | None,  # content-type => data-type
        responses: dict[int | str, dict[str, DataType]],  # status-code => content-type => data-type
        description: str | None,
    ):
        request_body: dict[HttpxRequestTypes, DataType | None] = {k: None for k in get_args(HttpxRequestTypes)}
        for content_type, data_type in (request_bodies or {}).items():
            match content_type:
                case "application/json":
                    request_body["json"] = data_type
                case "application/x-www-form-urlencoded":
                    request_body["data"] = data_type
                case "multipart/form-data":
                    assert data_type.reference is not None
                    files, data = self.parse_multipart_form_data_request_body(path, method, data_type)
                    request_body["files"] = files
                    request_body["data"] = data
                case _ if content_type.startswith("text"):
                    request_body["content"] = data_type
                case _:
                    request_body["content"] = self.data_type_manager.get_data_type_from_full_path(
                        "httpx._types.RequestContent"
                    )

        response: dict[int, dict[HttpxResponseTypes, DataType | None]] = {}
        for status_code, response_types in responses.items():
            status_responses: dict[HttpxResponseTypes, DataType | None] = {
                c: None for c in get_args(HttpxResponseTypes)
            }
            for content_type, data_type in response_types.items():
                response_type = (
                    "json"
                    if content_type == "application/json"
                    else "text"
                    if content_type.startswith("text")
                    else "content"
                )

                if self.collapse_root_models or self.collapse_response_models:
                    reference = data_type.reference
                    if reference and isinstance(reference.source, self.data_model_root_type):
                        data_type = reference.source.fields[0].data_type
                        self.results = [m for m in self.results if m is not reference.source]

                if status_responses[response_type] is None:
                    status_responses[response_type] = data_type
                else:
                    status_responses[response_type].data_types.append(data_type)  # type: ignore
            response[int(status_code)] = status_responses

        self.operations.append(
            HttpxOperationModel(
                method=method,
                path="/" + path[-2].replace("#-datamodel-code-generator-#-root-#-special-#", ""),
                request_params=parameters,
                request_body=request_body,
                response=response,
                description=description,
            )
        )

    def parse_operation(
        self,
        raw_operation: dict[str, Any],
        path: list[str],
    ) -> None:
        operation = Operation.parse_obj(raw_operation)
        path_name, method = path[-2:]
        if self.use_operation_id_as_name:
            if not operation.operationId:
                msg = (
                    f"All operations must have an operationId when --use_operation_id_as_name is set."
                    f"The following path was missing an operationId: {path_name}"
                )
                raise Error(msg)
            path_name = operation.operationId
            method = ""
        parameters_data_type = self.parse_all_parameters(
            self._get_model_name(path_name, method, suffix="Params"),
            operation.parameters,
            [*path, "parameters"],
        )
        # If all parameters are optional (not required), make the params argument optional
        if parameters_data_type is not None and parameters_data_type.reference is not None:
            params_model = next((m for m in self.results if m.reference == parameters_data_type.reference), None)
            if params_model is not None and all(not f.required for f in params_model.fields):
                parameters_data_type.is_optional = True

        if operation.requestBody:
            if isinstance(operation.requestBody, ReferenceObject):
                ref_model = self.get_ref_model(operation.requestBody.ref)
                request_body = RequestBodyObject.parse_obj(ref_model)
            else:
                request_body = operation.requestBody

            request_body_data_types = self.parse_request_body(
                name=self._get_model_name(path_name, method, suffix="Request"),
                request_body=request_body,
                path=[*path, "requestBody"],
            )
            if not request_body.required:
                for data_type in request_body_data_types.values():
                    data_type.is_optional = True
        else:
            request_body_data_types = None
        response_data_types = self.parse_responses(
            name=self._get_model_name(path_name, method, suffix="Response"),
            responses=operation.responses,
            path=[*path, "responses"],
        )
        self.append_operation(
            method=method,
            path=path,
            parameters=parameters_data_type,
            request_bodies=request_body_data_types,
            responses=response_data_types,
            description=operation.description,
        )
        if OpenAPIScope.Tags in self.open_api_scopes:
            self.parse_tags(
                name=self._get_model_name(path_name, method, suffix="Tags"),
                tags=operation.tags,
                path=[*path, "tags"],
            )

    def render_method_kwargs(self) -> str:
        if self.target_python_version_has_unpack_kwargs:
            return "**kwargs: Unpack[RequestKwargs]"
        return dedent(
            """
                headers: HeaderTypes | None = None,
                cookies: CookieTypes | None = None,
                auth: AuthTypes | UseClientDefault = USE_CLIENT_DEFAULT,
                follow_redirects: bool | UseClientDefault = USE_CLIENT_DEFAULT,
                timeout: TimeoutTypes | UseClientDefault = USE_CLIENT_DEFAULT,
                extensions: RequestExtensions | None = None,
            """
        ).strip()

    def render_response_signature(
        self,
        method: str,
        path: str,
        params: DataType | None,
        request_body: dict[HttpxRequestTypes, DataType | None],
        response_content_type: HttpxResponseTypes,
        response_data_type: DataType,
        description: str | None,
    ) -> str:
        def render_arg(data_type: DataType | None) -> str:
            out = data_type.type_hint if data_type else "None"
            if not data_type or data_type.is_optional:
                out += " = None"
            return out

        if method.upper() in METHODS_WITH_BODY:
            body_args = ",\n".join(f"{k}: {render_arg(request_body[k])}" for k in request_body) + ","
        else:
            body_args = None

        if description:
            if "\n" in description.strip():
                docstring = "\n".join(
                    ['"""', "\n".join(indent(line.strip(), " " * 24) for line in description.split("\n")), '"""']
                )
            else:
                docstring = f'"""{description.strip()}"""'
        else:
            docstring = ""
        body_args_block = ("\n" + indent(body_args, " " * 16)) if body_args else ""
        parse_as_hint = f'Literal["{response_content_type}"]' if response_content_type != "content" else "None"
        parse_as_default = ' = "json"' if response_content_type == "json" else ""
        method_kwargs_block = indent(self.render_method_kwargs(), " " * 16).strip()
        docstring_block = ("\n" + indent(docstring, " " * 16)) if docstring else ""

        def_prefix = "async def" if self.async_client else "def"

        return dedent(
            f"""
            {def_prefix} {method.upper()}(
                self,
                path: Literal["{path}"],
                *,
                params: {render_arg(params)},{body_args_block}
                parse_as: {parse_as_hint}{parse_as_default},
                {method_kwargs_block}
            ) -> {response_data_type.type_hint}:{docstring_block}
            """
        ).strip()

    def render_generic_method_signature(self, method: str) -> str:
        if method.upper() in METHODS_WITH_BODY:
            body_args = dedent(
                """
                    json: Any | None = None,
                    data: Mapping[str, Any] | None = None,
                    content: RequestContent | None = None,
                    files: dict[Any, FileTypes] | list[tuple[Any, FileTypes]] | None = None,
                """
            ).strip()
        else:
            body_args = None

        body_args_block = ("\n" + indent(body_args, " " * 16)) if body_args else ""
        method_kwargs_block = indent(self.render_method_kwargs(), " " * 16).strip()

        def_prefix = "async def" if self.async_client else "def"

        return dedent(
            f"""
            {def_prefix} {method.upper()}(
                self,
                path: str,
                *,
                params: Mapping[str, Any] | None = None,{body_args_block}
                parse_as: Literal["json", "text"] | None = "json",
                {method_kwargs_block}
            ) -> Any:
            """
        ).strip()

    def render_method_implementation(self, method: str) -> str:
        if method.upper() in METHODS_WITH_BODY:
            body_args = [
                "content=content,",
                "data=data,",
                "files=files,",
                "json=json,",
            ]
        else:
            body_args = []

        if self.target_python_version_has_unpack_kwargs:
            method_kwargs = ["**kwargs,"]
        else:
            method_kwargs = [
                "headers=headers,",
                "cookies=cookies,",
                "auth=auth,",
                "follow_redirects=follow_redirects,",
                "timeout=timeout,",
                "extensions=extensions,",
            ]

        call_params = [
            "path.format(**path_params),",
            "params=query_params,",
            *body_args,
            *method_kwargs,
        ]

        indent_base = " " * 12
        indent_inner = indent_base + "    "
        await_prefix = "await " if self.async_client else ""
        call_lines = [f"{indent_base}res = {await_prefix}self.{method.lower()}("]
        call_lines.extend(f"{indent_inner}{line}" for line in call_params)
        call_lines.append(f"{indent_base})")

        lines = [
            f"{indent_base}path_params, query_params = self._parse_params(params or {{}}, path)",
            *call_lines,
            f"{indent_base}res.raise_for_status()",
            f'{indent_base}return None if res.status_code == 204 else res.json() if parse_as == "json" else res.text if parse_as == "text" else res.content',
        ]
        return "\n".join(lines)

    def render_client(self) -> str:
        operations_by_method: dict[str, list[HttpxOperationModel]] = defaultdict(list)
        for operation in self.operations:
            operations_by_method[operation.method].append(operation)

        out = []
        if self.target_python_version_has_unpack_kwargs:
            out.append(
                dedent(
                    """
                        class RequestKwargs(TypedDict, total=False):
                            headers: HeaderTypes
                            cookies: CookieTypes
                            auth: AuthTypes | None
                            follow_redirects: bool
                            timeout: TimeoutTypes
                            extensions: RequestExtensions
                    """
                )
            )

        out.append(
            dedent(
                f"""
                    class {self.client_class_name}({self.client_base_class}):
                        @staticmethod
                        def _parse_params(
                            params: Mapping[str, Any],
                            path: str,
                        ) -> tuple[dict[str, Any], dict[str, Any]]:
                            placeholders = {{name for _, name, _, _ in Formatter().parse(path) if name}}
                            path_params = {{k: v for k, v in params.items() if k in placeholders}}
                            query_params = {{k: v for k, v in params.items() if k not in placeholders and v is not None}}
                            if placeholders - path_params.keys():
                                raise ValueError(f"Missing path params: {{', '.join(placeholders - path_params.keys())}}")
                            return path_params, query_params
                """
            )
        )
        for method, operations in operations_by_method.items():
            no_overloads = len(operations) == 1 and len(operations[0].success_response) == 1
            for operation in operations:
                for response_content_type, response_data_type in operation.success_response:
                    signature = self.render_response_signature(
                        method=operation.method,
                        path=operation.path,
                        params=operation.request_params,
                        request_body=operation.request_body,
                        response_content_type=response_content_type,
                        response_data_type=response_data_type,
                        description=operation.description,
                    )
                    if no_overloads:
                        out.append(indent(signature, "    "))
                    else:
                        out.append(indent(f"@overload\n{signature}\n    pass", "    "))
                        out.append("")
            implementation = self.render_method_implementation(method)
            if no_overloads:
                out.append(indent(implementation, "        "))
            else:
                signature = self.render_generic_method_signature(method)
                out.append(indent(f"{signature}\n{indent(implementation, '    ')}", "    "))
            out.append("")

        return "\n".join(out)

    def parse(self) -> str | dict[tuple[str, ...], Result]:
        result = super().parse()
        if not isinstance(result, str):
            raise Exception("Expected string result")
        result = "\n".join(
            f"{self.private_httpx_imports}{line}" if line.startswith("from httpx import") else line
            for line in result.split("\n")
        )
        result += self.render_client()
        return result
