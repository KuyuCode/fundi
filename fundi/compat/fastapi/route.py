import typing
import inspect
from enum import Enum, IntEnum
from collections.abc import Sequence

from fastapi.types import IncEx
from fastapi import Response, params
from fastapi.routing import APIRoute
from fastapi._compat import ModelField
from fastapi.responses import JSONResponse
from pydantic.v1.utils import lenient_issubclass
from fastapi.datastructures import Default, DefaultPlaceholder
from starlette.routing import BaseRoute, compile_path, get_name, request_response

from fastapi.utils import (
    create_model_field,  # pyright: ignore[reportUnknownVariableType]
    generate_unique_id,
    get_path_param_names,
    is_body_allowed_for_status_code,
)
from fastapi.dependencies.utils import (
    get_body_field,
    _should_embed_body_fields,  # pyright: ignore[reportPrivateUsage]
)

from fundi import scan
from fundi.util import callable_str
from fundi.types import CallableInfo
from fundi.compat.fastapi import secured
from .handler import get_request_handler
from .dependant import get_scope_dependant, update_dependant


@typing.final
class FunDIRoute(APIRoute):

    def __init__(  # pyright: ignore[reportMissingSuperCall]
        self,
        path: str,
        endpoint: typing.Callable[..., typing.Any],
        *,
        response_model: typing.Any = Default(None),
        status_code: int | None = None,
        tags: list[str | Enum] | None = None,
        dependencies: (
            Sequence[typing.Callable[..., typing.Any] | params.Depends | CallableInfo[typing.Any]]
            | None
        ) = None,
        summary: str | None = None,
        description: str | None = None,
        response_description: str = "Successful Response",
        responses: dict[int | str, dict[str, typing.Any]] | None = None,
        deprecated: bool | None = None,
        name: str | None = None,
        methods: set[str] | list[str] | None = None,
        operation_id: str | None = None,
        response_model_include: IncEx | None = None,
        response_model_exclude: IncEx | None = None,
        response_model_by_alias: bool = True,
        response_model_exclude_unset: bool = False,
        response_model_exclude_defaults: bool = False,
        response_model_exclude_none: bool = False,
        include_in_schema: bool = True,
        response_class: type[Response] | DefaultPlaceholder = Default(JSONResponse),
        dependency_overrides_provider: typing.Any | None = None,
        callbacks: list[BaseRoute] | None = None,
        openapi_extra: dict[str, typing.Any] | None = None,
        generate_unique_id_function: (
            typing.Callable[[APIRoute], str] | DefaultPlaceholder
        ) = Default(generate_unique_id),
    ) -> None:
        callable_info = scan(endpoint)
        self.ci = callable_info
        self.path = path
        self.endpoint = endpoint
        self.dependencies: list[CallableInfo[typing.Any]] = []

        for dependency in dependencies or []:
            if isinstance(dependency, params.Security):
                security = dependency
                assert (
                    security.dependency is not None
                ), f"Dependency defined in endpoint {callable_str(endpoint)} doesn't have callable"

                self.dependencies.append(
                    secured(security.dependency, security.scopes, security.use_cache)
                )
                continue

            if isinstance(dependency, params.Depends):
                depends = dependency

                assert (
                    depends.dependency is not None
                ), f"Dependency defined in endpoint {callable_str(endpoint)} doesn't have callable"

                self.dependencies.append(scan(depends.dependency, depends.use_cache))
                continue

            if isinstance(dependency, CallableInfo):
                self.dependencies.append(dependency)
                continue

            self.dependencies.append(scan(dependency))

        if isinstance(response_model, DefaultPlaceholder):
            if not lenient_issubclass(callable_info.return_annotation, Response):
                response_model = None
            else:
                response_model = callable_info.return_annotation

        self.response_model = response_model
        self.summary = summary
        self.response_description = response_description
        self.deprecated = deprecated
        self.operation_id = operation_id
        self.response_model_include = response_model_include
        self.response_model_exclude = response_model_exclude
        self.response_model_by_alias = response_model_by_alias
        self.response_model_exclude_unset = response_model_exclude_unset
        self.response_model_exclude_defaults = response_model_exclude_defaults
        self.response_model_exclude_none = response_model_exclude_none
        self.include_in_schema = include_in_schema
        self.response_class = response_class
        self.dependency_overrides_provider = dependency_overrides_provider
        self.callbacks = callbacks
        self.openapi_extra = openapi_extra
        self.generate_unique_id_function = generate_unique_id_function
        self.tags = tags or []
        self.responses = responses or {}
        self.name = get_name(endpoint) if name is None else name
        self.path_regex, self.path_format, self.param_convertors = compile_path(path)

        if methods is None:
            methods = ["GET"]
        self.methods: set[str] = {method.upper() for method in methods}

        if isinstance(generate_unique_id_function, DefaultPlaceholder):
            current_generate_unique_id: typing.Callable[[APIRoute], str] = (
                generate_unique_id_function.value
            )
        else:
            current_generate_unique_id = generate_unique_id_function

        self.unique_id = self.operation_id or current_generate_unique_id(self)
        # normalize enums e.g. http.HTTPStatus
        if isinstance(status_code, IntEnum):
            status_code = int(status_code)

        self.status_code = status_code

        if self.response_model:
            assert is_body_allowed_for_status_code(
                status_code
            ), f"Status code {status_code} must not have a response body"
            response_name = "Response_" + self.unique_id
            self.response_field = create_model_field(
                name=response_name,
                type_=self.response_model,
                mode="serialization",
            )
            self.secure_cloned_response_field = None
        else:
            self.response_field = None  # type: ignore
            self.secure_cloned_response_field = None

        self.description = description or inspect.cleandoc(self.endpoint.__doc__ or "")

        # if a "form feed" character (page break) is found in the description text,
        # truncate description text to the content preceding the first "form feed"
        self.description = self.description.split("\f")[0].strip()

        response_fields: dict[int | str, ModelField] = {}
        for additional_status_code, response in self.responses.items():
            assert isinstance(response, dict), "An additional response must be a dict"
            model = response.get("model")
            if model:
                assert is_body_allowed_for_status_code(
                    additional_status_code
                ), f"Status code {additional_status_code} must not have a response body"
                response_name = f"Response_{additional_status_code}_{self.unique_id}"
                response_field = create_model_field(
                    name=response_name, type_=model, mode="serialization"
                )
                response_fields[additional_status_code] = response_field

        self.response_fields = response_fields

        path_param_names = get_path_param_names(self.path_format)
        self.dependant = get_scope_dependant(callable_info, path_param_names, self.path_format)

        for ci in self.dependencies:
            update_dependant(
                get_scope_dependant(ci, path_param_names, self.path_format), self.dependant
            )

        self._embed_body_fields = _should_embed_body_fields(self.dependant.body_params)
        self.body_field = get_body_field(
            flat_dependant=self.dependant,
            name=self.unique_id,
            embed_body_fields=self._embed_body_fields,
        )

        self.app = request_response(
            get_request_handler(
                callable_info,
                extra_dependencies=self.dependencies[::-1],
                body_field=self.body_field,
                status_code=self.status_code,
                response_class=self.response_class,
                response_field=self.secure_cloned_response_field,
                response_model_include=self.response_model_include,
                response_model_exclude=self.response_model_exclude,
                response_model_by_alias=self.response_model_by_alias,
                response_model_exclude_unset=self.response_model_exclude_unset,
                response_model_exclude_defaults=self.response_model_exclude_defaults,
                response_model_exclude_none=self.response_model_exclude_none,
                dependency_overrides_provider=self.dependency_overrides_provider,
                embed_body_fields=self._embed_body_fields,
            )
        )
