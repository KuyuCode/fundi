import typing

from fundi.types import CallableInfo, Parameter

R = typing.TypeVar("R")
C = typing.TypeVar("C", bound=typing.Callable[..., typing.Any])


def with_hooks(
    graph: typing.Callable[[CallableInfo[R], Parameter], typing.Any] | None = None,
):
    def applier(call: C) -> C:
        hooks: dict[str, typing.Callable[..., typing.Any]] | None = getattr(
            call, "__fundi_hooks__", None
        )
        if hooks is None:
            hooks = {}
            setattr(call, "__fundi_hooks__", hooks)

        if graph is not None:
            hooks["graph"] = graph

        return call

    return applier
