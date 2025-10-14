import typing

from fundi.types import CallableInfo, Parameter, ScopeHook

C = typing.TypeVar("C", bound=typing.Callable[..., typing.Any])


def with_hooks(
    graph: typing.Callable[[CallableInfo[typing.Any], Parameter], typing.Any] | None = None,
    scope: ScopeHook | None = None,
) -> typing.Callable[[C], C]:
    def applier(call: C) -> C:
        hooks: dict[str, typing.Callable[..., typing.Any]] | None = getattr(
            call, "__fundi_hooks__", None
        )
        if hooks is None:
            hooks = {}
            setattr(call, "__fundi_hooks__", hooks)

        if graph is not None:
            hooks["graph"] = graph

        if scope is not None:
            hooks["scope"] = scope

        return call

    return applier
