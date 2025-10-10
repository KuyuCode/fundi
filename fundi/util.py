import types
import typing
import inspect
import warnings
import contextlib
import collections.abc
from types import TracebackType

from fundi.types import CallableInfo, InjectionTrace, DependencyConfiguration


__all__ = [
    "call_sync",
    "call_async",
    "callable_str",
    "is_configured",
    "injection_trace",
    "get_configuration",
    "add_injection_trace",
    "normalize_annotation",
]


def callable_str(call: typing.Callable[..., typing.Any]) -> str:
    if hasattr(call, "__qualname__"):
        name = call.__qualname__
    elif hasattr(call, "__name__"):
        name = call.__name__
    else:
        name = str(call)

    module = inspect.getmodule(call)

    module_name = "<unknown>" if module is None else module.__name__

    return f"<{name} from {module_name}>"


def add_injection_trace(
    exception: Exception,
    info: CallableInfo[typing.Any],
    values: collections.abc.Mapping[str, typing.Any],
) -> None:
    setattr(
        exception,
        "__fundi_injection_trace__",
        InjectionTrace(info, values, getattr(exception, "__fundi_injection_trace__", None)),
    )


def call_sync(
    stack: contextlib.ExitStack | contextlib.AsyncExitStack,
    info: CallableInfo[typing.Any],
    values: collections.abc.Mapping[str, typing.Any],
) -> typing.Any:
    """
    Synchronously call dependency callable.

    :param stack: exit stack to properly handle generator dependencies
    :param info: callable information
    :param values: callable arguments
    :return: callable result
    """
    args, kwargs = info.build_arguments(values)
    value = info.call(*args, **kwargs)

    if info.context:
        manager: contextlib.AbstractContextManager[typing.Any] = value
        value = manager.__enter__()

        def exit_context(
            exc_type: type[BaseException] | None,
            exc_value: BaseException | None,
            tb: TracebackType | None,
        ) -> bool:
            try:
                manager.__exit__(exc_type, exc_value, tb)
            except Exception as e:
                # Do not include re-raise of this exception in traceback to make it cleaner
                if e is exc_value:
                    return False

                raise

            # DO NOT ALLOW LIFESPAN DEPENDENCIES TO IGNORE EXCEPTIONS
            return exc_type is None

        stack.push(exit_context)

    if info.generator:
        generator: collections.abc.Generator[typing.Any, None, None] = value
        value = next(generator)

        def close_generator(
            exc_type: type[BaseException] | None,
            exc_value: BaseException | None,
            tb: TracebackType | None,
        ) -> bool:
            try:
                if exc_type is not None:
                    generator.throw(exc_type, exc_value, tb)
                else:
                    next(generator)
            except StopIteration:
                # DO NOT ALLOW LIFESPAN DEPENDENCIES TO IGNORE EXCEPTIONS
                return exc_type is None
            except Exception as e:
                # Do not include re-raise of this exception in traceback to make it cleaner
                if e is exc_value:
                    return False

                raise

            warnings.warn("Generator not exited", UserWarning)

            # DO NOT ALLOW LIFESPAN DEPENDENCIES TO IGNORE EXCEPTIONS
            return exc_type is None

        stack.push(close_generator)

    return value


