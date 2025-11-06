import typing
import collections
import collections.abc
from logging import Logger
from typing_extensions import override
from dataclasses import dataclass, field, replace

from fundi.logging import get_logger

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


ScopeHook = typing.Callable[[dict[str, typing.Any], "CallableInfo[typing.Any]"], typing.Any]


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
    scopehook: ScopeHook | None = None

    side_effects: tuple["CallableInfo[typing.Any]", ...] = ()

    _logger: Logger = field(default=get_logger("types.CallableInfo"), init=False, repr=False)

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
        self._logger.debug(
            "Building %svalues for %r using arguments: arguments=(%d items) keyword=(%d items)",
            "partial " if partial else "",
            self.call,
            len(args),
            len(kwargs),
        )

        values: dict[str, typing.Any] = {}

        args_amount = len(args)

        ix = 0
        for parameter in self.parameters:
            name = parameter.name

            if parameter.keyword_varying:
                self._logger.debug("Parameter **%s got value %r", name, kwargs)
                values[name] = kwargs
                continue

            if name in kwargs:
                value = kwargs.pop(name)
                self._logger.debug("Parameter %s got value %r", name, value)
                values[name] = value
                continue

            if parameter.positional_varying:
                value = args[ix:]
                self._logger.debug("Parameter *%s got value %r", name, value)
                values[name] = value
                ix = args_amount
                continue

            if ix < args_amount:
                value = args[ix]
                self._logger.debug("Parameter %s got value %r", name, value)
                values[name] = value
                ix += 1
                continue

            if parameter.has_default:
                self._logger.debug("Parameter %s got value (default) %r", name, parameter.default)
                values[name] = parameter.default
                continue

            self._logger.debug("Parameter %s got no value", name)

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
        self._logger.debug("Building arguments for %r using values: %r", self.call, values)

        positional: tuple[typing.Any, ...] = ()
        keyword: dict[str, typing.Any] = {}

        for parameter in self.parameters:
            name = parameter.name

            if name not in values:
                raise ValueError(f'Value for "{name}" parameter not found')

            value = values[name]

            if parameter.positional_only:
                self._logger.debug("Adding positional-only %s argument: %r", name, value)
                positional += (value,)
            elif parameter.positional_varying:
                self._logger.debug("Adding *%s argument: %r", name, value)
                positional += value
            elif parameter.keyword_only:
                self._logger.debug("Adding keyword-only %s argument: %r", name, value)
                keyword[name] = value
            elif parameter.keyword_varying:
                self._logger.debug("Adding **%s argument: %r", name, value)
                keyword.update(value)
            else:
                self._logger.debug("Adding %s argument: %r", name, value)
                positional += (value,)

        self._logger.debug("Built arguments for %r: %r %r", self.call, positional, keyword)

        return positional, keyword

    def copy(self, deep: bool = False, **update: typing.Any):
        if not deep:
            self._logger.debug("Making shallow copy of %r", self.call)
            return replace(self, **update)

        self._logger.debug("Making deep copy of %r", self.call)
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
