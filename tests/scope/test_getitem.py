import pytest
from typing_extensions import NewType

from fundi.scope import Scope, Type


def test_exact():
    class User:
        pass

    initial = {User: Type.instance(User())}
    scope = Scope(initial)

    value = scope[User]
    assert isinstance(value, Type.Instance)
    assert value.instance is initial[User].instance
    assert isinstance(value.instance, User)


def test_no_value():
    scope = Scope()

    with pytest.raises(KeyError):
        scope[type]


def test_mro():
    class User:
        pass

    class Admin(User):
        pass

    admin = Admin()

    scope = Scope()
    scope.add_type(admin, mro=True)

    value = scope[User]
    assert isinstance(value, Type.Instance)
    assert value.instance is admin
    assert isinstance(value.instance, User) and isinstance(value.instance, Admin)


def test_alias():
    class User:
        pass

    Actor = NewType("Actor", User)

    user = User()

    initial = {Actor: Type.instance(user)}
    scope = Scope(initial)

    value = scope[Actor]
    assert isinstance(value, Type.Instance)
    assert isinstance(value.instance, User)
    assert value.instance is user


def test_factory():
    class User:
        pass

    def factory() -> User:
        return User()

    initial = {User: Type.factory(factory)}
    scope = Scope(initial)

    value = scope[User]

    assert isinstance(value, Type.Factory)
    assert value.factory.call is factory


def test_valid_name():
    constant = 1

    initial = {
        "constant": constant,
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

    assert scope["constant"] is constant


def test_invalid_name():
    initial = {"name": -1}

    scope = Scope(initial)

    with pytest.raises(KeyError):
        scope["invalid-name"]
