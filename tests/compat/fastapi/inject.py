from contextlib import AsyncExitStack
from starlette.background import BackgroundTasks
from fastapi import Body, Cookie, Form, Header, Path, Query, Request, Response
from starlette.datastructures import FormData

from fundi import scan

from fundi.compat.fastapi.inject import inject
from fundi.compat.fastapi.alias import init_aliases
from fundi.compat.fastapi.metadata import build_metadata
from fundi.compat.fastapi.dependant import get_scope_dependant


async def test_request():
    response = "response"

    def homepage(req: Request):
        assert isinstance(req, Request)
        yield response

    info = scan(homepage)
    build_metadata(info)
    init_aliases(info)
    _flat_dependant = get_scope_dependant(info, {"path"}, "/{path}")

    async with AsyncExitStack() as stack:
        req = Request({"type": "http", "headers": (), "query_string": ""})

        res = Response()
        tasks = BackgroundTasks()

        result = await inject(info, stack, req, None, None, False, tasks, res)

        assert result == response


async def test_query():
    response = "response"

    def homepage(query: int = Query()):
        assert isinstance(query, int)
        yield response

    info = scan(homepage)
    build_metadata(info)
    init_aliases(info)
    _flat_dependant = get_scope_dependant(info, {"path"}, "/{path}")

    async with AsyncExitStack() as stack:
        req = Request({"type": "http", "query_string": "query=101", "headers": ()})

        res = Response()
        tasks = BackgroundTasks()

        result = await inject(info, stack, req, None, None, False, tasks, res)

        assert result == response


async def test_path():
    response = "response"

    def homepage(path: bool = Path()):
        assert isinstance(path, bool)
        yield response

    info = scan(homepage)
    build_metadata(info)
    init_aliases(info)
    _flat_dependant = get_scope_dependant(info, {"path"}, "/{path}")

    async with AsyncExitStack() as stack:
        req = Request(
            {"type": "http", "headers": (), "path_params": {"path": "true"}, "query_string": ""}
        )

        res = Response()
        tasks = BackgroundTasks()

        result = await inject(info, stack, req, None, None, False, tasks, res)

        assert result == response


async def test_cookie():
    response = "response"

    def homepage(cookie: str = Cookie()):
        assert isinstance(cookie, str)
        yield response

    info = scan(homepage)
    build_metadata(info)
    init_aliases(info)
    _flat_dependant = get_scope_dependant(info, {"path"}, "/{path}")

    async with AsyncExitStack() as stack:
        req = Request(
            {
                "type": "http",
                "headers": ((b"cookie", b"cookie=some;"),),
                "query_string": "",
            }
        )

        res = Response()
        tasks = BackgroundTasks()

        result = await inject(info, stack, req, None, None, False, tasks, res)

        assert result == response


async def test_header():
    response = "response"

    def homepage(header: float = Header()):
        assert isinstance(header, float)
        yield response

    info = scan(homepage)
    build_metadata(info)
    init_aliases(info)
    _flat_dependant = get_scope_dependant(info, {"path"}, "/{path}")

    async with AsyncExitStack() as stack:
        req = Request(
            {
                "type": "http",
                "headers": ((b"header", b"0.3"),),
                "query_string": "",
            }
        )

        res = Response()
        tasks = BackgroundTasks()

        result = await inject(info, stack, req, None, None, False, tasks, res)

        assert result == response


async def test_form():
    response = "response"

    def homepage(username: str = Form(), password: str = Form()):
        assert isinstance(username, str)
        assert isinstance(password, str)
        yield response

    info = scan(homepage)
    build_metadata(info)
    init_aliases(info)
    _flat_dependant = get_scope_dependant(info, {"path"}, "/{path}")

    async with AsyncExitStack() as stack:
        req = Request(
            {
                "type": "http",
                "headers": (),
                "query_string": "",
            }
        )

        res = Response()
        tasks = BackgroundTasks()

        result = await inject(
            info,
            stack,
            req,
            FormData(username="Kuyugama", password="Kuyugama the best"),
            None,
            False,
            tasks,
            res,
        )

        assert result == response


async def test_json():
    response = "response"

    def homepage(username: str = Body(), password: str = Body()):
        assert isinstance(username, str)
        assert isinstance(password, str)
        yield response

    info = scan(homepage)
    build_metadata(info)
    init_aliases(info)
    _flat_dependant = get_scope_dependant(info, {"path"}, "/{path}")

    async with AsyncExitStack() as stack:
        req = Request(
            {
                "type": "http",
                "headers": (),
                "query_string": "",
            }
        )

        res = Response()
        tasks = BackgroundTasks()

        result = await inject(
            info,
            stack,
            req,
            dict(username="Kuyugama", password="Kuyugama the best"),
            None,
            False,
            tasks,
            res,
        )


async def test_pydantic_model():
    from pydantic import BaseModel

    class Signin(BaseModel):
        username: str
        password: str

    response = "response"

    def homepage(body: Signin):
        assert isinstance(body.username, str)
        assert isinstance(body.password, str)
        assert isinstance(body, Signin)

        yield response

    info = scan(homepage)
    build_metadata(info)
    init_aliases(info)
    _flat_dependant = get_scope_dependant(info, {"path"}, "/{path}")

    async with AsyncExitStack() as stack:
        req = Request(
            {
                "type": "http",
                "headers": (),
                "query_string": "",
            }
        )

        res = Response()
        tasks = BackgroundTasks()

        result = await inject(
            info,
            stack,
            req,
            dict(username="Kuyugama", password="Kuyugama the best"),
            None,
            False,
            tasks,
            res,
        )

        assert result == response
