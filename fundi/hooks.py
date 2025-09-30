import typing

from fundi.scan import scan as scan_
from fundi.types import CallableInfo, Parameter

R = typing.TypeVar("R")
C = typing.TypeVar("C", bound=typing.Callable[..., typing.Any])


def with_hooks(
    graph: typing.Callable[[CallableInfo[R], Parameter], CallableInfo[R] | None] | None = None,
):
    def applier(call: C) -> C:
        info = scan_(call)

        info.graphhook = graph

        setattr(call, "__fundi_info__", info)

        return call

    return applier
