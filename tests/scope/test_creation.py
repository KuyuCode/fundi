import pytest

from fundi import scan
from fundi.exceptions import InvalidInitialValue
from fundi.scope import Scope, TypeInstance, TypeFactory


def test_fundamental_types_only():
    initial = {
        "int": 1,
        "float": 1.1,
        "str": "",
        "bytes": b"",
        "bytearray": bytearray(),
        "set": set(),
        "dict": {},
        "list": [],
        "tuple": (),
        "bool": True,
        "object": object(),
        "type": object,
    }
    scope = Scope(initial)

    assert scope.values == initial
    assert scope.types == {}
    assert scope.factories == {}


def test_custom_type_without_marker():
    class User:
        pass

    initial = {User: User()}

    with pytest.raises(InvalidInitialValue):
        Scope(initial)


def test_custom_type_with_marker():
    class User:
        pass

    initial = {User: TypeInstance(User())}

    scope = Scope(initial)

    assert scope.values == {}
    assert scope.types == {User: initial[User].instance}
    assert scope.factories == {}


def test_factory_without_marker():
    class User:
        pass

    def factory() -> User:
        return User()

    initial = {User: scan(factory)}

    with pytest.raises(InvalidInitialValue):
        Scope(initial)


def test_factory_with_marker():
    class User:
        pass

    def factory() -> User:
        return User()

    initial = {User: TypeFactory(scan(factory))}

    scope = Scope(initial)

    assert scope.values == {}
    assert scope.types == {}
    assert scope.factories == {User: initial[User].factory}
