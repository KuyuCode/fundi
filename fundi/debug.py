import typing
import collections.abc

from fundi.scope import Scope
from fundi.inject import injection_impl
from fundi.types import CacheKey, CallableInfo


def tree(
    scope: collections.abc.Mapping[str, typing.Any] | Scope,
    info: CallableInfo[typing.Any],
    cache: (
        collections.abc.MutableMapping[CacheKey, collections.abc.Mapping[str, typing.Any]] | None
    ) = None,
) -> collections.abc.Mapping[str, typing.Any]:
    """
    Get tree of dependencies of callable.

    :param scope: container with contextual values
    :param info: callable information
    :param cache: tree generation cache
    :return: Tree of dependencies
    """
    if not isinstance(scope, Scope):
        scope = Scope({**scope})

    if cache is None:
        cache = {}

    gen = injection_impl(scope, info, cache, None)

    value = None

    while True:
        inner_scope, inner_info, more = gen.send(value)
        if not more:
            return {"call": inner_info.call, "values": inner_scope}

        value = tree(inner_scope, inner_info, cache)


def order(
    scope: collections.abc.Mapping[str, typing.Any] | Scope,
    info: CallableInfo[typing.Any],
    cache: (
        collections.abc.MutableMapping[CacheKey, list[typing.Callable[..., typing.Any]]] | None
    ) = None,
) -> list[typing.Callable[..., typing.Any]]:
    """
    Get resolving order of callable dependencies.

    :param info: callable information
    :param scope: container with contextual values
    :param cache: solvation cache
    :return: order of dependencies
    """
    if not isinstance(scope, Scope):
        scope = Scope({**scope})

    if cache is None:
        cache = {}

    gen = injection_impl(scope, info, cache, None)

    order_: list[typing.Callable[..., typing.Any]] = []

    value = None
    while True:
        inner_scope, inner_info, more = gen.send(value)
        if not more:
            return order_

        order_.extend(order(inner_scope, inner_info, cache))
        order_.append(inner_info.call)
