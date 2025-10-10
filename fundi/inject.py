import typing
import contextlib
import collections.abc

from fundi.resolve import resolve
from fundi.types import CacheKey, CallableInfo
from fundi.util import call_sync, call_async, add_injection_trace


def injection_impl(
    scope: collections.abc.Mapping[str, typing.Any],
    info: CallableInfo[typing.Any],
    cache: collections.abc.MutableMapping[CacheKey, typing.Any],
    override: collections.abc.Mapping[typing.Callable[..., typing.Any], typing.Any] | None,
) -> collections.abc.Generator[
    tuple[collections.abc.Mapping[str, typing.Any], CallableInfo[typing.Any], bool],
    typing.Any,
    None,
]:
    """
    Injection brain.

    Coordinates dependency resolution for a given `CallableInfo`. For each parameter:

    - If the parameter has a pre-resolved value (from scope, override, or cache) — uses it.
    - If the parameter requires another dependency to be resolved:
      - Yields `(scope_with_context, dependency_info, True)` to request the caller to inject it.
      - Once the value is received — caches it if allowed.

    After all parameters are resolved, yields:
      `(resolved_values_dict, top_level_callable_info, False)`

    If any error occurs during resolution, attaches injection trace and re-raises the exception.
    """

    values: dict[str, typing.Any] = {}
    try:
        for result in resolve(scope, info, cache, override):
            name = result.parameter.name
            value = result.value

            if not result.resolved:
                dependency = result.dependency
                assert dependency is not None

                value = yield {**scope, "__fundi_parameter__": result.parameter}, dependency, True

                if dependency.use_cache:
                    cache[dependency.key] = value

            values[name] = value

        yield values, info, False

    except Exception as exc:
        add_injection_trace(exc, info, values)
        raise exc


def inject(
    scope: collections.abc.Mapping[str, typing.Any],
    info: CallableInfo[typing.Any],
    stack: contextlib.ExitStack | None = None,
    cache: collections.abc.MutableMapping[CacheKey, typing.Any] | None = None,
    override: collections.abc.Mapping[typing.Callable[..., typing.Any], typing.Any] | None = None,
) -> typing.Any:
    """
    Synchronously inject dependencies into callable.

    If exit stack is not provided - it will be created and closed after injection

    :param scope: container with contextual values
    :param info: callable information
    :param stack: exit stack to properly handle generator dependencies
    :param cache: dependency cache
    :param override: override dependencies
    :return: result of callable
    """
    if info.async_:
        raise RuntimeError("Cannot process async functions in synchronous injection")

    if stack is None:
        with contextlib.ExitStack() as stack:
            return inject(scope, info, stack, cache, override)

    if cache is None:
        cache = {}

    gen = injection_impl(scope, info, cache, override)

    value: typing.Any | None = None

    try:
        while True:
            inner_scope, inner_info, more = gen.send(value)

            if more:
                value = inject(inner_scope, inner_info, stack, cache, override)
                continue

            return call_sync(stack, inner_info, inner_scope)
    except Exception as exc:
        with contextlib.suppress(StopIteration):
            gen.throw(type(exc), exc, exc.__traceback__)

        raise


async def ainject(
    scope: collections.abc.Mapping[str, typing.Any],
    info: CallableInfo[typing.Any],
    stack: contextlib.AsyncExitStack | None = None,
    cache: collections.abc.MutableMapping[CacheKey, typing.Any] | None = None,
    override: collections.abc.Mapping[typing.Callable[..., typing.Any], typing.Any] | None = None,
) -> typing.Any:
    """
    Asynchronously inject dependencies into callable.

    If exit stack is not provided - it will be created and closed after injection

    :param scope: container with contextual values
    :param info: callable information
    :param stack: exit stack to properly handle generator dependencies
    :param cache: dependency cache
    :param override: override dependencies
    :return: result of callable
    """
    if stack is None:
        async with contextlib.AsyncExitStack() as stack:
            return await ainject(scope, info, stack, cache, override)

    if cache is None:
        cache = {}

    gen = injection_impl(scope, info, cache, override)

    value: typing.Any | None = None

    try:
        while True:
            inner_scope, inner_info, more = gen.send(value)

            if more:
                value = await ainject(inner_scope, inner_info, stack, cache, override)
                continue

            if info.async_:
                return await call_async(stack, inner_info, inner_scope)

            return call_sync(stack, inner_info, inner_scope)
    except Exception as exc:
        with contextlib.suppress(StopIteration):
            gen.throw(type(exc), exc, exc.__traceback__)

        raise
