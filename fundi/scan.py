import typing
import inspect
from dataclasses import replace
from types import BuiltinFunctionType, FunctionType, MethodType
from contextlib import AbstractAsyncContextManager, AbstractContextManager

from fundi.util import is_configured, get_configuration
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


def scan(call: typing.Callable[..., R], caching: bool = True) -> CallableInfo[R]:
    """
    Get callable information

    :param call: callable to get information from
    :param caching:  whether to use cached result of this callable or not

    :return: callable information
    """

    if hasattr(call, "__fundi_info__"):
        info = typing.cast(CallableInfo[typing.Any], getattr(call, "__fundi_info__"))
        return replace(info, use_cache=caching)

    if not callable(call):
        raise ValueError(
            f"Callable expected, got {type(call)!r}"
        )  # pyright: ignore[reportUnreachable]

    truecall = call.__call__
    if isinstance(call, (FunctionType, BuiltinFunctionType, MethodType, type)):
        truecall = call

    signature = inspect.signature(truecall)

    generator = inspect.isgeneratorfunction(truecall)
    async_generator = inspect.isasyncgenfunction(truecall)

    context = _is_context(call)
    async_context = _is_async_context(call)

    async_ = inspect.iscoroutinefunction(truecall) or async_generator or async_context
    generator = generator or async_generator
    context = context or async_context

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
