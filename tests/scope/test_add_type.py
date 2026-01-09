from typing import NewType
from fundi.scope import Scope


def test_default():
    class User:
        pass

    user = User()

    scope = Scope()
    scope.add_type(user)

    assert scope.types == {User: user}


def test_mro():
    class User:
        pass

    class Admin(User):
        pass

    admin = Admin()

    scope = Scope()
    scope.add_type(admin, mro=True)

    assert scope.types == {User: admin, Admin: admin}


def test_alias():
    class User:
        pass

    Actor = NewType("Actor", User)

    user = User()

    scope = Scope()
    scope.add_type(Actor, user)

    assert scope.types == {Actor: user}
