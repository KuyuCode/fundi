from fundi import scan
from fundi.scope import Scope, TypeInstance, TypeFactory


def test_default():
    initial = {
        "key": "value",
        int: TypeInstance(2),
        str: TypeFactory(scan(lambda: "string")),
        "another key": "another value",
    }
    scope = Scope(initial)

    simplified = scope.simplify()
    assert simplified == initial
