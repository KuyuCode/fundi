import json
import typing
import inspect
from enum import Enum, IntEnum
from collections import defaultdict
from contextlib import AsyncExitStack
from collections.abc import Coroutine, Sequence

from fastapi.types import IncEx
from pydantic.v1.fields import Undefined
from fastapi.responses import JSONResponse
from starlette.requests import HTTPConnection
from starlette.background import BackgroundTasks
from pydantic.v1.utils import lenient_issubclass
from fastapi.dependencies.models import Dependant
from fastapi.security.oauth2 import SecurityScopes
from fastapi.exceptions import RequestValidationError
from fastapi.routing import APIRoute, serialize_response
from fastapi._compat import ModelField, _normalize_errors  # pyright: ignore[reportPrivateUsage]
from fastapi.datastructures import Default, DefaultPlaceholder
from fastapi import HTTPException, Request, Response, WebSocket, params
from starlette.routing import BaseRoute, compile_path, get_name, request_response

from fundi import scan, ainject, CallableInfo

from fastapi.utils import (
    create_model_field,  # pyright: ignore[reportUnknownVariableType]
    generate_unique_id,
    get_path_param_names,
    is_body_allowed_for_status_code,
)
from fastapi.dependencies.utils import (
    analyze_param,
    get_body_field,
    solve_dependencies,
    add_param_to_fields,
    _should_embed_body_fields,  # pyright: ignore[reportPrivateUsage]
)


ALIAS_ALLOWED_CLASSES = (
    Request,
    WebSocket,
    HTTPConnection,
    Response,
    BackgroundTasks,
    SecurityScopes,
)


async def validate_body(request: Request, stack: AsyncExitStack, body_field: ModelField | None):
    is_body_form = body_field and isinstance(body_field.field_info, params.Form)
    try:
        if body_field:
            if is_body_form:
                form = await request.form()
                stack.push_async_callback(form.close)
                return form

            body_bytes = await request.body()
            if body_bytes:
                json_body: typing.Any = Undefined
                content_type_value = request.headers.get("content-type")

                if not content_type_value:
                    json_body = await request.json()

                else:
                    if content_type_value.count("/") != 1:
                        content_type_value = "text/plain"

                    maintype, subtype = content_type_value.split("/", 1)

                    if maintype == "application":
                        if subtype == "json" or subtype.endswith("+json"):
                            json_body = await request.json()

                if json_body != Undefined:
                    return json_body
                else:
                    return typing.cast(typing.Any, body_bytes)
    except json.JSONDecodeError as e:
        validation_error = RequestValidationError(
            [
                {
                    "type": "json_invalid",
                    "loc": ("body", e.pos),
                    "msg": "JSON decode error",
                    "input": {},
                    "ctx": {"error": e.msg},
                }
            ],
            body=e.doc,
        )
        raise validation_error from e
    except HTTPException:
        # If a middleware raises an HTTPException, it should be raised again
        raise
    except Exception as e:
        http_error = HTTPException(status_code=400, detail="There was an error parsing the body")
        raise http_error from e


