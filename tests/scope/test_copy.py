from fundi import scan
from fundi.scope import TypeInstance, TypeFactory, Scope


def test_default():
    initial = {
        "key": "value",
        int: TypeInstance(2),  # noqa: F821
        str: TypeFactory(scan(lambda: "string")),  # noqa: F821
        "another key": "another value",
    }
    scope = Scope(initial)

    copy = scope.copy()

    assert copy.values == scope.values
    assert copy.types == scope.types
    assert copy.factories == scope.factories
