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
from typing_extensions import Self
from contextlib import AsyncExitStack, ExitStack
from collections.abc import Mapping, MutableMapping

from .scope import Scope
from .inject import ainject, inject
from .types import CacheKey, CallableInfo


def _validate_scope(scope: Scope | Mapping[str, typing.Any] | None) -> Scope:
    if not isinstance(scope, Scope):
        scope = Scope.from_legacy(scope or {})
    else:
        scope = scope.copy()

    return scope


class InjectionContext:
    """
    Synchronous injection context.
    Allows only synchronous dependencies of all kinds to be injected.
    """

    def __init__(
        self,
        scope: Mapping[str, typing.Any] | Scope | None = None,
        cache: MutableMapping[CacheKey, typing.Any] | None = None,
        override: Mapping[typing.Callable[..., typing.Any], typing.Any] | None = None,
    ) -> None:
        self.scope: Scope = _validate_scope(scope)

        self.cache: dict[CacheKey, typing.Any] = {**cache} if cache is not None else {}

        self.override: dict[typing.Callable[..., typing.Any], typing.Any] = (
            {**override} if override is not None else {}
        )

        self.stack: ExitStack = ExitStack()

    def inject(
        self,
        info: CallableInfo[typing.Any],
        scope: Mapping[str, typing.Any] | Scope | None = None,
        override: Mapping[typing.Callable[..., typing.Any], typing.Any] | None = None,
        no_cache: bool = False,
    ):
        """
        Inject dependency within injection context.
        This function uses scope, cache, stack and overrides defined in the context.

        Scope is modified before injection.
        It is merged with provided scope via argument
        and ``{'__fundi_injection_context__': self.sub()}``

        Overrides are also merged with provided
        ``override`` argument before injection.

        If ``no_cache`` is ``True`` then - cache is not used.
        This includes reads and writes to cache.
        """
        override = override or {}
        cache: MutableMapping[CacheKey, typing.Any] = {} if no_cache else self.cache

        scope = self.scope | _validate_scope(scope)
        scope.add_factory(lambda: self.sub(scope), InjectionContext)

        return inject(
            scope,
            info,
            self.stack,
            cache,
            {**self.override, **override},
        )

    def sub(
        self,
        scope: Mapping[str, typing.Any] | Scope | None = None,
        override: Mapping[typing.Callable[..., typing.Any], typing.Any] | None = None,
        no_cache: bool = False,
    ) -> "InjectionContext":
        """
        Create copy of this injection context and
        connect it to the lifecycle of this context.

        Scope is merged with provided ``scope`` argument.

        Overrides are also merged with provided
        ``override`` argument.

        If ``no_cache`` is ``True`` then - cache is not copied.
        """
        return self.stack.enter_context(self.copy(scope, override, no_cache))

    def copy(
        self,
        scope: Mapping[str, typing.Any] | Scope | None = None,
        override: Mapping[typing.Callable[..., typing.Any], typing.Any] | None = None,
        no_cache: bool = False,
    ) -> "InjectionContext":
        """
        Create copy of this injection context.

        Scope is merged with provided ``scope`` argument.

        Overrides are also merged with provided
        ``override`` argument.

        If ``no_cache`` is ``True`` then - cache is not copied.
        """
        scope = _validate_scope(scope)
        override = override or {}
        cache: MutableMapping[CacheKey, typing.Any] = {} if no_cache else {**self.cache}

        return InjectionContext(self.scope | scope, cache, {**self.override, **override})

    def close(self):
        """
        End lifecycle of this injection context
        """
        self.stack.close()

    def __enter__(self) -> Self:
        """
        Start lifecycle of this injection context.
        Does nothing, as ``AsyncExitStack.__aenter__`` is empty. (CPython 3.10-3.14)
        """
        self.stack.__enter__()
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ):
        """
        End lifecycle of this injection context.
        this closes all pending lifespan-dependencies.

        If context-manager is closing due to exception -
        exceptions are raised inside pending dependencies.
        """
        return self.stack.__exit__(exc_type, exc_value, traceback)


