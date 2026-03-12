from fundi import scan
from fundi.scope import Scope, Type


def test_default():
    scope = Scope()
    scope.update(some="value")

    assert scope.values == {"some": "value"}
    assert scope.types == {}
    assert scope.factories == {}


def test_type_instances():
    scope = Scope()
    scope.update({int: Type.instance(2)})

    assert scope.values == {}
    assert scope.types == {int: 2}
    assert scope.factories == {}


def test_type_factories():
    scope = Scope()
    factory = scan(lambda: 1)
    scope.update({int: Type.Factory(factory)})

    assert scope.values == {}
    assert scope.types == {}
    assert scope.factories == {int: factory}
