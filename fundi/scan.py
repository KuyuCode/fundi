import typing
import inspect
from dataclasses import replace
from types import BuiltinFunctionType, FunctionType, MethodType
from collections.abc import AsyncGenerator, Awaitable, Generator
from contextlib import AbstractAsyncContextManager, AbstractContextManager

from fundi.util import is_configured, get_configuration, normalize_annotation
from fundi.types import R, CallableInfo, Parameter, TypeResolver


def _transform_parameter(parameter: inspect.Parameter) -> Parameter:
    positional_varying = parameter.kind == inspect.Parameter.VAR_POSITIONAL
    positional_only = parameter.kind == inspect.Parameter.POSITIONAL_ONLY
    keyword_varying = parameter.kind == inspect.Parameter.VAR_KEYWORD
    keyword_only = parameter.kind == inspect.Parameter.KEYWORD_ONLY

    if isinstance(parameter.default, CallableInfo):
        return Parameter(
            parameter.name,
            parameter.annotation,
            from_=typing.cast(CallableInfo[typing.Any], parameter.default),
            positional_varying=positional_varying,
            positional_only=positional_only,
            keyword_varying=keyword_varying,
            keyword_only=keyword_only,
        )

    has_default = parameter.default is not inspect.Parameter.empty
    resolve_by_type = False

    annotation = parameter.annotation
    if isinstance(annotation, TypeResolver):
        annotation = annotation.annotation
        resolve_by_type = True

    elif typing.get_origin(annotation) is typing.Annotated:
        args = typing.get_args(annotation)

        if args[1] is TypeResolver:
            resolve_by_type = True

    return Parameter(
        parameter.name,
        annotation,
        from_=None,
        default=parameter.default if has_default else None,
        has_default=has_default,
        resolve_by_type=resolve_by_type,
        positional_varying=positional_varying,
        positional_only=positional_only,
        keyword_varying=keyword_varying,
        keyword_only=keyword_only,
    )


def _is_context(call: typing.Any):
    if isinstance(call, type):
        return issubclass(call, AbstractContextManager)
    else:
        return isinstance(call, AbstractContextManager)


def _is_async_context(call: typing.Any):
    if isinstance(call, type):
        return issubclass(call, AbstractAsyncContextManager)
    else:
        return isinstance(call, AbstractAsyncContextManager)


def scan(
    call: typing.Callable[..., R],
    caching: bool = True,
    async_: bool | None = None,
    generator: bool | None = None,
    context: bool | None = None,
    use_return_annotation: bool = True,
) -> CallableInfo[R]:
    """
    Get callable information

    :param call: callable to get information from
    :param caching:  whether to use cached result of this callable or not
    :param async_: Override "async_" attriubute value
    :param generator: Override "generator" attriubute value
    :param context: Override "context" attriubute value

    :return: callable information
    """

    if hasattr(call, "__fundi_info__"):
        info = typing.cast(CallableInfo[typing.Any], getattr(call, "__fundi_info__"))

        overrides = {"use_cache": caching}
        if async_ is not None:
            overrides["async_"] = async_

        if generator is not None:
            overrides["generator"] = generator

        if context is not None:
            overrides["context"] = context

        return replace(info, **overrides)

    if not callable(call):
        raise ValueError(
            f"Callable expected, got {type(call)!r}"
        )  # pyright: ignore[reportUnreachable]

    truecall = call.__call__
    if isinstance(call, (FunctionType, BuiltinFunctionType, MethodType, type)):
        truecall = call

    signature = inspect.signature(truecall)

    return_ = type
    if signature.return_annotation is not signature.empty:
        return_ = normalize_annotation(signature.return_annotation)[0]

    # WARNING: over-engineered logic!! :3

    _generator: bool = inspect.isgeneratorfunction(truecall)
    _agenerator: bool = inspect.isasyncgenfunction(truecall)
    _context: bool = _is_context(call)
    _acontext: bool = _is_async_context(call)

    # Getting "generator" using return typehint or __code__ flags
    if generator is None:
        generator = (
            use_return_annotation
            and (issubclass(return_, Generator) or issubclass(return_, AsyncGenerator))
        ) or (_generator or _agenerator)

    # Getting "context" using return typehint or callable type
    if context is None:
        context = (
            use_return_annotation
            and (issubclass(return_, (AbstractContextManager, AbstractAsyncContextManager)))
        ) or (_context or _acontext)

    # Getting "async_" using return typehint or __code__ flags or defined above variables
    if async_ is None:
        async_ = (
            use_return_annotation
            and issubclass(return_, (AsyncGenerator, AbstractAsyncContextManager, Awaitable))
        ) or (_agenerator or _acontext or inspect.iscoroutinefunction(truecall))

    parameters = [_transform_parameter(parameter) for parameter in signature.parameters.values()]

    info = CallableInfo(
        call=call,
        use_cache=caching,
        async_=async_,
        context=context,
        generator=generator,
        parameters=parameters,
        return_annotation=signature.return_annotation,
        configuration=get_configuration(call) if is_configured(call) else None,
    )

    try:
        setattr(call, "__fundi_info__", info)
    except (AttributeError, TypeError):
        pass

    return info