class AsyncInjectionContext:
    """
    Synchronous injection context.
    Allows both synchronous and asynchronous dependencies of all kinds to be injected.
    """

    def __init__(
        self,
        scope: Mapping[str, typing.Any] | Scope | None = None,
        cache: MutableMapping[CacheKey, typing.Any] | None = None,
        override: Mapping[typing.Callable[..., typing.Any], typing.Any] | None = None,
    ) -> None:
        self.scope: Scope = _validate_scope(scope)

        self.cache: dict[CacheKey, typing.Any] = {**cache} if cache is not None else {}

        self.override: dict[typing.Callable[..., typing.Any], typing.Any] = (
            {**override} if override is not None else {}
        )

        self.stack: AsyncExitStack = AsyncExitStack()

    async def inject(
        self,
        info: CallableInfo[typing.Any],
        scope: Mapping[str, typing.Any] | Scope | None = None,
        override: Mapping[typing.Callable[..., typing.Any], typing.Any] | None = None,
        no_cache: bool = False,
    ):
        """
        Inject dependency within injection context.
        This function uses scope, cache, stack and overrides defined in the context.

        Scope is modified before injection.
        It is merged with provided scope via argument
        and ``{'__fundi_injection_context__': self.sub()}``

        Overrides are also merged with provided
        ``override`` argument before injection.

        If ``no_cache`` is ``True`` then - cache is not used.
        This includes reads and writes to cache.
        """
        override = override or {}
        cache: MutableMapping[CacheKey, typing.Any] = {} if no_cache else self.cache

        scope = self.scope | _validate_scope(scope)

        async def factory() -> AsyncInjectionContext:
            return await self.sub(scope)

        scope.add_factory(factory, AsyncInjectionContext, use_return_annotation=False)

        return await ainject(
            scope,
            info,
            self.stack,
            cache,
            {**self.override, **override},
        )

    async def sub(
        self,
        scope: Mapping[str, typing.Any] | Scope | None = None,
        override: Mapping[typing.Callable[..., typing.Any], typing.Any] | None = None,
        no_cache: bool = False,
    ) -> "AsyncInjectionContext":
        """
        Create copy of this injection context and
        connect it to the lifecycle of this context.

        Scope is merged with provided ``scope`` argument.

        Overrides are also merged with provided
        ``override`` argument.

        If ``no_cache`` is ``True`` then - cache is not copied.
        """
        return await self.stack.enter_async_context(self.copy(scope, override, no_cache))

    def copy(
        self,
        scope: Mapping[str, typing.Any] | Scope | None = None,
        override: Mapping[typing.Callable[..., typing.Any], typing.Any] | None = None,
        no_cache: bool = False,
    ) -> "AsyncInjectionContext":
        """
        Create copy of this injection context.

        Scope is merged with provided ``scope`` argument.

        Overrides are also merged with provided
        ``override`` argument.

        If ``no_cache`` is ``True`` then - cache is not copied.
        """
        scope = _validate_scope(scope)
        override = override or {}
        cache: MutableMapping[CacheKey, typing.Any] = {} if no_cache else {**self.cache}

        return AsyncInjectionContext(self.scope | scope, cache, {**self.override, **override})

    async def close(self) -> None:
        """
        End lifecycle of this injection context
        """
        await self.stack.aclose()

    async def __aenter__(self) -> Self:
        """
        Start lifecycle of this injection context.
        Does nothing, as ``AsyncExitStack.__aenter__`` is empty. (CPython 3.10-3.14)
        """
        await self.stack.__aenter__()
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> bool | None:
        """
        End lifecycle of this injection context.
        this closes all pending lifespan-dependencies.

        If context-manager is closing due to exception -
        exceptions are raised inside pending dependencies.
        """
        return await self.stack.__aexit__(exc_type, exc_value, traceback)
