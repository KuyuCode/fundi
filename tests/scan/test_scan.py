import typing
import inspect
import functools
from typing import Callable
from types import TracebackType

from fundi.configurable import configurable_dependency
from fundi import scan, from_, FromType, virtual_context
from fundi.types import CallableInfo, DependencyConfiguration, Parameter


def test_scan_no_deps():
    def func(arg: int): ...

    info = scan(func)

    assert info.async_ is False
    assert info.generator is False
    assert info.call is func

    assert info.parameters == [Parameter("arg", int, None)]


def test_scan_deps():
    def dep() -> int: ...

    dep_info = scan(dep)

    def func(arg: int = from_(dep)): ...

    info = scan(func)

    assert info.async_ is False
    assert info.generator is False
    assert info.call is func
    assert info.parameters == [Parameter("arg", int, dep_info)]


def test_scan_generator_no_deps():
    def func(arg: int):
        yield arg

    info = scan(func)

    assert info.async_ is False
    assert info.generator is True
    assert info.call is func

    assert info.parameters == [Parameter("arg", int, None)]


def test_scan_generator_deps():
    def dep() -> int: ...

    dep_info = scan(dep)

    def func(arg: int = from_(dep)):
        yield arg

    info = scan(func)

    assert info.async_ is False
    assert info.generator is True
    assert info.call is func
    assert info.parameters == [Parameter("arg", int, dep_info)]


def test_scan_async_no_deps():
    async def func(arg: int):  # noqa
        pass

    info = scan(func)

    assert info.async_ is True
    assert info.generator is False
    assert info.call is func

    assert info.parameters == [Parameter("arg", int, None)]


def test_scan_async_deps():
    def dep() -> int:
        pass

    dep_info = scan(dep)

    async def func(arg: int = from_(dep)):  # noqa
        pass

    info = scan(func)

    assert info.async_ is True
    assert info.generator is False
    assert info.call is func
    assert info.parameters == [Parameter("arg", int, dep_info)]


def test_scan_async_generator_no_deps():
    async def func(arg: int):
        yield arg

    info = scan(func)

    assert info.async_ is True
    assert info.generator is True
    assert info.call is func

    assert info.parameters == [Parameter("arg", int, None)]


def test_scan_async_generator_deps():
    def dep() -> int: ...

    dep_info = scan(dep)

    async def func(arg: int = from_(dep)):
        yield arg

    info = scan(func)

    assert info.async_ is True
    assert info.generator is True
    assert info.call is func
    assert info.parameters == [Parameter("arg", int, dep_info)]


# noinspection PyPep8Naming
def test_scan_FromType():
    class Session: ...

    def dep(arg: FromType[Session]): ...

    info = scan(dep)

    assert info.async_ is False
    assert info.generator is False
    assert info.call is dep
    assert info.parameters == [Parameter("arg", FromType[Session], None, resolve_by_type=True)]


def test_scan_positional_only():
    def dep(arg: str, /): ...

    info = scan(dep)

    assert info.async_ is False
    assert info.generator is False
    assert info.call is dep
    assert info.parameters == [
        Parameter("arg", str, None, positional_only=True),
    ]


def test_scan_keyword_only():
    def dep(*, arg: str): ...

    info = scan(dep)

    assert info.async_ is False
    assert info.generator is False
    assert info.call is dep
    assert info.parameters == [Parameter("arg", str, None, keyword_only=True)]


def test_scan_configured():
    @configurable_dependency
    def dep_factory(multiplier: int):
        return lambda rank: rank * multiplier

    info = scan(dep_factory(17032026))

    assert info.async_ is False
    assert info.generator is False
    assert info.call is dep_factory(17032026)
    assert info.parameters == [Parameter("rank", inspect.Parameter.empty, None)]
    assert info.configuration is not None
    assert info.configuration == DependencyConfiguration(
        configurator=scan(inspect.unwrap(dep_factory)), values={"multiplier": 17032026}
    )