async def call_async(
    stack: contextlib.AsyncExitStack,
    info: CallableInfo[typing.Any],
    values: collections.abc.Mapping[str, typing.Any],
) -> typing.Any:
    """
    Asynchronously call dependency callable.

    :param stack: exit stack to properly handle generator dependencies
    :param info: callable information
    :param values: callable arguments
    :return: callable result
    """
    args, kwargs = info.build_arguments(values)

    value = info.call(*args, **kwargs)

    if info.context:
        manager: contextlib.AbstractAsyncContextManager[typing.Any] = value
        value = await manager.__aenter__()

        async def exit_context(
            exc_type: type[BaseException] | None,
            exc_value: BaseException | None,
            tb: TracebackType | None,
        ) -> bool:
            try:
                await manager.__aexit__(exc_type, exc_value, tb)
            except Exception as e:
                # Do not include re-raise of this exception in traceback to make it cleaner
                if e is exc_value:
                    return False

                raise

            # DO NOT ALLOW LIFESPAN DEPENDENCIES TO IGNORE EXCEPTIONS
            return exc_type is None

        stack.push_async_exit(exit_context)

    elif info.generator:
        generator: collections.abc.AsyncGenerator[typing.Any] = value
        value = await anext(generator)

        async def close_generator(
            exc_type: type[BaseException] | None,
            exc_value: BaseException | None,
            tb: TracebackType | None,
        ) -> bool:
            try:
                if exc_type is not None:
                    await generator.athrow(exc_type, exc_value, tb)
                else:
                    await anext(generator)
            except StopAsyncIteration:
                # DO NOT ALLOW LIFESPAN DEPENDENCIES TO IGNORE EXCEPTIONS
                return exc_type is None
            except Exception as e:
                # Do not include re-raise of this exception in traceback to make it cleaner
                if e is exc_value:
                    return False

                raise

            warnings.warn("Generator not exited", UserWarning)

            # DO NOT ALLOW LIFESPAN DEPENDENCIES TO IGNORE EXCEPTIONS
            return exc_type is None

        stack.push_async_exit(close_generator)

    else:
        value = await value

    return value


def injection_trace(exception: Exception) -> InjectionTrace:
    """
    Get injection trace from exception

    :param exception: exception to get injection trace from
    :return: injection trace
    """
    if not hasattr(exception, "__fundi_injection_trace__"):
        raise ValueError(f"Exception {exception} does not contain injection trace")

    return typing.cast(InjectionTrace, getattr(exception, "__fundi_injection_trace__"))


def is_configured(call: typing.Callable[..., typing.Any]) -> bool:
    """
    Get whether callable is configured via @configurable_dependency

    :param call: callable to check
    :return: Is this callable configured
    """
    return hasattr(call, "__fundi_configuration__")


def get_configuration(call: typing.Callable[..., typing.Any]) -> DependencyConfiguration:
    """
    Get dependency configuration. Can be useful in third-party tools that needs to know configuration

    :param call: callable to get configuration from
    :return: dependency configuration
    """
    if not is_configured(call):
        raise ValueError(f"Callable {call} is not configured via @configurable_dependency")

    configuration: DependencyConfiguration = getattr(call, "__fundi_configuration__")
    return configuration


def normalize_annotation(annotation: typing.Any) -> tuple[typing.Any, ...]:
    """
    Normalize type annotation to make it easily work with
    """
    type_options: tuple[type, ...] = (annotation,)

    origin = typing.get_origin(annotation)
    args = typing.get_args(annotation)

    if origin is typing.Annotated:
        annotation = args[0]
        type_options = (annotation,)
        origin = typing.get_origin(annotation)
        args = typing.get_args(annotation)

    if origin is types.UnionType:
        type_options = tuple(t for t in args if t is not types.NoneType)
    elif origin is not None:
        type_options = (origin,)

    return type_options


Target = typing.TypeVar("Target")
P = typing.ParamSpec("P")


def combine_hooks(*hooks: typing.Callable[P, typing.Any]) -> typing.Callable[P, None]:
    """
    Combine multiple hooks together.

    All hooks will be called with the same parameters.

    It is useful for combining hooks that mutate object itself, not produce new one

    For example it can be used in FunDI graph hook to update CallableInfo's caching key::

        from fundi.hooks import with_hooks

        @with_hooks(
            graph=combine_hooks(
                lambda ci, param: ci.key.add(param.name),
                lambda ci, _: ci.key.add("custom value")
            )
        )
        def dependency(...): ...
    """

    def hook(*args: P.args, **kwargs: P.kwargs) -> None:
        for instruction in hooks:
            instruction(*args, **kwargs)

        return None

    return hook
