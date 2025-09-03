from fastapi import Request
from starlette.websockets import WebSocket
from starlette.requests import HTTPConnection
from fastapi.security.oauth2 import SecurityScopes

from fundi import scan
from fundi.compat.fastapi import constants, secured
from fundi.compat.fastapi.alias import init_aliases
from fundi.compat.fastapi.dependant import get_scope_dependant
from fundi.compat.fastapi.metadata import get_metadata, build_metadata


def test_security_scopes():
    def dependency(sec: SecurityScopes): ...

    def homepage(_=secured(dependency, ["scope"])): ...

    info = scan(homepage)
    build_metadata(info)

    metadata = get_metadata(info.named_parameters["_"].from_)

    assert metadata[constants.METADATA_SECURITY_SCOPES].scopes == ["scope"]
    assert "sec" in metadata[constants.METADATA_SCOPE_EXTRA]


def test_dependant():
    def homepage(): ...

    info = scan(homepage)
    build_metadata(info)
    get_scope_dependant(info, set(), "/")

    metadata = get_metadata(info)

    assert metadata[constants.METADATA_DEPENDANT]


def test_aliases():
    def homepage(req: Request, ws: WebSocket, conn: HTTPConnection): ...

    info = scan(homepage)
    init_aliases(info)

    metadata = get_metadata(info)

    assert metadata[constants.METADATA_ALIASES] == {
        Request: {"req"},
        WebSocket: {"ws"},
        HTTPConnection: {"conn"},
    }
