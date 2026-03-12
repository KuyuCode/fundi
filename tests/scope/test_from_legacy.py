from fundi.scope import Scope


def test_fundamental_types():
    legacy = {
        "int": 1,
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
    scope = Scope.from_legacy(legacy)

    assert scope.factories == {}
    assert scope.types == {}
    assert scope.values == legacy


def test_custom_types():
    class User:
        pass

    legacy = {"user": User()}
    scope = Scope.from_legacy(legacy)

    assert scope.values == legacy
    assert scope.types == {User: legacy["user"]}
    assert scope.factories == {}
