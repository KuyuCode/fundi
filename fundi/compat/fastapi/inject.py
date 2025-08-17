import typing
import contextlib
import collections.abc

from starlette.requests import Request
from starlette.responses import Response
from starlette.datastructures import FormData
from fastapi._compat import _normalize_errors  # pyright: ignore[reportPrivateUsage]
from starlette.background import BackgroundTasks
from fastapi.exceptions import RequestValidationError
from fastapi.dependencies.utils import solve_dependencies

from fundi.inject import injection_impl
from fundi.util import call_async, call_sync
from fundi.types import CacheKey, CallableInfo

from .metadata import get_metadata
from .types import DependencyOverridesProvider
from .constants import METADATA_DEPENDANT, METADATA_SCOPE_EXTRA, METADATA_SECURITY_SCOPES


async def inject(
    info: CallableInfo[typing.Any],
    stack: contextlib.AsyncExitStack,
    request: Request,
    body: FormData | typing.Any | None,
    dependency_overrides_provider: DependencyOverridesProvider | None,
    embed_body_fields: bool,
    background_tasks: BackgroundTasks,
    response: Response,
    cache: collections.abc.MutableMapping[CacheKey, typing.Any] | None = None,
    override: collections.abc.Mapping[typing.Callable[..., typing.Any], typing.Any] | None = None,
) -> typing.Any:
    """
    Asynchronously inject dependencies into callable.

    :param scope: container with contextual values
    :param info: callable information
    :param stack: exit stack to properly handle generator dependencies
    :param cache: dependency cache
    :param override: override dependencies
    :return: result of callable
    """
    if cache is None:
        cache = {}

    metadata = get_metadata(info)

    fastapi_params = await solve_dependencies(
        request=request,
        dependant=metadata[METADATA_DEPENDANT],
        body=body,
        dependency_overrides_provider=dependency_overrides_provider,
        async_exit_stack=stack,
        embed_body_fields=embed_body_fields,
        background_tasks=background_tasks,
        response=response,
    )

    if fastapi_params.errors:
        raise RequestValidationError(_normalize_errors(fastapi_params.errors), body=body)

    scope = fastapi_params.values

    scope_extra: collections.abc.Mapping[str, typing.Any] = metadata.get(METADATA_SCOPE_EXTRA, {})

    if scope_extra:
        scope = {**scope, **scope_extra}

    gen = injection_impl(scope, info, cache, override)

    value: typing.Any | None = None

    try:
        while True:
            inner_scope, inner_info, more = gen.send(value)

            if more:
                value = await inject(
                    inner_info,
                    stack,
                    request,
                    body,
                    dependency_overrides_provider,
                    embed_body_fields,
                    background_tasks,
                    response,
                    cache,
                    override,
                )
                continue

            if info.async_:
                return await call_async(stack, inner_info, inner_scope)

            return call_sync(stack, inner_info, inner_scope)
    except Exception as exc:
        with contextlib.suppress(StopIteration):
            gen.throw(type(exc), exc, exc.__traceback__)

        raise
