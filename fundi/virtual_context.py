"""
Virtual context managers are created to replace contextlib.contextmanager
and contextlib.asynccontextmanager decorators.
They are fully typed and distinguishable by FunDIs `scan(...)` function
"""

import types
import typing
import inspect
import warnings
from dataclasses import replace
from collections.abc import Generator, AsyncGenerator
from contextlib import AbstractAsyncContextManager, AbstractContextManager

from .scan import scan
from .types import CallableInfo
from fundi.logging import get_logger
from .exceptions import GeneratorExitedTooEarly

__all__ = ["VirtualContextProvider", "AsyncVirtualContextProvider", "virtual_context"]

logger = get_logger("virtual_context")

T = typing.TypeVar("T")
P = typing.ParamSpec("P")
F = typing.TypeVar("F", bound=types.FunctionType)


@typing.final
class _VirtualContextManager(typing.Generic[T], AbstractContextManager[T]):
    """
    Virtual context manager implementation
    """

    def __init__(self, generator: Generator[T, None, None], origin: types.FunctionType) -> None:
        self.generator = generator
        self.origin = origin

    def __enter__(self) -> T:  # pyright: ignore[reportMissingSuperCall, reportImplicitOverride]
        try:
            logger.debug("Entering %r", self.origin)
            return self.generator.send(None)
        except StopIteration as exc:
            raise GeneratorExitedTooEarly(self.origin, self.generator) from exc

    def __exit__(  # pyright: ignore[reportImplicitOverride]
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: types.TracebackType | None,
    ) -> bool:
        try:
            if exc_type is not None:
                logger.debug(
                    "Raising %s in %r: %r",
                    exc_type.__name__ if exc_type else "Unknown",
                    self.origin,
                    exc_value,
                )
                self.generator.throw(exc_type, exc_value, traceback)
            else:
                logger.debug("Exiting %r", self.origin)
                self.generator.send(None)
        except StopIteration:
            logger.debug("Generator %r exited cleanly", self.origin)
        except Exception as exc:
            if exc is exc_value:
                logger.debug(
                    "Generator created by %r re-raised exception %r, suppressing traceback",
                    self.origin,
                    exc_type,
                )
                return False

            raise exc
        else:
            logger.warning("Generator %r did not exit properly", self.origin)
            warnings.warn("Generator not exited", UserWarning)

        return False


@typing.final
class _VirtualAsyncContextManager(typing.Generic[T], AbstractAsyncContextManager[T]):
    """
    Virtual context manager implementation
    """

    def __init__(self, generator: AsyncGenerator[T, None], origin: types.FunctionType) -> None:
        self.generator = generator
        self.origin = origin

    async def __aenter__(self) -> T:  # pyright: ignore[reportImplicitOverride]
        try:
            logger.debug("Entering %r", self.origin)
            return await self.generator.asend(None)
        except StopAsyncIteration as exc:
            raise GeneratorExitedTooEarly(self.origin, self.generator) from exc

    async def __aexit__(  # pyright: ignore[reportImplicitOverride]
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: types.TracebackType | None,
    ) -> bool:
        assert self.generator is not None, "Generator not initialized, call __call__ method first"

        try:
            if exc_type is not None:
                logger.debug(
                    "Raising %s in %r: %r",
                    exc_type.__name__ if exc_type else "Unknown",
                    self.origin,
                    exc_value,
                )
                await self.generator.athrow(exc_type, exc_value, traceback)
            else:
                logger.debug("Exiting %r", self.origin)
                await self.generator.asend(None)
        except StopAsyncIteration:
            logger.debug("Generator %r exited cleanly", self.origin)
        except Exception as exc:
            if exc is exc_value:
                logger.debug(
                    "Generator created by %r re-raised exception %r, suppressing traceback",
                    self.origin,
                    exc_type,
                )
                return False

            raise exc
        else:
            logger.warning("Generator %r did not exit properly", self.origin)
            warnings.warn("Generator not exited", UserWarning)

        return False


class VirtualContextProvider(typing.Generic[T, P]):
    """
    Synchronous virtual context manager
    """

    def __init__(self, function: typing.Callable[P, Generator[T, None, None]]):
        self.__fundi_info__: CallableInfo[typing.Any] = replace(
            scan(function, generator=False, context=True), call=self
        )

        self.__wrapped__: typing.Callable[P, Generator[T, None, None]] = function

    def __call__(self, *args: P.args, **kwargs: P.kwargs):
        logger.debug("Creating virtual context manager for %r", self.__wrapped__)
        return _VirtualContextManager(self.__wrapped__(*args, **kwargs), self.__wrapped__)


class AsyncVirtualContextProvider(typing.Generic[T, P]):
    """
    Asynchronous virtual context manager
    """

    def __init__(self, function: typing.Callable[P, AsyncGenerator[T]]):
        self.__fundi_info__: CallableInfo[typing.Any] = replace(
            scan(function, generator=False, context=True), call=self
        )

        self.__wrapped__: typing.Callable[P, AsyncGenerator[T]] = function

    def __call__(self, *args: P.args, **kwargs: P.kwargs):
        logger.debug("Creating virtual context manager for %r", self.__wrapped__)
        return _VirtualAsyncContextManager(self.__wrapped__(*args, **kwargs), self.__wrapped__)


@typing.overload
def virtual_context(
    function: typing.Callable[P, Generator[T, None, None]],
) -> VirtualContextProvider[T, P]: ...
@typing.overload
def virtual_context(
    function: typing.Callable[P, AsyncGenerator[T]],
) -> AsyncVirtualContextProvider[T, P]: ...
def virtual_context(
    function: typing.Callable[P, Generator[T, None, None] | AsyncGenerator[T]],
) -> VirtualContextProvider[T, P] | AsyncVirtualContextProvider[T, P]:
    """
    Define virtual context manager using decorator

    Example::


        @virtual_context
        def file(name: str):
            file_ = open(name, "r")
            try:
                yield file_
            finally:
                file_.close()


        with file("dontreadthis.txt") as f:
            print(f.read()


        @virtual_context
        async def lock(name: str):
            lock_ = locks[name]
            lock_.acquire()
            try:
                yield
            finally:
                lock_.release()


        async with lock("socket-send"):
            await socket.send("wtf")
    """
    if inspect.isasyncgenfunction(function):
        return AsyncVirtualContextProvider(function)
    elif inspect.isgeneratorfunction(function):
        return VirtualContextProvider(function)

    raise ValueError(
        f"@virtual_context expects a generator or async generator function, got {function!r}"
    )
