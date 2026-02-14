import typing
from itertools import chain
from dataclasses import dataclass
from collections.abc import Mapping, Callable

from typing_extensions import NewType, overload, override

from fundi import scan
from fundi.exceptions import InvalidInitialValue

if typing.TYPE_CHECKING:
    from fundi import CallableInfo


class NoValue:
    """
    No value marker. Do not use this as a value!
    """


IGNORE_TYPES: tuple[type, ...] = (
    int,
    str,
    set,
    bool,
    dict,
    list,
    type,
    float,
    bytes,
    tuple,
    object,
    bytearray,
)

NO_VALUE = NoValue()

T = typing.TypeVar("T")
S = typing.TypeVar("S", bound="Scope")


class Type:
    """
    Marker group. Markers of this group should be used to distinguish factories and instances for the given type.

    Convenient when used with match-statement:

    match scope.resolve_by_type(User):
        case Type.Instance(value):
            value = value
        case Type.Factory(factory):
            value = inject(scope, factory)
        case _:
            raise ValueError(f"No value found for {User}")
    """

    @dataclass
    class Factory(typing.Generic[T]):
        """Marker type. Wraps the factory of the type and should be used to distinguish the factory from instance"""

        factory: "CallableInfo[T]"

    @dataclass
    class Instance(typing.Generic[T]):
        """Marker type. Wraps the instance of the type and should be used to distinguish the instance from the factory"""

        instance: T

    @staticmethod
    def factory(
        factory_callable: Callable[..., T],
        caching: bool = False,
        async_: bool | None = None,
        generator: bool | None = None,
        context: bool | None = None,
        use_return_annotation: bool = True,
        side_effects: tuple[Callable[..., typing.Any], ...] = (),
    ) -> Factory[T]:
        return Type.Factory(
            scan(
                factory_callable,
                caching=caching,
                async_=async_,
                generator=generator,
                context=context,
                use_return_annotation=use_return_annotation,
                side_effects=side_effects,
            )
        )

    @staticmethod
    def instance(instance: T) -> Instance[T]:
        return Type.Instance(instance)


