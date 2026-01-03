import typing
from types import TracebackType
from typing_extensions import Self, overload
from collections.abc import Mapping, MutableMapping, Generator, AsyncGenerator, Awaitable

from .types import CacheKey, CallableInfo

from contextlib import (
    ExitStack,
    AsyncExitStack,
    AbstractContextManager,
    AbstractAsyncContextManager,
)

R = typing.TypeVar("R")

class InjectionContext:
    scope: dict[str, typing.Any]
    cache: dict[CacheKey, typing.Any]
    override: dict[typing.Callable[..., typing.Any], typing.Any]
    stack: ExitStack

    def __init__(
        self,
        scope: Mapping[str, typing.Any] | None = None,
        cache: MutableMapping[CacheKey, typing.Any] | None = None,
        override: Mapping[typing.Callable[..., typing.Any], typing.Any] | None = None,
    ) -> None:
        self.scope: dict[str, typing.Any] = {**scope} if scope is not None else {}

        self.cache: dict[CacheKey, typing.Any] = {**cache} if cache is not None else {}

        self.override: dict[typing.Callable[..., typing.Any], typing.Any] = (
            {**override} if override is not None else {}
        )

        self.stack: ExitStack = ExitStack()

    def sub(
        self,
        scope: Mapping[str, typing.Any] | None = None,
        override: Mapping[typing.Callable[..., typing.Any], typing.Any] | None = None,
        no_cache: bool = False,
    ) -> "InjectionContext": ...
    def copy(
        self,
        scope: Mapping[str, typing.Any] | None = None,
        override: Mapping[typing.Callable[..., typing.Any], typing.Any] | None = None,
        no_cache: bool = False,
    ) -> "InjectionContext": ...
    def close(self) -> None: ...
    def __enter__(self) -> Self: ...
    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> bool | None: ...
    @overload
    def inject(
        self,
        info: CallableInfo[Generator[R, None, None]],
        scope: Mapping[str, typing.Any] | None = None,
        override: Mapping[typing.Callable[..., typing.Any], typing.Any] | None = None,
        no_cache: bool = False,
    ) -> R: ...
    @overload
    def inject(
        self,
        info: CallableInfo[AbstractContextManager[R]],
        scope: Mapping[str, typing.Any] | None = None,
        override: Mapping[typing.Callable[..., typing.Any], typing.Any] | None = None,
        no_cache: bool = False,
    ) -> R: ...
    @overload
    def inject(
        self,
        info: CallableInfo[R],
        scope: Mapping[str, typing.Any] | None = None,
        override: Mapping[typing.Callable[..., typing.Any], typing.Any] | None = None,
        no_cache: bool = False,
    ) -> R: ...
    def inject(
        self,
        info: CallableInfo[typing.Any],
        scope: Mapping[str, typing.Any] | None = None,
        override: Mapping[typing.Callable[..., typing.Any], typing.Any] | None = None,
        no_cache: bool = False,
    ): ...

class AsyncInjectionContext:
    scope: dict[str, typing.Any]
    cache: dict[CacheKey, typing.Any]
    override: dict[typing.Callable[..., typing.Any], typing.Any]
    stack: AsyncExitStack

    def __init__(
        self,
        scope: Mapping[str, typing.Any] | None = None,
        cache: MutableMapping[CacheKey, typing.Any] | None = None,
        override: Mapping[typing.Callable[..., typing.Any], typing.Any] | None = None,
    ) -> None: ...
    async def sub(
        self,
        scope: Mapping[str, typing.Any] | None = None,
        override: Mapping[typing.Callable[..., typing.Any], typing.Any] | None = None,
        no_cache: bool = False,
    ) -> "AsyncInjectionContext": ...
    def copy(
        self,
        scope: Mapping[str, typing.Any] | None = None,
        override: Mapping[typing.Callable[..., typing.Any], typing.Any] | None = None,
        no_cache: bool = False,
    ) -> "AsyncInjectionContext": ...
    async def close(self) -> None: ...
    async def __aenter__(self) -> Self: ...
    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> bool | None: ...
    @overload
    async def inject(
        self,
        info: CallableInfo[Generator[R, None, None]],
        scope: Mapping[str, typing.Any] | None = None,
        override: Mapping[typing.Callable[..., typing.Any], typing.Any] | None = None,
        no_cache: bool = False,
    ) -> R: ...
    @overload
    async def inject(
        self,
        info: CallableInfo[AsyncGenerator[R, None]],
        scope: Mapping[str, typing.Any] | None = None,
        override: Mapping[typing.Callable[..., typing.Any], typing.Any] | None = None,
        no_cache: bool = False,
    ) -> R: ...
    @overload
    async def inject(
        self,
        info: CallableInfo[Awaitable[R]],
        scope: Mapping[str, typing.Any] | None = None,
        override: Mapping[typing.Callable[..., typing.Any], typing.Any] | None = None,
        no_cache: bool = False,
    ) -> R: ...
    @overload
    async def inject(
        self,
        info: CallableInfo[AbstractAsyncContextManager[R]],
        scope: Mapping[str, typing.Any] | None = None,
        override: Mapping[typing.Callable[..., typing.Any], typing.Any] | None = None,
        no_cache: bool = False,
    ) -> R: ...
    @overload
    async def inject(
        self,
        info: CallableInfo[AbstractContextManager[R]],
        scope: Mapping[str, typing.Any] | None = None,
        override: Mapping[typing.Callable[..., typing.Any], typing.Any] | None = None,
        no_cache: bool = False,
    ) -> R: ...
    async def inject(
        self,
        info: CallableInfo[R],
        scope: Mapping[str, typing.Any] | None = None,
        override: Mapping[typing.Callable[..., typing.Any], typing.Any] | None = None,
        no_cache: bool = False,
    ) -> R: ...
