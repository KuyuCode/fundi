import typing
from collections.abc import Coroutine
from contextlib import AsyncExitStack

from fastapi.types import IncEx
from starlette.requests import Request
from fastapi._compat import ModelField
from fastapi.routing import serialize_response
from starlette.background import BackgroundTasks
from starlette.responses import JSONResponse, Response
from fastapi.utils import is_body_allowed_for_status_code
from fastapi.datastructures import Default, DefaultPlaceholder

from .inject import inject
from fundi.types import CallableInfo

from .validate_request_body import validate_body


def get_request_handler(
    ci: CallableInfo[typing.Any],
    extra_dependencies: list[CallableInfo[typing.Any]],
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
        background_tasks = BackgroundTasks()
        stack = AsyncExitStack()
        # Close exit stack at after the response is sent
        background_tasks.add_task(stack.aclose)

        response = Response()
        del response.headers["content-length"]
        response.status_code = None  # pyright: ignore[reportAttributeAccessIssue]

        body_stack = AsyncExitStack()
        async with body_stack:
            body = await validate_body(request, body_stack, body_field)

            for dependency in extra_dependencies:
                await inject(
                    dependency,
                    stack,
                    request,
                    body,
                    dependency_overrides_provider,
                    embed_body_fields,
                    background_tasks,
                    response,
                )

            raw_response = await inject(
                ci,
                stack,
                request,
                body,
                dependency_overrides_provider,
                embed_body_fields,
                background_tasks,
                response,
            )

        if isinstance(raw_response, Response):
            if raw_response.background is None:
                raw_response.background = background_tasks

            return raw_response

        response_args: dict[str, typing.Any] = {"background": background_tasks}

        # If status_code was set, use it, otherwise use the default from the
        # response class, in the case of redirect it's 307
        status = response.status_code or status_code
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

        response.headers.raw.extend(response.headers.raw)

        return response

    return app
