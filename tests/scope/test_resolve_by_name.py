from fundi.scope import Scope, NO_VALUE


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

    assert scope.resolve_by_name("constant") is constant


def test_invalid_name():
    initial = {"name": -1}

    scope = Scope(initial)

    assert scope.resolve_by_name("invalid-name") is NO_VALUE
