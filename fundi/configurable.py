from collections.abc import Callable
import typing
import warnings
import functools

from fundi.scan import scan
from fundi.util import callable_str
from fundi.types import DependencyConfiguration

P = typing.ParamSpec("P")
InnerP = typing.ParamSpec("InnerP")
R = typing.TypeVar("R")


class MutableConfigurationWarning(UserWarning):
    pass


class DependencyConfiguratorProtocol(typing.Protocol[P, InnerP, R]):
    origin: Callable[P, Callable[InnerP, R]]
    """
    Original dependency configurator.
    This is the function that passed to @configurable_dependency decorator
    """

    def __call__(
        self, *args: P.args, **kwargs: P.kwargs
    ) -> "ConfiguredDependencyProtocol[InnerP, R]": ...


class ConfiguredDependencyProtocol(typing.Protocol[P, R]):
    __fundi_configuration__: DependencyConfiguration

    def __call__(self, *args: P.args, **kwargs: P.kwargs) -> R: ...


def configurable_dependency(
    configurator: Callable[P, Callable[InnerP, R]],
) -> DependencyConfiguratorProtocol[P, InnerP, R]:
    """
    Create dependency configurator that caches configured dependencies.
    This helps FunDI cache resolver understand that dependency already executed, if it was.

    Note: Calls with mutable arguments will not be stored in cache and warning would be shown

    :param configurator: Original dependency configurator
    :return: cache aware dependency configurator
    """
    dependencies: dict[
        frozenset[tuple[str, typing.Any]], ConfiguredDependencyProtocol[InnerP, R]
    ] = {}
    info = scan(configurator)

    if info.async_:
        raise ValueError("Dependency configurator should not be asynchronous")

    @functools.wraps(configurator)
    def cached_dependency_generator(
        *args: typing.Any, **kwargs: typing.Any
    ) -> ConfiguredDependencyProtocol[InnerP, R]:
        values = info.build_values(*args, **kwargs)
        key: frozenset[tuple[str, typing.Any]] | None = None

        try:
            key = frozenset(values.items())

            if key in dependencies:
                return dependencies[key]
        except TypeError:
            warnings.warn(
                f"Can't cache dependency created via {callable_str(configurator)}: configured with unhashable arguments",
                MutableConfigurationWarning,
            )

        dependency = configurator(*args, **kwargs)
        setattr(
            dependency,
            "__fundi_configuration__",
            DependencyConfiguration(configurator=info, values=values),
        )

        dependency = typing.cast(ConfiguredDependencyProtocol[InnerP, R], dependency)

        if key is not None:
            dependencies[key] = dependency

        return dependency

    setattr(cached_dependency_generator, "origin", configurator)

    return typing.cast(DependencyConfiguratorProtocol, cached_dependency_generator)
