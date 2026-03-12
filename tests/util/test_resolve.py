from fundi.scope import Scope
from fundi import resolve, from_, scan, exceptions, FromType


def test_resolve_sync():
    def dep():
        pass

    def func(arg: int, arg1: str, arg2: None = from_(dep)):
        pass

    for result in resolve(Scope.from_legacy({"arg": 1, "arg1": "value"}), scan(func), {}):
        if not result.resolved:
            assert result.dependency is not None
            assert result.dependency.call is dep

        if result.resolved:
            assert result.parameter.name in ("arg", "arg1")

            if result.parameter.name == "arg1":
                assert result.value == "value"

            if result.parameter.name == "arg":
                assert result.value == 1


def test_resolve_async():
    async def dep():
        pass

    async def func(arg: int, arg1: str, arg2: None = from_(dep)):
        pass

    for result in resolve(Scope.from_legacy({"arg": 1, "arg1": "value"}), scan(func), {}):
        if not result.resolved:
            assert result.dependency is not None
            assert result.dependency.call is dep

        if result.resolved:
            assert result.parameter.name in ("arg", "arg1")

            if result.parameter.name == "arg1":
                assert result.value == "value"

            if result.parameter.name == "arg":
                assert result.value == 1


def test_resolve_by_type():
    class EventHandler:
        pass

    def dep():
        pass

    # Using from_ on type tells resolver that it should search value in scope by type, not parameter name
    def func(arg: int, arg1: str, handler: from_(EventHandler)):
        pass

    event_handler = EventHandler()

    for result in resolve(
        Scope.from_legacy({"arg": 1, "arg1": "value", "+1": event_handler}), scan(func), {}
    ):
        assert result.parameter.name in ("arg", "arg1", "handler")

        if result.parameter.name == "arg1":
            assert result.value == "value"

        if result.parameter.name == "arg":
            assert result.value == 1

        if result.parameter.name == "handler":
            assert result.value is event_handler


# noinspection PyPep8Naming
def test_resolve_by_type_using_FromType():
    class EventHandler:
        pass

    def dep():
        pass

    # Using from_ on type tells resolver that it should search value in scope by type, not parameter name
    def func(arg: int, arg1: str, handler: FromType[EventHandler]):
        pass

    event_handler = EventHandler()

    for result in resolve(
        Scope.from_legacy({"arg": 1, "arg1": "value", "+1": event_handler}), scan(func), {}
    ):
        assert result.parameter.name in ("arg", "arg1", "handler")

        if result.parameter.name == "arg1":
            assert result.value == "value"

        if result.parameter.name == "arg":
            assert result.value == 1

        if result.parameter.name == "handler":
            assert result.value is event_handler


def test_override_result():
    def dep(): ...

    def func(arg: int = from_(dep)): ...

    for result in resolve(Scope(), scan(func), {}, override={dep: 2}):
        assert result.parameter.name == "arg"

        assert result.value == 2


def test_override_dependency():
    def dep(): ...

    def test_dep(): ...

    def func(arg: int = from_(dep)): ...

    for result in resolve(Scope(), scan(func), {}, override={dep: scan(test_dep)}):
        assert result.parameter.name == "arg"

        assert result.resolved is False

        assert result.dependency
        assert result.dependency.call is test_dep


def test_resolve_not_found():
    def func(arg: int): ...

    try:
        for result in resolve(Scope(), scan(func), {}):
            # This assertion would never evaluate under normal circumstances
            assert result is None
    except exceptions.ScopeValueNotFoundError as exc:
        assert exc.parameter == "arg"
        assert exc.info.call is func
