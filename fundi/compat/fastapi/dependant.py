import typing

from fastapi import params
from fastapi._compat import ModelField
from fastapi.security.base import SecurityBase
from fastapi.dependencies.models import Dependant, SecurityRequirement

from fundi.util import callable_str
from fundi.types import CallableInfo

from .metadata import build_metadata, get_metadata
from .constants import METADATA_DEPENDANT, METADATA_SECURITY_SCOPES

from fastapi.dependencies.utils import (
    analyze_param,
    add_param_to_fields,
    add_non_field_param_to_dependency,
)

MF = typing.TypeVar("MF", bound=ModelField)


def merge(into: list[MF], from_: list[MF]):
    names = {field.name for field in into}

    for field in from_:
        if field.name not in names:
            into.append(field)


def update_dependant(source: Dependant, target: Dependant):
    merge(target.path_params, source.path_params)
    merge(target.query_params, source.query_params)
    merge(target.header_params, source.header_params)
    merge(target.cookie_params, source.cookie_params)
    merge(target.body_params, source.body_params)

    target.security_requirements.extend(source.security_requirements)
    target.dependencies.extend(source.dependencies)
    if source.security_scopes:
        if target.security_scopes is None:
            target.security_scopes = []

        target.security_scopes[::] = set().union(target.security_scopes, source.security_scopes)


def get_scope_dependant(
    ci: CallableInfo[typing.Any],
    path_param_names: set[str],
    path: str,
) -> Dependant:
    build_metadata(ci)

    dependant = Dependant(path=path)
    dependant_metadata = get_metadata(ci)
    dependant.security_scopes = dependant_metadata[METADATA_SECURITY_SCOPES]

    dependant_metadata.update({METADATA_DEPENDANT: dependant})

    flat_dependant = Dependant(
        path=path, security_scopes=dependant_metadata[METADATA_SECURITY_SCOPES]
    )

    for param in ci.parameters:
        if param.from_ is not None:
            subci = param.from_

            sub = get_scope_dependant(subci, path_param_names, path)
            update_dependant(sub, flat_dependant)

            # This is required to pass security_scopes to dependency.
            # Here parameter name and security scopes itself are set.
            metadata = get_metadata(subci)

            if isinstance(subci.call, SecurityBase):
                flat_dependant.security_requirements.append(
                    SecurityRequirement(subci.call, metadata[METADATA_SECURITY_SCOPES])
                )

            continue

        details = analyze_param(
            param_name=param.name,
            annotation=param.annotation,
            value=param.default,
            is_path_param=param.name in path_param_names,
        )

        if add_non_field_param_to_dependency(
            param_name=param.name, type_annotation=param.annotation, dependant=dependant
        ):
            assert (
                details.field is None
            ), f'Non-field parameter shouldn\'t have field: error caused by analysis of the parameter "{param.name}" in {callable_str(ci.call)}'

            continue

        assert details.field is not None
        if isinstance(details.field.field_info, params.Body):
            dependant.body_params.append(details.field)
        else:
            add_param_to_fields(field=details.field, dependant=dependant)

    update_dependant(dependant, flat_dependant)

    return flat_dependant