def get_request_handler(
    ci: CallableInfo[typing.Any],
    scope_dependant: Dependant,
    extra_dependencies: list[CallableInfo[typing.Any]],
    scope_aliases: dict[type, set[str]],
    body_field: ModelField | None = None,
    status_code: int | None = None,
    response_class: type[Response] | DefaultPlaceholder = Default(JSONResponse),
    response_field: ModelField | None = None,
    response_model_include: IncEx | None = None,
    response_model_exclude: IncEx | None = None,
    response_model_by_alias: bool = True,
    response_model_exclude_unset: bool = False,
    response_model_exclude_defaults: bool = False,
    response_model_exclude_none: bool = False,
    dependency_overrides_provider: typing.Any | None = None,
    embed_body_fields: bool = False,
) -> typing.Callable[[Request], Coroutine[typing.Any, typing.Any, Response]]:

    if isinstance(response_class, DefaultPlaceholder):
        actual_response_class: type[Response] = response_class.value
    else:
        actual_response_class = response_class

    async def app(request: Request) -> Response:
        async with AsyncExitStack() as stack:
            body = await validate_body(request, stack, body_field)

            scope = await solve_dependencies(
                request=request,
                dependant=scope_dependant,
                body=body,
                dependency_overrides_provider=dependency_overrides_provider,
                async_exit_stack=stack,
                embed_body_fields=embed_body_fields,
            )

            if scope.errors:
                raise RequestValidationError(_normalize_errors(scope.errors), body=body)

            values = {**scope.values}

            for type_, names in scope_aliases.items():

                if type_ is HTTPConnection:
                    value = request
                elif type_ is Request:
                    value = request
                elif type_ is WebSocket:
                    assert isinstance(request, WebSocket), "Not a websocket"
                    value = request
                elif type_ is BackgroundTasks:
                    value = scope.background_tasks or BackgroundTasks()
                elif type_ is Response:
                    value = scope.response
                else:
                    value = scope_dependant.security_scopes

                values.update({name: value for name in names})

            for dependency in extra_dependencies:
                await ainject(values, dependency, stack)

            raw_response = await ainject(values, ci, stack)

            if isinstance(raw_response, Response):
                if raw_response.background is None:
                    raw_response.background = scope.background_tasks

                response = raw_response
            else:
                response_args: dict[str, typing.Any] = {"background": scope.background_tasks}

                # If status_code was set, use it, otherwise use the default from the
                # response class, in the case of redirect it's 307

                status = scope.response.status_code or status_code
                if status is not None:
                    response_args["status_code"] = status

                content = await serialize_response(
                    field=response_field,
                    response_content=raw_response,
                    include=response_model_include,
                    exclude=response_model_exclude,
                    by_alias=response_model_by_alias,
                    exclude_unset=response_model_exclude_unset,
                    exclude_defaults=response_model_exclude_defaults,
                    exclude_none=response_model_exclude_none,
                    is_coroutine=ci.async_,
                )
                response = actual_response_class(content, **response_args)
                if not is_body_allowed_for_status_code(response.status_code):
                    response.body = b""

                response.headers.raw.extend(scope.response.headers.raw)

        return response

    return app


def get_scope_dependant(
    ci: CallableInfo[typing.Any], path_param_names: set[str], path: str
) -> Dependant:
    dependant = Dependant(path=path)

    for param in ci.parameters:
        if param.from_ is not None:
            sub = get_scope_dependant(param.from_, path_param_names, path)
            dependant.path_params.extend(sub.path_params)
            dependant.query_params.extend(sub.query_params)
            dependant.header_params.extend(sub.header_params)
            dependant.cookie_params.extend(sub.cookie_params)
            dependant.body_params.extend(sub.body_params)
            continue

        details = analyze_param(
            param_name=param.name,
            annotation=param.annotation,
            value=param.default,
            is_path_param=param.name in path_param_names,
        )

        if details.type_annotation in ALIAS_ALLOWED_CLASSES:
            continue

        assert details.field is not None
        if isinstance(details.field.field_info, params.Body):
            dependant.body_params.append(details.field)
        else:
            add_param_to_fields(field=details.field, dependant=dependant)

    return dependant


def get_request_related_aliases(ci: CallableInfo[typing.Any]) -> dict[type, set[str]]:
    aliases: defaultdict[type, set[str]] = defaultdict(set)
    for parameter in ci.parameters:
        if parameter.from_ is not None:
            subaliases = get_request_related_aliases(parameter.from_)
            for type_, aliases_ in subaliases.items():
                aliases[type_].update(aliases_)
            continue

        origin = typing.get_origin(parameter.annotation) or parameter.annotation

        for type_ in ALIAS_ALLOWED_CLASSES:
            if lenient_issubclass(origin, type_):
                aliases[type_].add(parameter.name)
    return aliases


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
        dependencies: Sequence[typing.Callable[..., typing.Any]] | None = None,
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

        self.dependant = get_scope_dependant(
            callable_info, get_path_param_names(self.path_format), self.path_format
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
                self.dependant,
                extra_dependencies=[scan(call) for call in (dependencies or [])[::-1]],
                scope_aliases=get_request_related_aliases(callable_info),
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
