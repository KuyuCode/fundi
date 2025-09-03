import typing

from fastapi import params

from fundi import scan
from fundi.util import callable_str
from fundi.types import CallableInfo

from .secured import secured_scan
from .constants import METADATA_SECURITY_SCOPES


def get_metadata(info: CallableInfo[typing.Any]) -> dict[str, typing.Any]:
    metadata: dict[str, typing.Any] | None = getattr(info, "metadata", None)
    if metadata is None:
        metadata = {}
        setattr(info, "metadata", metadata)

    return metadata


def build_metadata(
    info: CallableInfo[typing.Any], *, security_scopes: list[str] | None = None
) -> None:
    security_scopes = security_scopes or []

    scopes_up = security_scopes
    scopes_down = security_scopes.copy()

    metadata = get_metadata(info)
    metadata.setdefault(METADATA_SECURITY_SCOPES, scopes_up)

    for parameter in info.parameters:
        subinfo = parameter.from_

        if subinfo is None:
            if isinstance(parameter.default, params.Security):
                security = parameter.default
                assert (
                    security.dependency
                ), f"Parameter {parameter.name} in {callable_str(info.call)} doesn't have dependency setup"

                subinfo = secured_scan(security.dependency, security.scopes, security.use_cache)

            elif isinstance(parameter.default, params.Depends):
                depends = parameter.default
                assert (
                    depends.dependency
                ), f"Parameter {parameter.name} in {callable_str(info.call)} doesn't have dependency setup"

                subinfo = scan(depends.dependency, depends.use_cache)

            else:
                continue

            parameter.from_ = subinfo

        param_metadata = get_metadata(subinfo)

        security: params.Security | None = None

        if typing.get_origin(parameter.annotation) is typing.Annotated:
            args = typing.get_args(parameter.annotation)
            presence: tuple[params.Security] | tuple[()] = tuple(
                filter(lambda x: isinstance(x, params.Security), args)
            )
            if presence:
                security = presence[0]

        if security is not None:
            scopes_down[::] = set().union(security.scopes, scopes_down)

        elif METADATA_SECURITY_SCOPES in param_metadata:
            scopes_down[::] = set().union(param_metadata[METADATA_SECURITY_SCOPES], scopes_down)

        build_metadata(subinfo, security_scopes=scopes_down)
        scopes_up[::] = set().union(scopes_up, scopes_down)

    info.key.add(tuple(scopes_down))
