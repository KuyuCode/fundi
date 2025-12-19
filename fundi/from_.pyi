import typing
from typing import overload
from collections.abc import Generator, AsyncGenerator, Awaitable
from contextlib import AbstractAsyncContextManager, AbstractContextManager

T = typing.TypeVar("T", bound=type)
# Send
S = typing.TypeVar("S")
# Yield
Y = typing.TypeVar("Y")
# Return
R = typing.TypeVar("R")

@overload
def from_(
    dependency: typing.Callable[..., AbstractContextManager[R]],
    caching: bool = True,
    async_: bool | None = None,
    generator: bool | None = None,
    context: bool | None = None,
    use_return_annotation: bool = True,
) -> R: ...
@overload
def from_(
    dependency: typing.Callable[..., AbstractAsyncContextManager[R]],
    caching: bool = True,
    async_: bool | None = None,
    generator: bool | None = None,
    context: bool | None = None,
    use_return_annotation: bool = True,
) -> R: ...
@overload
def from_(dependency: T, caching: bool = True) -> T: ...
@overload
def from_(
    dependency: typing.Callable[..., Generator[R, None, None]],
    caching: bool = True,
    async_: bool | None = None,
    generator: typing.Literal[True] | None = None,
    context: bool | None = None,
    use_return_annotation: bool = True,
) -> R: ...
@overload
def from_(
    dependency: typing.Callable[..., AsyncGenerator[R, None]],
    caching: bool = True,
    async_: bool | None = None,
    generator: typing.Literal[True] | None = None,
    context: bool | None = None,
    use_return_annotation: bool = True,
) -> R: ...
@overload
def from_(
    dependency: typing.Callable[..., Generator[Y, S, R]],
    caching: bool = True,
    async_: bool | None = None,
    generator: typing.Literal[False] = False,
    context: bool | None = None,
    use_return_annotation: bool = True,
) -> Generator[Y, S, R]: ...
@overload
def from_(
    dependency: typing.Callable[..., AsyncGenerator[Y, S]],
    caching: bool = True,
    async_: bool | None = None,
    generator: typing.Literal[False] = False,
    context: bool | None = None,
    use_return_annotation: bool = True,
) -> AsyncGenerator[Y, S]: ...
@overload
def from_(
    dependency: typing.Callable[..., Awaitable[R]],
    caching: bool = True,
    async_: bool | None = None,
    generator: bool | None = None,
    context: bool | None = None,
    use_return_annotation: bool = True,
) -> R: ...
@overload
def from_(
    dependency: typing.Callable[..., R],
    caching: bool = True,
    async_: bool | None = None,
    generator: bool | None = None,
    context: bool | None = None,
    use_return_annotation: bool = True,
) -> R: ...
