"""
Injection contexts allow you to share scope, cache, overrides and lifecycle
between multiple injections.

Example::

    with InjectionContext({"global_": 10}) as ctx:
        ctx.inject(scan(lambda global_: print(global_))) # 10
        ctx.scope["global_"] = 20 # update context scope

        # Create sub context which will be closed automatically with parent
        sub = ctx.sub()
        sub.inject(scan(lambda global_: print(global_))) # 20

        # Injection nesting
        def dependant(sub: FromType[InjectionContext]):
            # context passed into dependencies is the sub context of the context
            # it was called with
            assert sub != ctx
            sub.inject(scan(another_dependant))

        ctx.inject(scan(dependant))

        # Create context copy, it will not be closed automatically
        with ctx.copy() as copy:
            inject(scan(lambda global_: print(global_))) # 20
"""

import typing
from types import TracebackType
from contextlib import AsyncExitStack, ExitStack
from collections.abc import Mapping, MutableMapping

from .inject import ainject, inject
from .types import CacheKey, CallableInfo


class InjectionContext:
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

    def inject(
        self,
        info: CallableInfo[typing.Any],
        scope: Mapping[str, typing.Any] | None = None,
        override: Mapping[typing.Callable[..., typing.Any], typing.Any] | None = None,
        no_cache: bool = False,
    ):
        scope = scope or {}
        override = override or {}
        cache: MutableMapping[CacheKey, typing.Any] = {} if no_cache else self.cache

        return inject(
            {**self.scope, **scope, "__fundi_injection_context__": self.sub()},
            info,
            self.stack,
            cache,
            {**self.override, **override},
        )

    def sub(
        self,
        scope: Mapping[str, typing.Any] | None = None,
        override: Mapping[typing.Callable[..., typing.Any], typing.Any] | None = None,
        no_cache: bool = False,
    ):

        return self.stack.enter_context(self.copy(scope, override, no_cache))

    def copy(
        self,
        scope: Mapping[str, typing.Any] | None = None,
        override: Mapping[typing.Callable[..., typing.Any], typing.Any] | None = None,
        no_cache: bool = False,
    ):
        scope = scope or {}
        override = override or {}
        cache: MutableMapping[CacheKey, typing.Any] = {} if no_cache else {**self.cache}

        return InjectionContext({**self.scope, **scope}, cache, {**self.override, **override})

    def close(self):
        self.stack.close()

    def __enter__(self):
        self.stack.__enter__()
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ):
        return self.stack.__exit__(exc_type, exc_value, traceback)


class AsyncInjectionContext:
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

        self.stack: AsyncExitStack = AsyncExitStack()

    async def inject(
        self,
        info: CallableInfo[typing.Any],
        scope: Mapping[str, typing.Any] | None = None,
        override: Mapping[typing.Callable[..., typing.Any], typing.Any] | None = None,
        no_cache: bool = False,
    ):
        scope = scope or {}
        override = override or {}
        cache: MutableMapping[CacheKey, typing.Any] = {} if no_cache else self.cache
        return await ainject(
            {**self.scope, **scope, "__fundi_injection_context__": await self.sub()},
            info,
            self.stack,
            cache,
            {**self.override, **override},
        )

    async def sub(
        self,
        scope: Mapping[str, typing.Any] | None = None,
        override: Mapping[typing.Callable[..., typing.Any], typing.Any] | None = None,
        no_cache: bool = False,
    ):

        return await self.stack.enter_async_context(self.copy(scope, override, no_cache))

    def copy(
        self,
        scope: Mapping[str, typing.Any] | None = None,
        override: Mapping[typing.Callable[..., typing.Any], typing.Any] | None = None,
        no_cache: bool = False,
    ):
        scope = scope or {}
        override = override or {}
        cache: MutableMapping[CacheKey, typing.Any] = {} if no_cache else {**self.cache}

        return AsyncInjectionContext({**self.scope, **scope}, cache, {**self.override, **override})

    async def close(self):
        await self.stack.aclose()

    async def __aenter__(self):
        await self.stack.__aenter__()
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ):
        return await self.stack.__aexit__(exc_type, exc_value, traceback)
