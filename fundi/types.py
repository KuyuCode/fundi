import typing
import collections
import collections.abc
from typing_extensions import override
from dataclasses import dataclass, field, replace

__all__ = [
    "R",
    "Parameter",
    "TypeResolver",
    "CallableInfo",
    "InjectionTrace",
    "ParameterResult",
    "DependencyConfiguration",
]

R = typing.TypeVar("R")


@dataclass
class TypeResolver:
    """
    Mark that tells ``fundi.scan.scan`` to set ``Parameter.resolve_by_type`` to True.

    This changes logic of ``fundi.resolve.resolve``, so it uses ``Parameter.annotation``
    to find value in scope instead of ``Parameter.name``
    """

    annotation: type


@dataclass
class Parameter:
    name: str
    annotation: typing.Any
    from_: "CallableInfo[typing.Any] | None"
    default: typing.Any = None
    has_default: bool = False
    resolve_by_type: bool = False
    positional_only: bool = False
    keyword_only: bool = False
    positional_varying: bool = False
    keyword_varying: bool = False

    def copy(self, deep: bool = False, **update: typing.Any):
        if not deep:
            return replace(self, **update)

        return replace(
            self, **{"from_": self.from_.copy(deep=True) if self.from_ else None, **update}
        )


@dataclass
class CallableInfo(typing.Generic[R]):
    call: typing.Callable[..., R]
    use_cache: bool
    async_: bool
    context: bool
    generator: bool
    parameters: list[Parameter]
    return_annotation: typing.Any
    configuration: "DependencyConfiguration | None"
    named_parameters: dict[str, Parameter] = field(init=False)
    key: "CacheKey" = field(init=False)

    graphhook: typing.Callable[["CallableInfo[R]", Parameter], "typing.Any"] | None = None

    def __post_init__(self):
        self.named_parameters = {p.name: p for p in self.parameters}
        self.key = CacheKey(self.call)

    @override
    def __hash__(self) -> int:
        return hash(self.key)

    @override
    def __eq__(self, value: object) -> bool:
        return hash(self.key) == hash(value)

    def _build_values(
        self,
        args: tuple[typing.Any, ...],
        kwargs: collections.abc.MutableMapping[str, typing.Any],
        partial: bool = False,
    ) -> dict[str, typing.Any]:
        values: dict[str, typing.Any] = {}

        args_amount = len(args)

        ix = 0
        for parameter in self.parameters:
            name = parameter.name

            if parameter.keyword_varying:
                values[name] = kwargs
                continue

            if name in kwargs:
                values[name] = kwargs.pop(name)
                continue

            if parameter.positional_varying:
                values[name] = args[ix:]
                ix = args_amount
                continue

            if ix < args_amount:
                values[name] = args[ix]
                ix += 1
                continue

            if parameter.has_default:
                values[name] = parameter.default
                continue

            if not partial:
                raise ValueError(f'Argument for parameter "{parameter.name}" not found')

        return values

    def build_values(
        self, *args: typing.Any, **kwargs: typing.Any
    ) -> collections.abc.Mapping[str, typing.Any]:
        return self._build_values(args, kwargs)

    def partial_build_values(
        self, *args: typing.Any, **kwargs: typing.Any
    ) -> collections.abc.Mapping[str, typing.Any]:
        return self._build_values(args, kwargs, partial=True)

    def build_arguments(
        self, values: collections.abc.Mapping[str, typing.Any]
    ) -> tuple[tuple[typing.Any, ...], dict[str, typing.Any]]:
        positional: tuple[typing.Any, ...] = ()
        keyword: dict[str, typing.Any] = {}

        for parameter in self.parameters:
            name = parameter.name

            if name not in values:
                raise ValueError(f'Value for "{name}" parameter not found')

            value = values[name]

            if parameter.positional_only:
                positional += (value,)
            elif parameter.positional_varying:
                positional += value
            elif parameter.keyword_only:
                keyword[name] = value
            elif parameter.keyword_varying:
                keyword.update(value)
            else:
                positional += (value,)

        return positional, keyword

    def copy(self, deep: bool = False, **update: typing.Any):
        if not deep:
            return replace(self, **update)

        return replace(
            self,
            **{
                "parameters": [parameter.copy(deep=True) for parameter in self.parameters],
                **update,
            },
        )


class CacheKey:
    __slots__: tuple[str, ...] = ("_hash", "_items")

    def __init__(self, *initial_items: collections.abc.Hashable):
        self._hash: int | None = None
        self._items: list[collections.abc.Hashable] = list(initial_items)

    def add(self, *items: collections.abc.Hashable):
        self._items.extend(items)
        self._hash = None

    @override
    def __hash__(self) -> int:
        if self._hash is not None:
            return self._hash

        self._hash = hash(tuple(self._items))

        return self._hash

    @override
    def __eq__(self, value: typing.Hashable) -> bool:
        return self._hash == hash(value)

    @override
    def __repr__(self) -> str:
        return f"#{hash(self)}"


@dataclass
class ParameterResult:
    parameter: Parameter
    value: typing.Any | None
    dependency: CallableInfo[typing.Any] | None
    resolved: bool


@dataclass
class InjectionTrace:
    info: CallableInfo[typing.Any]
    values: collections.abc.Mapping[str, typing.Any]
    origin: "InjectionTrace | None" = None


@dataclass
class DependencyConfiguration:
    configurator: CallableInfo[typing.Any]
    values: collections.abc.Mapping[str, typing.Any]
