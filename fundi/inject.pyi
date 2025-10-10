import typing
from typing import overload
from collections.abc import Generator, AsyncGenerator, Mapping, MutableMapping, Awaitable

from fundi.types import CacheKey, CallableInfo

from contextlib import (
    AbstractAsyncContextManager,
    ExitStack as SyncExitStack,
    AbstractContextManager,
    AsyncExitStack,
)

R = typing.TypeVar("R")

ExitStack = AsyncExitStack | SyncExitStack

def injection_impl(
    scope: Mapping[str, typing.Any],
    info: CallableInfo[typing.Any],
    cache: MutableMapping[CacheKey, typing.Any],
    override: Mapping[typing.Callable[..., typing.Any], typing.Any] | None,
) -> Generator[
    tuple[Mapping[str, typing.Any], CallableInfo[typing.Any], bool],
    typing.Any,
    None,
]: ...
@overload
def inject(
    scope: Mapping[str, typing.Any],
    info: CallableInfo[Generator[R, None, None]],
    stack: ExitStack | None = None,
    cache: MutableMapping[CacheKey, typing.Any] | None = None,
    override: Mapping[typing.Callable[..., typing.Any], typing.Any] | None = None,
) -> R: ...
@overload
def inject(
    scope: Mapping[str, typing.Any],
    info: CallableInfo[AbstractContextManager[R]],
    stack: ExitStack | None = None,
    cache: MutableMapping[CacheKey, typing.Any] | None = None,
    override: Mapping[typing.Callable[..., typing.Any], typing.Any] | None = None,
) -> R: ...
@overload
def inject(
    scope: Mapping[str, typing.Any],
    info: CallableInfo[R],
    stack: ExitStack | None = None,
    cache: MutableMapping[CacheKey, typing.Any] | None = None,
    override: Mapping[typing.Callable[..., typing.Any], typing.Any] | None = None,
) -> R: ...
@overload
async def ainject(
    scope: Mapping[str, typing.Any],
    info: CallableInfo[Generator[R, None, None]],
    stack: AsyncExitStack | None = None,
    cache: MutableMapping[CacheKey, typing.Any] | None = None,
    override: Mapping[typing.Callable[..., typing.Any], typing.Any] | None = None,
) -> R: ...
@overload
async def ainject(
    scope: Mapping[str, typing.Any],
    info: CallableInfo[AsyncGenerator[R, None]],
    stack: AsyncExitStack | None = None,
    cache: MutableMapping[CacheKey, typing.Any] | None = None,
    override: Mapping[typing.Callable[..., typing.Any], typing.Any] | None = None,
) -> R: ...
@overload
async def ainject(
    scope: Mapping[str, typing.Any],
    info: CallableInfo[Awaitable[R]],
    stack: AsyncExitStack | None = None,
    cache: MutableMapping[CacheKey, typing.Any] | None = None,
    override: Mapping[typing.Callable[..., typing.Any], typing.Any] | None = None,
) -> R: ...
@overload
async def ainject(
    scope: Mapping[str, typing.Any],
    info: CallableInfo[AbstractAsyncContextManager[R]],
    stack: AsyncExitStack | None = None,
    cache: MutableMapping[CacheKey, typing.Any] | None = None,
    override: Mapping[typing.Callable[..., typing.Any], typing.Any] | None = None,
) -> R: ...
@overload
async def ainject(
    scope: Mapping[str, typing.Any],
    info: CallableInfo[AbstractContextManager[R]],
    stack: AsyncExitStack | None = None,
    cache: MutableMapping[CacheKey, typing.Any] | None = None,
    override: Mapping[typing.Callable[..., typing.Any], typing.Any] | None = None,
) -> R: ...
@overload
async def ainject(
    scope: Mapping[str, typing.Any],
    info: CallableInfo[R],
    stack: AsyncExitStack | None = None,
    cache: MutableMapping[CacheKey, typing.Any] | None = None,
    override: Mapping[typing.Callable[..., typing.Any], typing.Any] | None = None,
) -> R: ...
