import pytest
from fundi import from_, scan
from functools import partial
from starlette.requests import Request
from starlette.responses import Response
from fastapi import Body, Cookie, Form, Header, Query
from fundi.compat.fastapi.dependant import get_scope_dependant


get_dependant = partial(get_scope_dependant, path_param_names=set(), path="/")


def test_query_param():
    def homepage(name: str = Query()): ...

    dependant = get_dependant(scan(homepage))

    assert dependant.query_params[0].name == "name"


def test_header_param():
    def homepage(token: str = Header()): ...

    dependant = get_dependant(scan(homepage))

    assert dependant.header_params[0].name == "token"


def test_path_param():
    def homepage(type: str): ...

    dependant = get_dependant(scan(homepage), path_param_names={"type"}, path="/{type}")

    assert dependant.path_params[0].name == "type"


def test_cookie_param():
    def homepage(token: str = Cookie()): ...

    dependant = get_dependant(scan(homepage))

    assert dependant.cookie_params[0].name == "token"


def test_body_param():
    def homepage(name: str = Form()): ...

    dependant = get_dependant(scan(homepage))

    assert dependant.body_params[0].name == "name"

    def homepage(username: str = Body()): ...

    dependant = get_dependant(scan(homepage))

    assert dependant.body_params[0].name == "username"


def test_multi_param_same_name():
    def dependency(token: str = Header()): ...
    def homepage(token: str = Query(), authtoken=from_(dependency)): ...

    dependant = get_dependant(scan(homepage))

    assert dependant.query_params[0].name == "token"
    assert dependant.header_params[0].name == "token"
