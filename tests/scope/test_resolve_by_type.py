from typing import NewType
from fundi import scan
from fundi.scope import Scope, NO_VALUE, TypeInstance, TypeFactory


def test_exact():
    class User:
        pass

    initial = {User: TypeInstance(User())}
    scope = Scope(initial)

    value = scope.resolve_by_type(User)
    assert isinstance(value, TypeInstance)
    assert value.instance is initial[User].instance
    assert isinstance(value.instance, User)


def test_no_value():
    scope = Scope()

    assert scope.resolve_by_type(type) is NO_VALUE


def test_mro():
    class User:
        pass

    class Admin(User):
        pass

    admin = Admin()

    scope = Scope()
    scope.add_type(admin, mro=True)

    value = scope.resolve_by_type(User)
    assert isinstance(value, TypeInstance)
    assert value.instance is admin
    assert isinstance(value.instance, User) and isinstance(value.instance, Admin)


def test_alias():
    class User:
        pass

    Actor = NewType("Actor", User)

    user = User()

    initial = {Actor: TypeInstance(user)}
    scope = Scope(initial)

    value = scope.resolve_by_type(Actor)
    assert isinstance(value, TypeInstance)
    assert value.instance is user
    assert isinstance(value.instance, User)


def test_factory():
    class User:
        pass

    def factory() -> User:
        return User()

    initial = {User: TypeFactory(scan(factory))}
    scope = Scope(initial)

    value = scope.resolve_by_type(User)

    assert isinstance(value, TypeFactory)
    assert value.factory.call is factory