def test_scan_context():
    class dep:
        def __init__(self, name: str):
            pass

        def __enter__(self):
            return "value"

        def __exit__(
            self,
            exc_type: type[BaseException] | None,
            exc_val: BaseException | None,
            exc_tb: TracebackType | None,
        ):
            return False

    info = scan(dep)

    assert info.async_ is False
    assert info.generator is False
    assert info.context is True
    assert info.call is dep
    assert info.parameters == [Parameter("name", str, None)]


def test_scan_async_context():
    class dep:
        def __init__(self, name: str):
            pass

        async def __aenter__(self):
            return "value"

        async def __aexit__(
            self,
            exc_type: type[BaseException] | None,
            exc_val: BaseException | None,
            exc_tb: TracebackType | None,
        ):
            return False

    info = scan(dep)

    assert info.async_ is True
    assert info.generator is False
    assert info.context is True
    assert info.call is dep
    assert info.parameters == [Parameter("name", str, None)]


def test_scan_virtual_context():
    @virtual_context
    def dep(name: str):
        yield name

    info = scan(dep)

    assert info.async_ is False
    assert info.generator is False
    assert info.context is True
    assert info.call is dep
    assert info.parameters == [Parameter("name", str, None)]


def test_scan_async_virtual_context():
    @virtual_context
    async def dep(name: str):
        yield name

    info = scan(dep)

    assert info.async_ is True
    assert info.generator is False
    assert info.context is True
    assert info.call is dep
    assert info.parameters == [Parameter("name", str, None)]


def test_scan_vararg():
    def dep(*args: int): ...

    info = scan(dep)

    assert info.parameters == [Parameter("args", int, None, positional_varying=True)]


def test_scan_varkw():
    def dep(**kwargs: int): ...

    info = scan(dep)

    assert info.parameters == [Parameter("kwargs", int, None, keyword_varying=True)]


def test_scan_override_context():
    import contextlib

    @contextlib.contextmanager
    def dep():
        yield None

    info = scan(dep, context=True)

    assert info.context is True


def test_scan_override_async():
    import asyncio

    def dep():
        return asyncio.Future()

    info = scan(dep, async_=True)

    assert info.async_ is True


def test_scan_override_generator():
    def generator():
        yield 1

    def dep():
        return generator()

    info = scan(dep, generator=True)

    assert info.generator is True


def test_scan_infer_context():
    import contextlib

    def dep() -> contextlib.AbstractContextManager: ...

    info = scan(dep)

    assert info.context is True

    def dep() -> contextlib.AbstractAsyncContextManager: ...

    info = scan(dep)

    assert info.context is True


def test_scan_infer_generator():
    import collections.abc as C

    def dep() -> C.Generator: ...

    info = scan(dep)

    assert info.generator is True

    def dep() -> C.AsyncGenerator: ...

    info = scan(dep)

    assert info.generator is True


def test_scan_infer_generator():
    import asyncio
    import contextlib
    import collections.abc as C

    def dep() -> asyncio.Future: ...

    info = scan(dep)

    assert info.async_ is True

    def dep() -> contextlib.AbstractAsyncContextManager: ...

    info = scan(dep)

    assert info.async_ is True

    def dep() -> C.AsyncGenerator: ...

    info = scan(dep)

    assert info.async_ is True


def test_scan_with_None_typehint():
    def dep() -> None: ...

    info = scan(dep)

    assert info.async_ is False
    assert info.generator is False
    assert info.context is False


def test_scan_Annotated_dependency():
    from typing import Annotated

    def dep() -> int: ...

    def dependant(value: Annotated[int, from_(dep)]): ...

    info = scan(dependant)

    assert info.parameters[0].from_ is not None
    assert info.parameters[0].from_.call is dep


def test_scan_graphhook():
    def hook(ci: CallableInfo[typing.Any], parameter: Parameter):
        ci.key.add(parameter.name)
        return ci

    from fundi.hooks import with_hooks

    @with_hooks(hook)
    def dependency():
        return 1

    def dependant(value: int = from_(dependency)): ...

    info = scan(dependant)

    parameter = info.parameters[0]

    assert parameter.from_ is not None
    assert parameter.from_.key._items == [dependency, "value"]
