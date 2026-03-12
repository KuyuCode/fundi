import pytest
from typing import NewType
from fundi.scope import Scope, Type


def test_default():
    class User:
        pass

    def factory() -> User:
        return User()

    scope = Scope()
    scope.add_factory(factory, User)

    assert scope.factories[User].call is factory


def test_alias():
    class User:
        pass

    def factory() -> User:
        return User()

    Actor = NewType("Actor", User)

    scope = Scope()
    scope.add_factory(factory, Actor)

    assert scope.factories[Actor].call is factory


def test_type_inference():
    class User:
        pass

    def factory() -> User:
        return User()

    scope = Scope()
    scope.add_factory(factory)

    assert scope.factories[User].call is factory


def test_type_inference_fails():
    def factory():
        return "peace"

    scope = Scope()
    with pytest.raises(ValueError, match="Unable to identify return type of the factory"):
        scope.add_factory(factory)


def test_scan_params():
    class User:
        pass

    def factory() -> User:
        return User()

    scope = Scope()
    scope.add_factory(factory, caching=True)

    assert scope.factories[User].use_cache is True


def test_conflict_resolution():
    class User:
        pass

    def factory() -> User:
        return User()

    scope = Scope({User: Type.instance(User())})
    assert User in scope.types

    scope.add_factory(factory)

    assert User not in scope.types
    assert User in scope.factories

