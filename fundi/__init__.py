import typing as _typing

from .scan import scan
from .from_ import from_
from . import exceptions
from .resolve import resolve
from .hooks import with_hooks
from .debug import tree, order
from .inject import inject, ainject
from .configurable import configurable_dependency, MutableConfigurationWarning
from .virtual_context import virtual_context, VirtualContextProvider, AsyncVirtualContextProvider
from .util import injection_trace, is_configured, get_configuration, normalize_annotation, mutation
from .types import CallableInfo, TypeResolver, InjectionTrace, R, Parameter, DependencyConfiguration


FromType: _typing.TypeAlias = _typing.Annotated[R, TypeResolver]
"""Tell resolver to resolve parameter's value by its type, not name"""

__all__ = [
    "scan",
    "tree",
    "order",
    "from_",
    "inject",
    "resolve",
    "ainject",
    "mutation",
    "Parameter",
    "with_hooks",
    "exceptions",
    "CallableInfo",
    "TypeResolver",
    "is_configured",
    "InjectionTrace",
    "virtual_context",
    "injection_trace",
    "get_configuration",
    "normalize_annotation",
    "VirtualContextProvider",
    "DependencyConfiguration",
    "configurable_dependency",
    "AsyncVirtualContextProvider",
    "MutableConfigurationWarning",
]
