import typing
from typing import Callable, TypeVar

from fundi.scan import scan

C = TypeVar("C", bound=Callable[..., typing.Any])


def with_side_effects(*side_effects: Callable[..., typing.Any]) -> Callable[[C], C]:
    """
    Apply side effects to dependency globally

    Usage::

        from fundi import with_side_effects

        @with_side_effects(lambda __dependant__: print(dependant.call, "Gets injected"))
        def dependency():
            ...

    """

    def applier(dependency: C) -> C:
        info = scan(dependency, side_effects=side_effects)

        # Reset cached CallableInfo
        # This way at future scans the side effects applied
        # here will be present in next copies
        try:
            setattr(dependency, "__fundi_info__", info)
        except (AttributeError, ValueError):
            pass

        return dependency

    return applier
