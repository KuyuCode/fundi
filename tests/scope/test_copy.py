from fundi import scan
from fundi.scope import Type, Scope


def test_default():
    initial = {
        "key": "value",
        int: Type.Instance(2),  # noqa: F821
        str: Type.Factory(scan(lambda: "string")),  # noqa: F821
        "another key": "another value",
    }
    scope = Scope(initial)

    copy = scope.copy()

    assert copy.values == scope.values
    assert copy.types == scope.types
    assert copy.factories == scope.factories
