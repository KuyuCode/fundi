from fundi.scope import Scope, Type


def test_default():
    initial = {
        "key": "value",
        int: Type.instance(2),
        str: Type.factory(lambda: "string"),
        "another key": "another value",
    }
    scope = Scope(initial)

    simplified = scope.simplify()
    assert simplified == initial
