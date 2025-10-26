import typing as _typing

from .scan import scan
from .from_ import from_
from . import exceptions
from .resolve import resolve
from .hooks import with_hooks
from .debug import tree, order
from .inject import inject, ainject
from .side_effects import with_side_effects
from .configurable import configurable_dependency, MutableConfigurationWarning
from .virtual_context import virtual_context, VirtualContextProvider, AsyncVirtualContextProvider
from .types import CallableInfo, TypeResolver, InjectionTrace, R, Parameter, DependencyConfiguration

from .util import (
    is_configured,
    combine_hooks,
    injection_trace,
    get_configuration,
    normalize_annotation,
)


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
    "Parameter",
    "with_hooks",
    "exceptions",
    "CallableInfo",
    "TypeResolver",
    "combine_hooks",
    "is_configured",
    "InjectionTrace",
    "virtual_context",
    "injection_trace",
    "with_side_effects",
    "get_configuration",
    "normalize_annotation",
    "VirtualContextProvider",
    "DependencyConfiguration",
    "configurable_dependency",
    "AsyncVirtualContextProvider",
    "MutableConfigurationWarning",
]
