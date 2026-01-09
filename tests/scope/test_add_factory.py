from fundi import scan
from typing import NewType
from fundi.scope import Scope


def test_default():
    class User:
        pass

    def factory() -> User:
        return User()

    scope = Scope()
    scope.add_factory(User, factory)

    assert scope.factories == {User: scan(factory)}


def test_alias():

    class User:
        pass

    def factory() -> User:
        return User()

    Actor = NewType("Actor", User)

    scope = Scope()
    scope.add_factory(Actor, factory)

    assert scope.factories == {Actor: scan(factory)}
