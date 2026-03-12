import typing
from typing_extensions import NewType

from fundi import scan
from fundi.scope import Scope, Type


def test_replace():
    class AClass:
        pass

    class BClass:
        pass

    def factory0():
        pass

    def factory1():
        pass

    initial: dict[str | type | NewType, typing.Any] = {
        "key": "value",
        AClass: Type.instance(1),
        BClass: Type.factory(factory0),
    }

    scope = Scope(initial)
    scope1 = Scope(
        {"key": "another value", AClass: Type.instance(2), BClass: Type.factory(factory1)}
    )

    scope_merged = scope | scope1

    assert scope_merged.values == {"key": "another value"}
    assert scope_merged.types == {AClass: 2}
    assert scope_merged.factories == {BClass: scan(factory1)}


def test_extend():
    class AClass:
        pass

    class BClass:
        pass

    def factory0():
        pass

    scope = Scope({"base_key": "initial value"})

    scope1 = Scope({"key": "value", AClass: Type.instance(1), BClass: Type.factory(factory0)})

    scope_merged = scope | scope1

    assert scope_merged.values == {"key": "value", "base_key": "initial value"}
    assert scope_merged.types == {AClass: 1}
    assert scope_merged.factories == {BClass: scan(factory0)}
