from collections.abc import Mapping
import typing


class DependencyOverridesProvider(typing.Protocol):
    dependency_overrides: Mapping[
        typing.Callable[..., typing.Any], typing.Callable[..., typing.Any]
    ]
