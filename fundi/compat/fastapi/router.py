import typing
from enum import Enum
from collections.abc import Sequence
from fastapi.routing import APIRoute
from fastapi import APIRouter, params
from starlette.routing import BaseRoute
from starlette.responses import Response
from fastapi.datastructures import Default
from fastapi.responses import JSONResponse
from fastapi.utils import generate_unique_id
from starlette.types import ASGIApp, Lifespan

from fundi.compat.fastapi.route import FunDIRoute


class FunDIRouter(APIRouter):
    def __init__(
        self,
        *,
        prefix: str = "",
        tags: list[str | Enum] | None = None,
        dependencies: Sequence[params.Depends] | None = None,
        default_response_class: type[Response] = Default(JSONResponse),
        responses: dict[int | str, dict[str, typing.Any]] | None = None,
        callbacks: list[BaseRoute] | None = None,
        routes: list[BaseRoute] | None = None,
        redirect_slashes: bool = True,
        default: ASGIApp | None = None,
        dependency_overrides_provider: typing.Any = None,
        route_class: type[APIRoute] = FunDIRoute,
        on_startup: Sequence[typing.Callable[[], typing.Any]] | None = None,
        on_shutdown: Sequence[typing.Callable[[], typing.Any]] | None = None,
        lifespan: Lifespan[typing.Any] | None = None,
        deprecated: bool | None = None,
        include_in_schema: bool = True,
        generate_unique_id_function: typing.Callable[[APIRoute], str] = Default(generate_unique_id),
    ) -> None:
        super().__init__(
            prefix=prefix,
            tags=tags,
            dependencies=dependencies,
            default_response_class=default_response_class,
            responses=responses,
            callbacks=callbacks,
            routes=routes,
            redirect_slashes=redirect_slashes,
            default=default,
            dependency_overrides_provider=dependency_overrides_provider,
            route_class=route_class,
            on_startup=on_startup,
            on_shutdown=on_shutdown,
            lifespan=lifespan,
            deprecated=deprecated,
            include_in_schema=include_in_schema,
            generate_unique_id_function=generate_unique_id_function,
        )