class Scope:
    """
    Injection scope.
    Stores and resolves dynamic values.

    Created to extend resolving mechanism with more features.

    Allows to store values by string keys, types, MROs.
    Also, allows to create type factories - functions that create instances of the type.
    """

    def __init__(self, initial: dict[str | type | NewType, typing.Any] | None = None):
        """
        Create the Scope.

        If the key of the ``initial`` is the string then the value is stored under that key.

        If the key is the type then the value is checked whether it is ``TypeInstance`` or ``TypeFactory``.
        If the value is the ``TypeInstance`` - it is stored as instance of the type from key.
        If the value is the ``TypeFactory`` - it is stored as factory of the type from key.
        """
        initial = initial or {}

        self.values: dict[str, typing.Any] = {}
        self.types: dict[type | NewType, typing.Any] = {}
        self.factories: dict[type | NewType, "CallableInfo[typing.Any]"] = {}

        for key, value in initial.items():
            if isinstance(key, str):
                self.values[key] = value
                continue

            match value:
                case Type.Instance(instance):
                    self.types[key] = instance
                case Type.Factory(factory):
                    self.factories[key] = factory
                case value:
                    raise InvalidInitialValue(value)

    def add_value(self, key: str, value: typing.Any) -> bool:
        """
        Adds named value to the scope.

        Returns True if the value replaced existing one.
        """
        if key in self.values:
            self.values[key] = value
            return True

        self.values[key] = value
        return False

    def add_type(
        self,
        type_or_instance: typing.Any,
        instance: typing.Any = NO_VALUE,
        mro: bool = False,
    ) -> None:
        """
        Adds value by type to the scope.

        If ``instance`` is not provided -
        uses ``type_or_instance`` as the instance and takes its type as the key.

        If ``type_or_instance`` is a tuple of types then each of the values is used as key for the ``instance`` and
        ``mro`` parameter is disabled.

        If mro is True - adds this value by type and type's MRO(method resolution order)
        ignoring last entry in the list.

        If a factory for the given type already exists, it is removed —
        an instance always takes precedence over a factory.

        Returns nothing.
        """
        if isinstance(instance, NoValue):
            type_ = type(type_or_instance)
            instance = type_or_instance

        elif isinstance(type_or_instance, tuple):
            for type_ in type_or_instance:
                self.types[type_] = instance
            return None

        elif isinstance(type_or_instance, (type, NewType)):
            type_ = type_or_instance
            instance = instance

        else:
            raise ValueError("Unable to detect type or value of the assignment")

        if type_ in self.factories:
            del self.factories[type_]

        self.types[type_] = instance

        if mro:
            for type_ in type_.mro()[1:-1]:
                if type_ in self.factories:
                    del self.factories[type_]
                self.types[type_] = instance

    @overload
    def add_factory(
        self, type_: NewType | tuple[type[T], ...], factory: typing.Callable[..., T]
    ) -> None: ...
    @overload
    def add_factory(
        self, type_: type[T] | tuple[type[T], ...], factory: typing.Callable[..., T]
    ) -> None: ...
    def add_factory(
        self, type_: type[T] | tuple[type[T], ...], factory: typing.Callable[..., T]
    ) -> None:
        """
        Adds factory of the type to the scope.
        The factory can be any function that can be interpeted as a dependant.

        If the ``type_`` is the tuple of types then the factory is set for each type of that tuple.

        If an instance for the given type already exists, it is removed —
        a factory cannot coexist with an instance.

        Returns nothing.
        """
        if isinstance(type_, tuple):
            for type_ in type_:
                self.factories[type_] = scan(factory)
            return

        if type_ in self.types:
            del self.types[type_]

        self.factories[type_] = scan(factory)

    def update(
        self,
        mapping: (
            Mapping[
                str | type | NewType,
                Type.Instance[typing.Any] | Type.Factory[typing.Any] | typing.Any,
            ]
            | None
        ) = None,
        **values: typing.Any,
    ):
        """
        Update this scope with provided values.

        ``mapping`` argument can be used to add multiple factories and type instances at a time.
        And ``values`` argument can be used only for string based values.

        When adding a type instance, any existing factory for that type is removed.
        When adding a type factory, any existing instance for that type is removed.
        """
        self.values.update(values)

        if mapping is None:
            return None

        for key, value in mapping.items():
            if isinstance(key, str):
                self.values[key] = value
                continue

            match value:
                case Type.Instance(value):
                    if key in self.factories:
                        del self.factories[key]
                    self.types[key] = value
                case Type.Factory(factory):
                    if key in self.types:
                        del self.types[key]
                    self.factories[key] = factory

    def resolve_by_name(self, key: str, *, default: typing.Any = NO_VALUE) -> typing.Any | NoValue:
        """
        Resolves value by the key name.

        Returns either value or the default.
        The default is set to ``NoValue`` instance as the value may be None in the scope.
        """
        return self.values.get(key, default)

    @overload
    def resolve_by_type(
        self, type_: NewType, default: T | NoValue = NO_VALUE
    ) -> Type.Instance[typing.Any] | Type.Factory[typing.Any] | T | NoValue: ...
    @overload
    def resolve_by_type(
        self, type_: type[T], default: T | NoValue = NO_VALUE
    ) -> Type.Instance[T] | Type.Factory[T] | NoValue: ...
    def resolve_by_type(
        self, type_: typing.Any, default: typing.Any = NO_VALUE
    ) -> Type.Instance[typing.Any] | Type.Factory[typing.Any] | NoValue | typing.Any:
        """
        Resolves value or factory by the provided type.

        Returns value wrapped in ``TypeInstance``, factory wrapped in ``TypeFactory`` or the default value.
        The default is set to ``NoValue`` instance as the value may be None in the scope.

        Resolution order: instance of the type -> type factory -> default value
        """
        if type_ in self.types:
            return Type.Instance(self.types[type_])

        if type_ in self.factories:
            return Type.Factory(self.factories[type_])

        return default

    def merge(self, other: "Scope") -> "Scope":
        """
        Merges two scopes together and returns the result as the new Scope instance.

        If the method detects confict of type instance and type factories -
        the type factories with conflicts are being discarded
        """
        new_scope = Scope()
        new_scope.values = {**self.values, **other.values}
        new_scope.types = {**self.types, **other.types}
        new_scope.factories = {
            type_: factory
            for type_, factory in chain(self.factories.items(), other.factories.items())
            if type_ not in new_scope.types
        }

        return new_scope

    def copy(self) -> "Scope":
        """
        Make a copy of this scope
        """
        scope = Scope()
        scope.values = self.values.copy()
        scope.types = self.types.copy()
        scope.factories = self.factories.copy()
        return scope

    def simplify(self):
        """
        Return simple representation of this scope that can be used in the Scope constructor
        """
        return (
            self.values
            | {t: Type.Instance(ti) for t, ti in self.types.items()}
            | {t: Type.Factory(f) for t, f in self.factories.items()}
        )

    @classmethod
    def from_legacy(cls: typing.Callable[[], S], scope: Mapping[str, typing.Any]) -> S:
        """
        Makes the `Scope` instance from the legacy dictionary based scope
        """
        new_scope = cls()

        for key, value in scope.items():
            new_scope.values[key] = value

            value_type = type(value)
            if value_type in IGNORE_TYPES or getattr(value_type, "__module__", None) == "builtins":
                continue

            new_scope.types[value_type] = value

        return new_scope

    __or__ = merge

    @overload
    def __getitem__(self, key: type[T]) -> Type.Instance[T] | Type.Factory[T]: ...
    @overload
    def __getitem__(self, key: NewType) -> Type.Instance[typing.Any] | Type.Factory[typing.Any]: ...
    @overload
    def __getitem__(self, key: str) -> typing.Any: ...
    def __getitem__(self, key: typing.Any) -> typing.Any:
        """
        Get the value for the ``key``.

        If the ``key`` is a ``type`` or ``NewType`` instance tries to
        lookup for value using ``resolve_by_type`` method

        If it is the string - uses ``resolve_by_name`` method
        """
        value = NO_VALUE
        match key:
            case str():
                value = self.resolve_by_name(key)

            case type() | NewType():
                value = self.resolve_by_type(key)

        if value is NO_VALUE:
            raise KeyError(key)

        return value

    def __contains__(self, key: str | type[typing.Any] | NewType) -> bool:
        """
        Check if the `key` is in this `Scope` in following order:
        named values -> typed instances -> typed factories
        """
        return key in self.values or key in self.types or key in self.factories

    @override
    def __str__(self):
        return f"Scope{{named={len(self.values)}, by_type={len(self.types)}, factories={len(self.factories)}}}"
