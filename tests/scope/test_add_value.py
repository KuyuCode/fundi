from fundi.scope import Scope


def test_default():
    scope = Scope()
    scope.add_value("name", "Kuyugama")

    assert scope.values == {"name": "Kuyugama"}

    assert scope.resolve_by_name("name") == "Kuyugama"
