from types import TracebackType
from contextlib import ExitStack, AsyncExitStack

from fundi.hooks import with_hooks
from fundi.types import InjectionTrace
from fundi import from_, scan, inject, ainject, injection_trace, Parameter, FromType


def test_inject_sync():
    def dep():
        pass

    def func(arg: int, arg1: str, arg2: None = from_(dep)) -> str:
        assert arg == 1
        assert arg1 == "value"
        assert arg2 is None

        return "result"

    with ExitStack() as stack:
        result = inject({"arg": 1, "arg1": "value"}, scan(func), stack)

        assert result == "result"


def test_inject_sync_generator():
    dependency_state = None

    def dep():
        nonlocal dependency_state
        dependency_state = "started"
        yield 111
        dependency_state = "finished"

    def func(arg: int, arg1: str, arg2: int = from_(dep)) -> str:
        assert dependency_state == "started"

        assert arg == 1
        assert arg1 == "value"
        assert arg2 == 111

        return "result"

    with ExitStack() as stack:
        assert dependency_state is None
        result = inject({"arg": 1, "arg1": "value"}, scan(func), stack)

        assert result == "result"

    assert dependency_state == "finished"


async def test_inject_async():
    async def dep():
        pass

    async def func(arg: int, arg1: str, arg2: None = from_(dep)) -> str:
        assert arg == 1
        assert arg1 == "value"
        assert arg2 is None

        return "result"

    async with AsyncExitStack() as stack:
        result = await ainject({"arg": 1, "arg1": "value"}, scan(func), stack)

        assert result == "result"


async def test_inject_async_generator():
    dependency_state = None

    async def dep():
        nonlocal dependency_state
        dependency_state = "started"
        yield 111
        dependency_state = "finished"

    async def func(arg: int, arg1: str, arg2: int = from_(dep)) -> str:
        assert dependency_state == "started"

        assert arg == 1
        assert arg1 == "value"
        assert arg2 == 111

        return "result"

    async with AsyncExitStack() as stack:
        assert dependency_state is None
        result = await ainject({"arg": 1, "arg1": "value"}, scan(func), stack)

        assert result == "result"

    assert dependency_state == "finished"


def test_inject_cached():
    def dep() -> type:
        return type("unique type", (object,), {})

    def application(unique_type: type = from_(dep), unique_type1: type = from_(dep)):
        return unique_type is unique_type1

    with ExitStack() as stack:
        is_the_same_type = inject({}, scan(application), stack)

        assert is_the_same_type is True


def test_inject_uncached():
    def dep() -> type:
        return type("unique type", (object,), {})

    def application(unique_type: type = from_(dep), unique_type1: type = from_(dep, caching=False)):
        return unique_type is unique_type1

    with ExitStack() as stack:
        is_the_same_type = inject({}, scan(application), stack)

        assert is_the_same_type is False


def test_injection_trace():
    def dep():
        raise RuntimeError()

    def application(value=from_(dep)): ...

    with ExitStack() as stack:
        try:
            inject({}, scan(application), stack)
        except RuntimeError as exc:
            trace = injection_trace(exc)

            assert isinstance(trace, InjectionTrace)

            assert trace.info.call is application

            assert trace.origin is not None
            assert trace.origin.info.call is dep


def test_injection_trace_values():
    def dep(arg: str):
        raise RuntimeError()

    def application(app_name: str, value=from_(dep)): ...

    try:
        with ExitStack() as stack:
            inject({"arg": "string", "app_name": "Kuyu's App"}, scan(application), stack)
    except RuntimeError as exc:
        trace = injection_trace(exc)

        assert isinstance(trace, InjectionTrace)

        assert trace.info.call is application
        assert trace.values == {"app_name": "Kuyu's App"}

        dep_trace = trace.origin

        assert dep_trace is not None

        assert dep_trace.info.call is dep
        assert dep_trace.values == {"arg": "string"}


def test_generator_exception_awareness():
    dependency_state = None

    def dep():
        nonlocal dependency_state
        dependency_state = "started"
        try:
            yield 111
            dependency_state = "finished"
        except RuntimeError:
            dependency_state = "failed"

    def func(arg: int, arg1: str, arg2: int = from_(dep)) -> str:
        assert dependency_state == "started"

        assert arg == 1
        assert arg1 == "value"
        assert arg2 == 111

        raise RuntimeError()

    try:
        with ExitStack() as stack:
            assert dependency_state is None
            inject({"arg": 1, "arg1": "value"}, scan(func), stack)
    except RuntimeError:
        assert True
    else:
        assert False  # This should never happen

    assert dependency_state == "failed"


def test_dependency_parameter_awareness():
    def dep(param: FromType[Parameter]) -> str:
        assert param.name == "arg"
        assert param.annotation is str

        return "value"

    def func(arg: str = from_(dep)):
        assert arg == "value"

    with ExitStack() as stack:
        inject({}, scan(func), stack)


def test_positional_only():
    def dep(arg: str, /):
        return arg

    with ExitStack() as stack:
        result = inject({"arg": "argValue"}, scan(dep), stack)

        assert result == "argValue"


def test_keyword_only():
    def dep(*, arg: str):
        return arg

    with ExitStack() as stack:
        result = inject({"arg": "argValue"}, scan(dep), stack)

        assert result == "argValue"


def test_context():
    class dep:
        def __init__(self, name: str):
            self.name = name

        def __enter__(self):
            return self.name

        def __exit__(
            self,
            exc_type: type[BaseException] | None,
            exc_val: BaseException | None,
            exc_tb: TracebackType | None,
        ):
            return False

    with ExitStack() as stack:
        result = inject({"name": "context"}, scan(dep), stack)
        assert result == "context"


async def test_async_context():
    class dep:
        def __init__(self, name: str):
            self.name = name

        async def __aenter__(self):
            return self.name

        async def __aexit__(
            self,
            exc_type: type[BaseException] | None,
            exc_val: BaseException | None,
            exc_tb: TracebackType | None,
        ):
            return False

    async with AsyncExitStack() as stack:
        result = await ainject({"name": "context"}, scan(dep), stack)
        assert result == "context"


def test_sync_no_stack():
    states = []

    def dependency():
        states.append("start")
        yield "result"
        states.append("end")

    result = inject({}, scan(dependency))
    assert result == "result"

    assert states == ["start", "end"]


async def test_async_no_stack():
    states = []

    async def dependency():
        states.append("start")
        yield "result"
        states.append("end")

    result = await ainject({}, scan(dependency))
    assert result == "result"

    assert states == ["start", "end"]


def test_scope_hook():
    @with_hooks(scope=lambda scope, _: scope.update(value="Hook value"))
    def dependency(value: str):
        assert value == "Hook value"

    inject({}, scan(dependency))
