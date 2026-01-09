import typing
from dataclasses import dataclass

from fundi import CallableInfo, scan
from fundi.exceptions import InvalidInitialValue


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


@dataclass
class TypeFactory(typing.Generic[T]):
    """Marker type. Should be used to determine whether this value is a factory or instance of the type"""

    factory: CallableInfo[T]


@dataclass
class TypeInstance(typing.Generic[T]):
    """Marker type. Should be used to determine whether this value is a factory or instance of the type"""

    instance: T


class Scope:
    """
    Injection scope.
    Stores and resolves dynamic values.

    Created to extend resolving mechanism with more features.

    Allows to store values by string keys, types, MROs.
    Also, allows to create type factories - functions that create instances of the type.
    """

    def __init__(self, initial: dict[str | type, typing.Any] | None = None):
        """
        Create the Scope.

        If the key of the ``initial`` is the string then the value is stored under that key.

        If the key is the type then the value is checked whether it is ``TypeInstance`` or ``TypeFactory``.
        If the value is the ``TypeInstance`` - it is stored as instance of the type from key.
        If the value is the ``TypeFactory`` - it is stored as factory of the type from key.
        """
        initial = initial or {}

        self.values: dict[str, typing.Any] = {}
        self.types: dict[type, typing.Any] = {}
        self.factories: dict[type, CallableInfo[typing.Any]] = {}

        for key, value in initial.items():
            if isinstance(key, str):
                self.values[key] = value
                continue

            match value:
                case TypeInstance(instance):
                    self.types[key] = instance
                case TypeFactory(factory):
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

        Returns nothing.
        """
        if isinstance(instance, NoValue):
            type_ = type(type_or_instance)
            instance = type_or_instance

        elif isinstance(type_or_instance, tuple):
            for type_ in type_or_instance:
                self.types[type_] = instance
            return None

        elif isinstance(type_or_instance, type):
            type_ = type_or_instance
            instance = instance

        else:
            raise ValueError("Unable to detect type or value of the assignment")

        self.types[type_] = instance

        if mro:
            for type_ in type_.mro()[1:-1]:
                self.types[type_] = instance

    def add_factory(
        self, type_: type[T] | tuple[type[T], ...], factory: typing.Callable[..., T]
    ) -> None:
        """
        Adds factory of the type to the scope.
        The factory can be any function that can be interpeted as a dependant.

        If the ``type_`` is the tuple of types then the factory is set for each type of that tuple.

        Returns nothing.
        """
        if isinstance(type_, tuple):
            for type_ in type_:
                self.factories[type_] = scan(factory)
            return

        self.factories[type_] = scan(factory)

    def resolve_by_name(self, key: str, *, default: typing.Any = NO_VALUE) -> typing.Any | NoValue:
        """
        Resolves value by the key name.

        Returns either value or the default.
        The default is set to ``NoValue`` instance as the value may be None in the scope.
        """
        return self.values.get(key, default)

    def resolve_by_type(
        self, type_: type[T], default: T | NoValue = NO_VALUE
    ) -> TypeInstance[T] | TypeFactory[T] | T | NoValue:
        """
        Resolves value or factory by the provided type.

        Returns value wrapped in ``TypeInstance``, factory wrapped in ``TypeFactory`` or the default value.
        The default is set to ``NoValue`` instance as the value may be None in the scope.

        Resolution order: instance of the type -> type factory -> default value
        """
        if type_ in self.types:
            return TypeInstance(self.types[type_])

        if type_ in self.factories:
            return TypeFactory(self.factories[type_])

        return default

    @classmethod
    def from_legacy(cls: type[T], scope: dict[str, typing.Any]) -> T:
        initial: dict[str | type, typing.Any] = {}

        for key, value in scope.items():
            initial[key] = value

            if type(value) in IGNORE_TYPES:
                continue

            initial[type(value)] = TypeInstance(value)

        return cls(initial)
