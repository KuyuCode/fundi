import typing
from collections.abc import Sequence

from fundi import scan
from fundi.types import CallableInfo

from .constants import METADATA_SECURITY_SCOPES

__all__ = ["secured"]


def secured_scan(
    dependency: typing.Callable[..., typing.Any], scopes: Sequence[str], caching: bool = True
) -> CallableInfo[typing.Any]:
    """
    Scan dependency and setup it's security scopes
    """
    from .metadata import get_metadata

    info = scan(dependency, caching=caching)

    metadata = get_metadata(info)
    metadata.update({METADATA_SECURITY_SCOPES: list(scopes)})

    return info


def secured(
    dependency: typing.Callable[..., typing.Any], scopes: Sequence[str], caching: bool = True
) -> CallableInfo[typing.Any]:
    """
    Use callable dependency for parameter of function

    :param dependency: function dependency
    :param caching: Whether to use cached result of this callable or not
    :return: callable information
    """

    return secured_scan(dependency, scopes, caching)
